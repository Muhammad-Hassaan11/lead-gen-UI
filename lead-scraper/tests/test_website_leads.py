"""Smoke test for the new Website-URL flow.

Run:
    cd lead-scraper
    .venv\\Scripts\\activate          (Windows)
    source .venv/bin/activate         (mac/Linux)
    pytest tests/test_website_leads.py -v

The test patches the slow Playwright scrapers with fakes so it runs in seconds
without hitting the network.
"""
from __future__ import annotations

import asyncio
import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Make `app` importable when pytest is run from the repo root or lead-scraper/.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app.jobs import store  # noqa: E402


# ---- fake scraper outputs --------------------------------------------------

async def fake_scrape_contacts(url):
    return (["hello@example.com", "sales@example.com"], ["+1 555-123-4567"])


async def fake_find_facebook(url):
    return "https://www.facebook.com/exampleco"


async def fake_fetch_business_name(url):
    return "Example Co."


# ---- helpers ---------------------------------------------------------------

def _wait_for_job(client: TestClient, job_id: str, timeout_s: float = 8.0) -> dict:
    """Poll the job endpoint until it reports done/failed."""
    import time
    start = time.time()
    while time.time() - start < timeout_s:
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200
        body = r.json()
        if body["status"] in ("done", "failed"):
            return body
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} did not finish in {timeout_s}s")


# ---- tests -----------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_scrapers():
    """Replace the real scrapers with instant fakes for every test."""
    with patch("app.pipeline.scrape_contacts", side_effect=fake_scrape_contacts), \
         patch("app.pipeline.find_facebook", side_effect=fake_find_facebook), \
         patch("app.pipeline._fetch_business_name", side_effect=fake_fetch_business_name):
        yield


def test_website_single_returns_enriched_lead():
    client = TestClient(app)
    r = client.post(
        "/api/scrape/website-single",
        json={"website_url": "https://example.com"},
    )
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["status"] == "pending"
    assert payload["total"] == 1

    job = _wait_for_job(client, payload["job_id"])
    assert job["status"] == "done"
    assert job["done"] == 1
    lead = job["leads"][0]
    assert lead["status"] == "done"
    assert lead["business_name"] == "Example Co."
    assert "hello@example.com" in lead["emails"]
    assert lead["phone"] == "+1 555-123-4567"
    assert lead["facebook"] == "https://www.facebook.com/exampleco"
    # source_url stays unchanged so the UI can show it back to the operator
    assert lead["source_url"] == "https://example.com"


def test_website_bulk_processes_each_url():
    client = TestClient(app)
    urls = ["https://example.com", "https://acme.co", "https://hello.world"]
    r = client.post("/api/scrape/website-bulk", json={"website_urls": urls})
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] == 3

    job = _wait_for_job(client, payload["job_id"])
    assert job["status"] == "done"
    assert job["done"] == 3
    seen = {lead["source_url"] for lead in job["leads"]}
    assert seen == set(urls)
    for lead in job["leads"]:
        assert lead["business_name"] == "Example Co."
        assert lead["emails"]


def test_website_csv_requires_known_column():
    client = TestClient(app)
    bad = io.BytesIO(b"name,description\nfoo,bar\n")
    r = client.post(
        "/api/scrape/website-csv",
        files={"file": ("input.csv", bad, "text/csv")},
    )
    assert r.status_code == 400
    assert "website_url" in r.json()["detail"]


def test_website_csv_happy_path():
    client = TestClient(app)
    body = io.BytesIO(b"website_url\nhttps://example.com\nhttps://acme.co\n")
    r = client.post(
        "/api/scrape/website-csv",
        files={"file": ("input.csv", body, "text/csv")},
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] == 2

    job = _wait_for_job(client, payload["job_id"])
    assert job["status"] == "done"
    assert {lead["source_url"] for lead in job["leads"]} == {
        "https://example.com",
        "https://acme.co",
    }


def test_maps_single_route_still_works():
    """Regression: the new code must not break the original Maps flow."""
    # Stub the all-runner so we don't actually hit Maps.
    async def fake_run_all(job):
        for lead in job.leads:
            lead.business_name = "Maps Co."
            lead.status = "done"
        job.done = len(job.leads)
        job.status = "done"

    with patch("app.pipeline.RUNNERS", {
        **__import__("app.pipeline", fromlist=["RUNNERS"]).RUNNERS,
        "all": fake_run_all,
    }):
        client = TestClient(app)
        r = client.post(
            "/api/scrape/single",
            json={"maps_url": "https://www.google.com/maps/place/Example"},
        )
        assert r.status_code == 200
        payload = r.json()
        job = _wait_for_job(client, payload["job_id"])
        assert job["status"] == "done"
        assert job["leads"][0]["business_name"] == "Maps Co."
