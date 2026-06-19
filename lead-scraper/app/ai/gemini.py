"""Gemini-powered lead verifier.

Given a scraped lead, ask Gemini Flash to:
  1. Validate each email (real vs. placeholder/junk, domain matches site).
  2. Decide if the scraped business_name actually represents the website.

Returns a small dict the pipeline writes onto the lead. Never raises in
production — on any failure the lead just gets `ai_note` set and unverified
fields, so the rest of the flow keeps moving.

Free tier: https://aistudio.google.com — set GEMINI_API_KEY in .env.
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.config import settings
from app.utils.log import logger


class VerifierError(Exception):
    """Raised when the AI call fails. Pipeline catches and continues."""


_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _domain_of(url: str | None) -> str:
    if not url:
        return ""
    try:
        host = urlsplit(url if url.startswith("http") else f"https://{url}").hostname or ""
    except Exception:
        return ""
    return host.lower().removeprefix("www.")


def _build_prompt(business_name: str | None, website: str | None, emails: list[str]) -> str:
    site_domain = _domain_of(website)
    return f"""You are a strict B2B lead-quality auditor. Reply with ONLY valid JSON. No markdown, no commentary.

Inputs
------
business_name: {business_name or "(unknown)"}
website:       {website or "(unknown)"}
website_domain: {site_domain or "(unknown)"}
emails:        {json.dumps(emails)}

Tasks
-----
1. For EACH email decide if it looks like a real, useful business contact:
   - INVALID if it's a placeholder (info@example.com, hello@yourdomain.com, test@test.com).
   - INVALID if the domain clearly does not match website_domain (Wix/GoDaddy/Sentry hosting
     leftovers, contact forms from other sites, asset-host emails).
   - INVALID if the local part looks like a hash, file path, or image filename.
   - VALID for role addresses (info@, sales@, contact@, hello@) when the domain matches the site.
   - VALID for personal addresses on the same domain.
   - If website_domain is unknown, be lenient: accept anything that isn't an obvious placeholder.

2. Decide if business_name plausibly represents this website. Use the domain, the brand-ish
   portion of the URL, and your general knowledge. "Plausible" includes abbreviations, parent
   brands, dba names, or close spellings. If business_name is blank, return null.

Output schema (must match exactly)
----------------------------------
{{
  "emails": [
    {{"email": "string", "valid": true|false, "reason": "short string"}}
  ],
  "name_matches": true|false|null,
  "name_reason": "short string"
}}
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    """Pull JSON out of a Gemini response — handles ```json ... ``` fences."""
    text = (text or "").strip()
    if not text:
        raise VerifierError("empty model response")
    fence = _JSON_BLOCK_RE.search(text)
    payload = fence.group(1).strip() if fence else text
    # Strip a stray leading "json" word some models add
    payload = re.sub(r"^json\s*", "", payload, flags=re.IGNORECASE)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        # Try to salvage by finding the first { ... } block
        start = payload.find("{")
        end = payload.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(payload[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise VerifierError(f"could not parse JSON from model: {exc}") from exc


def _normalize(raw: dict[str, Any], emails: list[str]) -> dict[str, Any]:
    """Ensure all expected keys exist and types are sane."""
    out: dict[str, Any] = {
        "emails": [],
        "name_matches": None,
        "name_reason": "",
    }

    raw_emails = raw.get("emails") or []
    keyed: dict[str, dict[str, Any]] = {}
    if isinstance(raw_emails, list):
        for item in raw_emails:
            if not isinstance(item, dict):
                continue
            email = str(item.get("email") or "").strip().lower()
            if not email:
                continue
            keyed[email] = {
                "email": email,
                "valid": bool(item.get("valid")),
                "reason": str(item.get("reason") or "")[:200],
            }

    # Make sure every input email shows up exactly once, in input order.
    for raw_email in emails:
        key = raw_email.strip().lower()
        if key in keyed:
            out["emails"].append(keyed[key])
        else:
            out["emails"].append(
                {"email": raw_email, "valid": False, "reason": "no verdict from AI"}
            )

    nm = raw.get("name_matches")
    if isinstance(nm, bool):
        out["name_matches"] = nm
    elif nm is None:
        out["name_matches"] = None
    out["name_reason"] = str(raw.get("name_reason") or "")[:200]
    return out


async def verify_lead(
    business_name: str | None,
    website: str | None,
    emails: list[str],
) -> dict[str, Any] | None:
    """Ask Gemini to grade the lead. Returns None when AI is disabled / fails.

    Result shape:
        {
          "emails": [{"email": str, "valid": bool, "reason": str}, ...],
          "name_matches": bool | None,
          "name_reason": str,
        }
    """
    api_key = settings.gemini_api_key
    if not api_key:
        return None
    if not emails and not business_name:
        return None

    prompt = _build_prompt(business_name, website, emails)
    url = f"{_API_BASE}/{settings.gemini_model}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",
        },
    }

    log = logger.bind(scraper="ai_verify")
    try:
        async with httpx.AsyncClient(timeout=settings.gemini_timeout_sec) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        log.warning("gemini_http_error", status=exc.response.status_code, body=exc.response.text[:200])
        return None
    except Exception as exc:
        log.warning("gemini_call_failed", error=str(exc))
        return None

    try:
        candidates = data.get("candidates") or []
        if not candidates:
            log.warning("gemini_no_candidates", data_keys=list(data.keys()))
            return None
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        raw = _extract_json(text)
        return _normalize(raw, emails)
    except VerifierError as exc:
        log.warning("gemini_parse_failed", error=str(exc))
        return None
    except Exception as exc:
        log.warning("gemini_unknown_error", error=str(exc))
        return None
