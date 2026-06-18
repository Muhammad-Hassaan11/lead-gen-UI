"""Pipeline orchestrator. Drives Jobs to completion."""
from __future__ import annotations

import asyncio
import random
import time
import traceback

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.extractors.ceo import find_ceo
from app.extractors.contact import extract_emails, extract_phones
from app.extractors.social import extract_socials
from app.jobs import Job as MemoryJob
from app.jobs import Lead as MemoryLead
from app.models import Lead as DbLead
from app.scrapers import find_facebook, find_website, scrape_maps
from app.scrapers.email import scrape_contacts
from app.scrapers.website import crawl_website
from app.sinks import sheets
from app.utils.log import logger


def _bump_done(job: MemoryJob) -> None:
    job.done = sum(1 for l in job.leads if l.status in ("done", "partial"))
    job.failed = sum(1 for l in job.leads if l.status == "failed")
    if job.done + job.failed >= job.total:
        job.status = "done"
        job.finished_at = time.time()


async def _maps_delay(i: int, total: int) -> None:
    if i >= total - 1:
        return
    base = settings.maps_min_delay_sec
    span = max(0.0, settings.maps_max_delay_sec - settings.maps_min_delay_sec)
    await asyncio.sleep(base + random.uniform(0, span))


async def run_maps_job(job: MemoryJob) -> None:
    job.status = "running"
    for i, lead in enumerate(job.leads):
        started = time.time()
        lead.status = "running"
        try:
            result = await scrape_maps(lead.source_url)
            lead.business_name = result.business_name
            lead.address = result.address
            lead.phone = result.phone
            lead.website = result.website
            has_any = any([result.business_name, result.address, result.phone, result.website])
            lead.status = "done" if has_any else "partial"
            if not has_any and getattr(result, "note", None):
                lead.error = result.note
        except Exception as e:
            logger.exception("maps_lead_failed", url=lead.source_url, error=str(e))
            lead.status = "failed"
            lead.error = str(e)[:240]
        finally:
            lead.elapsed_ms = int((time.time() - started) * 1000)
            _bump_done(job)
        await _maps_delay(i, len(job.leads))


async def run_website_job(job: MemoryJob) -> None:
    job.status = "running"
    for i, lead in enumerate(job.leads):
        started = time.time()
        lead.status = "running"
        try:
            site = await find_website(lead.source_url)
            lead.website = site
            lead.status = "done" if site else "partial"
            if not site:
                lead.error = "no website link found on this Maps listing"
        except Exception as e:
            lead.status = "failed"
            lead.error = str(e)[:240]
        finally:
            lead.elapsed_ms = int((time.time() - started) * 1000)
            _bump_done(job)
        await _maps_delay(i, len(job.leads))


async def _site_concurrent(job: MemoryJob, work) -> None:
    sem = asyncio.Semaphore(settings.website_concurrency)

    async def _runner(lead: MemoryLead) -> None:
        started = time.time()
        lead.status = "running"
        try:
            async with sem:
                await work(lead)
        except Exception as e:
            lead.status = "failed"
            lead.error = str(e)[:240]
        finally:
            lead.elapsed_ms = int((time.time() - started) * 1000)
            _bump_done(job)

    job.status = "running"
    await asyncio.gather(*[_runner(l) for l in job.leads], return_exceptions=False)


async def run_email_job(job: MemoryJob) -> None:
    """Email tab also fills lead.phone from the same page."""
    async def work(lead: MemoryLead) -> None:
        emails, phones = await scrape_contacts(lead.source_url)
        lead.emails = emails
        if phones:
            lead.phone = phones[0]
        has_any = bool(emails or phones)
        lead.status = "done" if has_any else "partial"
        if not has_any:
            lead.error = "site loaded but no public emails or phones found"
    await _site_concurrent(job, work)


async def run_facebook_job(job: MemoryJob) -> None:
    async def work(lead: MemoryLead) -> None:
        fb = await find_facebook(lead.source_url)
        lead.facebook = fb
        lead.status = "done" if fb else "partial"
        if not fb:
            lead.error = "no Facebook link found on this site"
    await _site_concurrent(job, work)


async def run_all_job(job: MemoryJob) -> None:
    job.status = "running"
    for i, lead in enumerate(job.leads):
        started = time.time()
        lead.status = "running"
        try:
            maps = await scrape_maps(lead.source_url)
            lead.business_name = maps.business_name
            lead.address = maps.address
            lead.phone = maps.phone
            lead.website = maps.website

            if lead.website:
                contacts_task = asyncio.create_task(scrape_contacts(lead.website))
                fb_task = asyncio.create_task(find_facebook(lead.website))
                (emails, phones), fb = await asyncio.gather(
                    contacts_task, fb_task, return_exceptions=False
                )
                lead.emails = emails
                if not lead.phone and phones:
                    lead.phone = phones[0]
                lead.facebook = fb

            has_any = any([
                lead.business_name, lead.phone, lead.website,
                lead.emails, lead.facebook,
            ])
            if lead.website and lead.emails:
                lead.status = "done"
            elif has_any:
                lead.status = "partial"
                if getattr(maps, "note", None) and not lead.business_name:
                    lead.error = maps.note
            else:
                lead.status = "partial"
                lead.error = getattr(maps, "note", None) or "no fields extracted"
        except Exception as e:
            logger.exception("all_lead_failed", url=lead.source_url, error=str(e))
            lead.status = "failed"
            lead.error = (str(e) or traceback.format_exc())[:240]
        finally:
            lead.elapsed_ms = int((time.time() - started) * 1000)
            _bump_done(job)
        await _maps_delay(i, len(job.leads))


RUNNERS = {
    "maps": run_maps_job,
    "website": run_website_job,
    "email": run_email_job,
    "facebook": run_facebook_job,
    "all": run_all_job,
}


async def dispatch(job: MemoryJob) -> None:
    try:
        await RUNNERS[job.kind](job)
    except Exception as e:
        job.status = "failed"
        job.error = str(e)[:240]
        job.finished_at = time.time()
        logger.exception("job_failed", job_id=job.id, error=str(e))


async def process_lead(lead_id: int, session: AsyncSession) -> None:
    """Run the legacy DB-backed single-lead pipeline.

    The current FastAPI tabs use the in-memory job runners above. The CLI and
    tests still exercise this older path, so keep it small and explicit here.
    """
    lead = await session.get(DbLead, lead_id)
    if lead is None:
        raise ValueError(f"Lead {lead_id} not found")

    try:
        maps = await scrape_maps(lead.maps_url)
        lead.business_name = maps.business_name or maps.name
        lead.address = maps.address
        lead.phone = maps.phone
        lead.website = maps.website

        pages = []
        if lead.website:
            pages = await crawl_website(lead.website)
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
                for platform, url in extract_socials(page.html, page.url).items():
                    if url and socials.get(platform) is None:
                        socials[platform] = url

            lead.emails = emails
            if not lead.phone and phones:
                lead.phone = phones[0]
            lead.facebook = socials["facebook"]
            lead.linkedin = socials["linkedin"]
            lead.instagram = socials["instagram"]
            lead.twitter = socials["twitter"]
            lead.source_pages = [page.url for page in pages]

            ceo = find_ceo(pages)
            if ceo is not None:
                lead.ceo_name = ceo.name
                lead.ceo_linkedin = ceo.linkedin

        lead.status = "scraped"
        lead.error = None
        await session.commit()

        lead.status = "pushed"
        await session.commit()
        try:
            sheets.append_lead(lead)
        except sheets.SheetsPushError as exc:
            lead.status = "scraped"
            lead.error = str(exc)[:500]
            await session.commit()
        else:
            lead.error = None
            await session.commit()
    except Exception as exc:
        lead.status = "failed"
        lead.error = str(exc)[:500]
        await session.commit()
        raise


def _extend_unique(target: list[str], values: list[str]) -> None:
    seen = set(target)
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        target.append(value)
