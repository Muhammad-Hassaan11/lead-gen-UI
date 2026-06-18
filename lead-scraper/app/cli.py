from __future__ import annotations

import asyncio
import json

import structlog
import typer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import SessionLocal, init_db
from app.extractors.contact import extract_emails, extract_phones
from app.extractors.ceo import CeoCandidate, find_ceo
from app.extractors.social import extract_socials
from app.models import Job, Lead
from app.pipeline import process_lead
from app.scrapers.maps import MapsScrapeError, scrape_maps
from app.scrapers.website import CrawledPage, crawl_website
from app.schemas import LeadOut
from app.sinks import sheets
from app.utils.url import normalize_maps_url, resolve_short_link


app = typer.Typer(no_args_is_help=True)
log = structlog.get_logger(__name__)


@app.callback()
def main() -> None:
    return None


@app.command()
def maps(url: str) -> None:
    try:
        result = asyncio.run(scrape_maps(url))
    except MapsScrapeError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc

    typer.echo(result.model_dump_json(indent=2))


@app.command()
def site(url: str) -> None:
    result = asyncio.run(_scrape_site(url))
    typer.echo(json.dumps(result, indent=2))


@app.command()
def ceo(url: str) -> None:
    result = asyncio.run(_find_ceo_for_site(url))
    if result is None:
        typer.echo("Not found")
        return

    typer.echo(result.model_dump_json(indent=2))


@app.command("init-db")
def init_db_command() -> None:
    asyncio.run(init_db())
    typer.echo("Initialized database.")


@app.command("run")
def run_pipeline(maps_url: str) -> None:
    lead = asyncio.run(_run_lead_pipeline(maps_url))
    typer.echo(LeadOut.model_validate(lead).model_dump_json(indent=2))


@app.command("flush")
def flush_sheets() -> None:
    result = asyncio.run(_flush_scraped_leads())
    typer.echo(json.dumps(result, indent=2))


async def _scrape_site(url: str) -> dict[str, object]:
    pages = await crawl_website(url)
    emails: list[str] = []
    phones: list[str] = []
    socials: dict[str, str | None] = {
        "facebook": None,
        "linkedin": None,
        "instagram": None,
        "twitter": None,
    }

    for page in pages:
        _extend_unique(emails, extract_emails(page.html, page.url))
        _extend_unique(phones, extract_phones(page.html))

        page_socials = extract_socials(page.html, page.url)
        for platform, profile_url in page_socials.items():
            if profile_url and socials.get(platform) is None:
                socials[platform] = profile_url

    return {
        "root_url": url,
        "pages": [_page_payload(page) for page in pages],
        "contacts": {
            "emails": emails,
            "phones": phones,
            "socials": socials,
        },
    }


async def _find_ceo_for_site(url: str) -> CeoCandidate | None:
    pages = await crawl_website(url)
    return find_ceo(pages)


async def _run_lead_pipeline(maps_url: str) -> Lead:
    await init_db()
    normalized_maps_url = normalize_maps_url(await resolve_short_link(maps_url))

    async with SessionLocal() as session:
        lead = await _get_or_create_single_lead(session, normalized_maps_url)

        if lead.status not in {"scraped", "pushed"}:
            lead.status = "pending"
            lead.error = None
            await _mark_single_job_running(session, lead)
            await session.commit()

            await process_lead(lead.id, session)
            await session.refresh(lead)

        await _finalize_single_job(session, lead)
        await session.refresh(lead)
        return lead


async def _flush_scraped_leads() -> dict[str, int | str]:
    await init_db()

    async with SessionLocal() as session:
        leads = (
            await session.scalars(
                select(Lead).where(Lead.status == "scraped").order_by(Lead.updated_at.asc())
            )
        ).all()

        pushed = 0
        failed = 0
        for lead in leads:
            lead.status = "pushed"
            try:
                sheets.append_lead(lead)
            except sheets.SheetsPushError as exc:
                lead.status = "scraped"
                lead.error = str(exc)[:500]
                failed += 1
                log.warning(
                    "sheets_flush_failed",
                    lead_id=lead.id,
                    maps_url=lead.maps_url,
                    error=str(exc),
                )
            else:
                lead.error = None
                pushed += 1

            await session.commit()

    return {
        "status": "done",
        "found": len(leads),
        "pushed": pushed,
        "failed": failed,
    }


async def _get_or_create_single_lead(session: AsyncSession, maps_url: str) -> Lead:
    existing = await session.scalar(
        select(Lead)
        .where(Lead.maps_url == maps_url)
        .options(selectinload(Lead.job))
    )
    if existing is not None:
        return existing

    job = Job(mode="single", total=1, done=0, failed=0, status="running")
    lead = Lead(job=job, maps_url=maps_url, status="pending", emails=[], source_pages=[])
    session.add(job)
    await session.commit()
    await session.refresh(lead)
    return lead


async def _mark_single_job_running(session: AsyncSession, lead: Lead) -> None:
    job = await session.get(Job, lead.job_id)
    if job is None:
        return

    job.status = "running"
    job.done = 0
    job.failed = 0


async def _finalize_single_job(session: AsyncSession, lead: Lead) -> None:
    job = await session.get(Job, lead.job_id)
    if job is None:
        return

    if lead.status == "failed":
        job.done = 0
        job.failed = 1
        job.status = "failed"
    elif lead.status in {"scraped", "pushed"}:
        job.done = 1
        job.failed = 0
        job.status = "done"
    else:
        job.done = 0
        job.failed = 0
        job.status = "pending"

    await session.commit()


def _extend_unique(target: list[str], values: list[str]) -> None:
    seen = set(target)
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        target.append(value)


def _page_payload(page: CrawledPage) -> dict[str, object]:
    return {
        "url": page.url,
        "status_code": page.status_code,
        "html": page.html,
    }


if __name__ == "__main__":
    app()
