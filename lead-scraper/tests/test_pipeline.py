from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cli import _run_lead_pipeline
from app.models import Base, Job, Lead
from app.pipeline import process_lead
from app.scrapers.maps import MapsResult
from app.scrapers.website import CrawledPage
from app.sinks.sheets import SheetsPushError


def test_process_lead_persists_and_pushes_lead(monkeypatch, tmp_path: Path) -> None:
    asyncio.run(_process_lead_persists_and_pushes_lead(monkeypatch, tmp_path))


def test_process_lead_keeps_scraped_status_when_sheets_push_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    asyncio.run(_process_lead_keeps_scraped_status_when_sheets_push_fails(monkeypatch, tmp_path))


def test_run_pipeline_reuses_existing_lead(monkeypatch, tmp_path: Path) -> None:
    asyncio.run(_run_pipeline_reuses_existing_lead(monkeypatch, tmp_path))


async def _process_lead_persists_and_pushes_lead(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def fake_scrape_maps(_maps_url: str) -> MapsResult:
        return MapsResult(
            name="TestCo Labs",
            address="42 Clifton Road, Karachi",
            phone="+923001234567",
            website="https://testco.example",
            rating=4.8,
            review_count=120,
            category="Software company",
        )

    async def fake_crawl_website(_root_url: str) -> list[CrawledPage]:
        return [
            CrawledPage(
                url="https://testco.example/team",
                status_code=200,
                html="""
                <html>
                  <body>
                    <main>
                      <a href="mailto:hello@testco.com">Email us</a>
                      <a href="tel:+923001234567">Call</a>
                      <div class="team-card">
                        <img src="/ayesha.jpg" alt="Ayesha Khan">
                        <h2>Ayesha Khan</h2>
                        <p>Founder and CEO</p>
                        <a href="https://www.linkedin.com/in/ayeshakhan">LinkedIn</a>
                      </div>
                    </main>
                    <footer>
                      <a href="https://facebook.com/testco">Facebook</a>
                      <a href="https://linkedin.com/company/testco">LinkedIn</a>
                      <a href="https://instagram.com/testco">Instagram</a>
                      <a href="https://x.com/testco">X</a>
                    </footer>
                  </body>
                </html>
                """,
            )
        ]

    append_calls: list[str] = []

    def fake_append_lead(lead: Lead) -> None:
        append_calls.append(lead.maps_url)
        assert lead.status == "pushed"

    monkeypatch.setattr("app.pipeline.scrape_maps", fake_scrape_maps)
    monkeypatch.setattr("app.pipeline.crawl_website", fake_crawl_website)
    monkeypatch.setattr("app.pipeline.sheets.append_lead", fake_append_lead)

    async with session_factory() as session:
        job = Job(mode="single", total=1, done=0, failed=0, status="running")
        lead = Lead(
            job=job,
            maps_url="https://www.google.com/maps/place/TestCo",
            status="pending",
            emails=[],
            source_pages=[],
        )
        session.add(job)
        await session.commit()
        await session.refresh(lead)

        await process_lead(lead.id, session)
        await session.refresh(lead)

        assert lead.status == "pushed"
        assert lead.error is None
        assert lead.business_name == "TestCo Labs"
        assert lead.address == "42 Clifton Road, Karachi"
        assert lead.phone == "+923001234567"
        assert lead.website == "https://testco.example"
        assert lead.emails == ["hello@testco.com"]
        assert lead.facebook == "https://facebook.com/testco"
        assert lead.linkedin == "https://linkedin.com/company/testco"
        assert lead.instagram == "https://instagram.com/testco"
        assert lead.twitter == "https://x.com/testco"
        assert lead.ceo_name == "Ayesha Khan"
        assert lead.ceo_linkedin == "https://www.linkedin.com/in/ayeshakhan"
        assert lead.source_pages == ["https://testco.example/team"]
        assert append_calls == ["https://www.google.com/maps/place/TestCo"]

    await engine.dispose()


async def _process_lead_keeps_scraped_status_when_sheets_push_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "app.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def fake_scrape_maps(_maps_url: str) -> MapsResult:
        return MapsResult(
            name="No Site Co",
            address="1 Test Road",
            phone="+923001234567",
            website=None,
            rating=None,
            review_count=None,
            category=None,
        )

    def fake_append_lead(_lead: Lead) -> None:
        raise SheetsPushError("Google Sheets push failed: permission denied")

    monkeypatch.setattr("app.pipeline.scrape_maps", fake_scrape_maps)
    monkeypatch.setattr("app.pipeline.sheets.append_lead", fake_append_lead)

    async with session_factory() as session:
        job = Job(mode="single", total=1, done=0, failed=0, status="running")
        lead = Lead(
            job=job,
            maps_url="https://www.google.com/maps/place/NoSiteCo",
            status="pending",
            emails=[],
            source_pages=[],
        )
        session.add(job)
        await session.commit()
        await session.refresh(lead)

        await process_lead(lead.id, session)
        await session.refresh(lead)

        assert lead.status == "scraped"
        assert lead.error == "Google Sheets push failed: permission denied"
        assert lead.business_name == "No Site Co"

    await engine.dispose()


async def _run_pipeline_reuses_existing_lead(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    process_calls: list[int] = []

    async def fake_init_db() -> None:
        return None

    async def fake_resolve_short_link(url: str) -> str:
        return url

    async def fake_process_lead(lead_id: int, session) -> None:
        process_calls.append(lead_id)
        lead = await session.get(Lead, lead_id)
        assert lead is not None
        lead.business_name = "TestCo Labs"
        lead.status = "pushed"
        lead.error = None
        await session.commit()

    monkeypatch.setattr("app.cli.SessionLocal", session_factory)
    monkeypatch.setattr("app.cli.init_db", fake_init_db)
    monkeypatch.setattr("app.cli.resolve_short_link", fake_resolve_short_link)
    monkeypatch.setattr("app.cli.process_lead", fake_process_lead)

    url = "https://WWW.GOOGLE.com/maps/place/TestCo?utm_source=newsletter"
    first = await _run_lead_pipeline(url)
    second = await _run_lead_pipeline(url)

    async with session_factory() as session:
        job_count = await session.scalar(select(func.count()).select_from(Job))
        lead_count = await session.scalar(select(func.count()).select_from(Lead))

    assert second.id == first.id
    assert process_calls == [first.id]
    assert job_count == 1
    assert lead_count == 1

    await engine.dispose()
