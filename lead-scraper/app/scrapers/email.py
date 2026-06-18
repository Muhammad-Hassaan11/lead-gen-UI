"""Contact extractor for a business website.

Returns a tuple of (emails, phones). The "Email" tab uses both — emails go
into the Emails column, the first phone goes into the Phone column.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import urlsplit

import phonenumbers

from app.config import settings
from app.scrapers.browser import new_page
from app.utils.log import logger
from app.utils.url import ensure_scheme

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_TEXT_RE = re.compile(r"(?:\+?\d[\d\s().\-]{7,}\d)")

BAD_LOCAL = {"noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster"}
JUNK_DOMAINS = (
    "wixpress.com", "sentry.io", "sentry-next.wixpress.com",
    "example.com", "domain.com", "mysite.com", "yourdomain.com",
    "email.com", "test.com", "godaddy.com", "wix.com", "placeholder.com",
)
BAD_TLDS = {
    "png", "jpg", "jpeg", "gif", "webp", "svg", "css", "js",
    "ico", "bmp", "tiff", "woff", "woff2", "ttf", "eot",
    "mp4", "webm", "mov",
}

FOLLOW_KEYWORDS = re.compile(r"contact|about|reach|support|connect|info|team|staff", re.I)
MAX_FOLLOW = 4
LOAD_TIMEOUT_MS = 30_000


# ---- email cleaning --------------------------------------------------------

def clean_email(raw: str) -> str | None:
    if not raw:
        return None
    email = raw.strip().lower().strip(".")
    email = email.split("?")[0]
    if email.count("@") != 1:
        return None
    local, domain = email.split("@")
    if not local or not domain:
        return None
    if local in BAD_LOCAL:
        return None
    tld = domain.rsplit(".", 1)[-1]
    if tld in BAD_TLDS:
        return None
    if any(j in domain for j in JUNK_DOMAINS):
        return None
    if re.fullmatch(r"[0-9a-f]{24,}", local):
        return None
    if re.search(r"@\d+x$", email):
        return None
    if not (6 <= len(email) <= 100):
        return None
    return email


# ---- phone cleaning --------------------------------------------------------

def clean_phone(raw: str, region: str | None = None) -> str | None:
    """Normalise a phone string to international E.164 using libphonenumber."""
    region = region or settings.default_phone_region
    if not raw:
        return None
    raw = raw.strip()
    # libphonenumber wants something resembling a phone; reject pure noise
    digits = re.sub(r"\D", "", raw)
    if not (7 <= len(digits) <= 15):
        return None
    try:
        if raw.startswith("+"):
            num = phonenumbers.parse(raw, None)
        else:
            num = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_possible_number(num):
        return None
    if not phonenumbers.is_valid_number(num):
        return None
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL)


# ---- page-level harvesting -------------------------------------------------

async def _collect_emails(page: Any) -> set[str]:
    found: set[str] = set()
    try:
        hrefs = await page.eval_on_selector_all(
            "a[href^='mailto:']", "els => els.map(e => e.getAttribute('href'))"
        )
        for h in hrefs or []:
            if not h:
                continue
            raw = h.replace("mailto:", "").split(",")[0]
            email = clean_email(raw)
            if email:
                found.add(email)
    except Exception:
        pass
    try:
        body = await page.inner_text("body")
    except Exception:
        body = ""
    for m in EMAIL_RE.findall(body or ""):
        e = clean_email(m)
        if e:
            found.add(e)
    try:
        html = await page.content()
    except Exception:
        html = ""
    for m in EMAIL_RE.findall(html or ""):
        e = clean_email(m)
        if e:
            found.add(e)
    return found


async def _collect_phones(page: Any, region: str | None = None) -> list[str]:
    """Return a deduped list of phones in E.164 international format.

    Source priority: tel: hrefs > visible text > raw HTML.
    """
    seen: set[str] = set()
    ordered: list[str] = []

    def _add(raw: str) -> None:
        phone = clean_phone(raw, region=region)
        if phone and phone not in seen:
            seen.add(phone)
            ordered.append(phone)

    # 1. tel: hrefs — most reliable
    try:
        hrefs = await page.eval_on_selector_all(
            "a[href^='tel:']", "els => els.map(e => e.getAttribute('href'))"
        )
        for h in hrefs or []:
            if h:
                _add(h.replace("tel:", "").strip())
    except Exception:
        pass

    # 2. visible body text
    try:
        body = await page.inner_text("body")
    except Exception:
        body = ""
    for m in PHONE_TEXT_RE.findall(body or ""):
        _add(m)

    # 3. raw HTML (footer / structured data)
    try:
        html = await page.content()
    except Exception:
        html = ""
    for m in PHONE_TEXT_RE.findall(html or ""):
        _add(m)

    return ordered


async def _follow_candidates(page: Any, base_url: str) -> list[str]:
    try:
        hrefs = await page.eval_on_selector_all(
            "a[href]", "els => els.map(e => e.getAttribute('href'))"
        )
    except Exception:
        return []
    from urllib.parse import urljoin
    seen: set[str] = set()
    out: list[str] = []
    for h in hrefs or []:
        if not h:
            continue
        if not FOLLOW_KEYWORDS.search(h):
            continue
        full = urljoin(base_url, h)
        if full in seen or not full.startswith("http"):
            continue
        seen.add(full)
        out.append(full)
        if len(out) >= MAX_FOLLOW:
            break
    return out


# ---- public ----------------------------------------------------------------

async def scrape_contacts(url: str) -> tuple[list[str], list[str]]:
    """Return (emails, phones) for a business website. Never raises."""
    url = ensure_scheme(url)
    phone_region = _phone_region_for_url(url)
    log = logger.bind(url=url, scraper="contacts")
    try:
        ctx, page = await new_page()
    except Exception as e:
        log.error("contacts_browser_launch_failed", error=str(e))
        return [], []

    emails: set[str] = set()
    phones: list[str] = []
    try:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        except Exception as e:
            log.warning("contacts_goto_failed", error=str(e))
            return [], []

        await asyncio.sleep(3.0)
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
        except Exception:
            pass

        emails |= await _collect_emails(page)
        phones = await _collect_phones(page, phone_region)

        if not (emails or phones):
            for c in await _follow_candidates(page, url):
                try:
                    await page.goto(c, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
                    await asyncio.sleep(2.0)
                    emails |= await _collect_emails(page)
                    new_phones = await _collect_phones(page, phone_region)
                    for p in new_phones:
                        if p not in phones:
                            phones.append(p)
                    if emails or phones:
                        break
                except Exception:
                    continue

        log.info("contacts_done", emails=len(emails), phones=len(phones))
        return sorted(emails), phones
    finally:
        try:
            await ctx.close()
        except Exception:
            pass


async def scrape_emails(url: str) -> list[str]:
    """Backwards-compat wrapper used elsewhere — emails only."""
    emails, _ = await scrape_contacts(url)
    return emails


def _phone_region_for_url(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    if host.endswith(".pk"):
        return "PK"
    return settings.default_phone_region
