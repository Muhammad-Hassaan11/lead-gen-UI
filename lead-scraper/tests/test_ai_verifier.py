"""Tests for the Gemini AI verifier.

Run:
    pytest tests/test_ai_verifier.py -v

These tests mock the HTTP call to Gemini so they run offline and don't burn
your free quota. They verify:
  - The prompt embeds the right fields
  - JSON output is parsed (with and without ```json fences)
  - Missing API key short-circuits cleanly
  - Pipeline writes verdicts onto the lead
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai import gemini as gemini_module  # noqa: E402
from app.ai.gemini import verify_lead  # noqa: E402
from app.config import settings  # noqa: E402


# ---- helpers ---------------------------------------------------------------

def _fake_gemini_response(payload: dict, *, fenced: bool = False) -> dict:
    text = json.dumps(payload)
    if fenced:
        text = f"```json\n{text}\n```"
    return {
        "candidates": [
            {"content": {"parts": [{"text": text}]}}
        ]
    }


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError(
                "boom", request=None, response=self  # type: ignore[arg-type]
            )


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.last_url = None
        self.last_body = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None):
        self.last_url = url
        self.last_body = json
        return self._response


# ---- tests -----------------------------------------------------------------

def test_no_api_key_short_circuits(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    result = asyncio.run(verify_lead("Acme", "https://acme.co", ["hi@acme.co"]))
    assert result is None


def test_happy_path(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    payload = {
        "emails": [
            {"email": "hi@acme.co", "valid": True, "reason": "domain matches"},
            {"email": "info@example.com", "valid": False, "reason": "placeholder"},
        ],
        "name_matches": True,
        "name_reason": "Acme runs acme.co",
    }
    fake = _FakeClient(_FakeResponse(200, _fake_gemini_response(payload)))

    with patch.object(gemini_module.httpx, "AsyncClient", return_value=fake):
        result = asyncio.run(verify_lead("Acme", "https://acme.co", ["hi@acme.co", "info@example.com"]))

    assert result is not None
    assert result["name_matches"] is True
    assert result["name_reason"].startswith("Acme")
    assert [v["email"] for v in result["emails"]] == ["hi@acme.co", "info@example.com"]
    assert result["emails"][0]["valid"] is True
    assert result["emails"][1]["valid"] is False
    # The prompt should mention the website domain
    assert "acme.co" in fake.last_body["contents"][0]["parts"][0]["text"]


def test_fenced_json_is_unwrapped(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    payload = {
        "emails": [{"email": "ok@acme.co", "valid": True, "reason": "good"}],
        "name_matches": True,
        "name_reason": "yes",
    }
    fake = _FakeClient(_FakeResponse(200, _fake_gemini_response(payload, fenced=True)))
    with patch.object(gemini_module.httpx, "AsyncClient", return_value=fake):
        result = asyncio.run(verify_lead("Acme", "https://acme.co", ["ok@acme.co"]))
    assert result is not None
    assert result["emails"][0]["valid"] is True


def test_missing_email_in_response_gets_filler(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    payload = {
        # AI forgot about the second email
        "emails": [{"email": "ok@acme.co", "valid": True, "reason": "good"}],
        "name_matches": False,
        "name_reason": "different brand",
    }
    fake = _FakeClient(_FakeResponse(200, _fake_gemini_response(payload)))
    with patch.object(gemini_module.httpx, "AsyncClient", return_value=fake):
        result = asyncio.run(verify_lead("Acme", "https://acme.co", ["ok@acme.co", "missing@acme.co"]))
    assert len(result["emails"]) == 2
    assert result["emails"][1]["valid"] is False
    assert result["emails"][1]["reason"] == "no verdict from AI"


def test_http_error_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    fake = _FakeClient(_FakeResponse(429, {"error": "rate limited"}))
    with patch.object(gemini_module.httpx, "AsyncClient", return_value=fake):
        result = asyncio.run(verify_lead("Acme", "https://acme.co", ["x@acme.co"]))
    assert result is None


def test_garbage_response_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    bad = {"candidates": [{"content": {"parts": [{"text": "totally not json"}]}}]}
    fake = _FakeClient(_FakeResponse(200, bad))
    with patch.object(gemini_module.httpx, "AsyncClient", return_value=fake):
        result = asyncio.run(verify_lead("Acme", "https://acme.co", ["x@acme.co"]))
    assert result is None


# ---- pipeline integration -------------------------------------------------

def test_pipeline_writes_verdicts_onto_lead(monkeypatch):
    """`_ai_check` should populate email_verdicts + name_matches + ai_checked."""
    from app import pipeline
    from app.jobs import Lead as MemoryLead

    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")

    async def fake_verify(business_name, website, emails):
        return {
            "emails": [
                {"email": "hi@acme.co", "valid": True, "reason": "matches domain"},
            ],
            "name_matches": True,
            "name_reason": "looks right",
        }

    lead = MemoryLead(
        source_url="https://acme.co",
        business_name="Acme",
        website="https://acme.co",
        emails=["hi@acme.co"],
    )

    with patch.object(pipeline, "ai_verify_lead", side_effect=fake_verify):
        asyncio.run(pipeline._ai_check(lead))

    assert lead.ai_checked is True
    assert lead.name_matches is True
    assert lead.ai_note == "looks right"
    assert len(lead.email_verdicts) == 1
    assert lead.email_verdicts[0].email == "hi@acme.co"
    assert lead.email_verdicts[0].valid is True


def test_pipeline_skips_when_no_api_key(monkeypatch):
    from app import pipeline
    from app.jobs import Lead as MemoryLead

    monkeypatch.setattr(settings, "gemini_api_key", None)

    lead = MemoryLead(source_url="https://acme.co", emails=["hi@acme.co"])
    asyncio.run(pipeline._ai_check(lead))

    assert lead.ai_checked is False
    assert lead.email_verdicts == []
    assert lead.name_matches is None
