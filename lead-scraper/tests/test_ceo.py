from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.extractors import ceo as ceo_module
from app.extractors.ceo import find_ceo
from app.scrapers.website import CrawledPage


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ceo"


@pytest.fixture(autouse=True)
def no_live_ddg(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search_ddg(query: str) -> list[dict]:
        return []

    monkeypatch.setattr(ceo_module, "search_ddg", fake_search_ddg)


def test_ceo_precision_recall_against_labeled_fixtures() -> None:
    labels = json.loads((FIXTURE_DIR / "labels.json").read_text(encoding="utf-8"))

    report: list[str] = []
    returned_count = 0
    correct_count = 0
    positive_count = 0

    for filename, expected in labels.items():
        page = _fixture_page(filename)
        candidate = find_ceo([page])
        returned = candidate.name if candidate is not None else None

        if returned is not None:
            returned_count += 1
        if expected is not None:
            positive_count += 1
        if expected is not None and returned is not None and _normalize(returned) == _normalize(expected):
            correct_count += 1

        report.append(
            f"{filename}: expected={expected!r} returned={returned!r} "
            f"confidence={candidate.confidence if candidate else None}"
        )

    precision = correct_count / returned_count if returned_count else 1.0
    recall = correct_count / positive_count if positive_count else 1.0

    failure_report = "\n".join(
        [
            f"precision={precision:.2f}",
            f"recall={recall:.2f}",
            *report,
        ]
    )
    assert precision >= 0.6, failure_report
    assert recall >= 0.4, failure_report


def test_ddg_fallback_parses_linkedin_snippet(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search_ddg(query: str) -> list[dict]:
        assert query == "Acme Studio CEO linkedin"
        return [
            {
                "title": "Mariam Iqbal | Founder at Acme Studio | LinkedIn",
                "snippet": "Mariam Iqbal is Founder at Acme Studio.",
                "url": "https://www.linkedin.com/in/mariam-iqbal",
            }
        ]

    monkeypatch.setattr(ceo_module, "search_ddg", fake_search_ddg)
    page = CrawledPage(
        url="https://acme.example/about",
        html="<html><head><title>Acme Studio</title></head><body><p>No leadership page.</p></body></html>",
        status_code=200,
    )

    candidate = find_ceo([page])

    assert candidate is not None
    assert candidate.name == "Mariam Iqbal"
    assert candidate.linkedin == "https://www.linkedin.com/in/mariam-iqbal"
    assert candidate.source_url == "https://acme.example/about"
    assert candidate.confidence <= 0.4


def _fixture_page(filename: str) -> CrawledPage:
    html = (FIXTURE_DIR / filename).read_text(encoding="utf-8")
    section = "about"
    if "team" in filename:
        section = "team"
    elif "leadership" in filename:
        section = "leadership"

    return CrawledPage(
        url=f"https://fixture.test/{section}/{filename.removesuffix('.html')}",
        html=html,
        status_code=200,
    )


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())
