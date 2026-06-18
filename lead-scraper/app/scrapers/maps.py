"""Google Maps place scraper.

Extracts name, address, phone, website from a single Maps place URL.

SELECTORS LAST VERIFIED: 2026-06-18
"""
from __future__ import annotations

import asyncio
import random
import re
from typing import Any

from pydantic import BaseModel

from app.scrapers.browser import new_page
from app.utils.log import logger

LAST_VERIFIED = "2026-06-18"

SEL_NAME = 'h1.DUwDvf, h1[class*="fontHeadlineLarge"], h1'
SEL_WEBSITE = (
    'a[data-item-id="authority"], '
    'a[aria-label*="website" i], '
    'a[data-tooltip="Open website"]'
)
SEL_PHONE = (
    'button[data-item-id^="phone:tel:"] div.fontBodyMedium, '
    'button[aria-label*="phone" i] div.fontBodyMedium'
)
SEL_ADDRESS = (
    'button[data-item-id="address"] div.fontBodyMedium, '
    'button[aria-label*="address" i] div.fontBodyMedium'
)

LOAD_TIMEOUT_MS = 35_000
SETTLE_DELAY_SEC = 5.0


class MapsScrapeError(RuntimeError):
    """Raised by older call sites when Maps scraping cannot complete."""


class MapsResult(BaseModel):
    business_name: str | None = None
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    note: str | None = None  # explanation when fields are missing


async def _text(page: Any, selector: str) -> str | None:
    try:
        el = await page.query_selector(selector)
        if el:
            txt = (await el.inner_text()).strip()
            return txt or None
    except Exception:
        pass
    return None


async def _attr(page: Any, selector: str, attr: str) -> str | None:
    try:
        el = await page.query_selector(selector)
        if el:
            val = await el.get_attribute(attr)
            if val:
                val = val.strip()
                return val or None
    except Exception:
        pass
    return None


async def _phone_from_aria(page: Any) -> str | None:
    try:
        el = await page.query_selector('button[data-item-id^="phone:tel:"]')
        if not el:
            return None
        aria = (await el.get_attribute("aria-label")) or ""
        m = re.search(r"[+\d][\d\s().\-+]{5,}", aria)
        if m:
            return m.group(0).strip()
    except Exception:
        pass
    return None


async def _dismiss_consent(page: Any) -> None:
    """Click through Google's EU/US consent dialog if it appears."""
    for sel in [
        'button[aria-label*="Accept all" i]',
        'button[aria-label*="Reject all" i]',
        'button:has-text("Accept all")',
        'button:has-text("I agree")',
        'form[action*="consent"] button',
    ]:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click(timeout=2000)
                await asyncio.sleep(2.0)
                return
        except Exception:
            continue


async def scrape_maps(url: str) -> MapsResult:
    """Open a Maps place URL and return the structured fields.

    Never raises — on failure returns an empty MapsResult with `note` set.
    """
    log = logger.bind(url=url, scraper="maps")
    try:
        ctx, page = await new_page()
    except Exception as e:
        log.error("maps_browser_launch_failed", error=str(e))
        return MapsResult(note=f"browser launch failed: {e}"[:240])

    try:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        except Exception as e:
            log.warning("maps_goto_failed", error=str(e))
            return MapsResult(note=f"page did not load: {e}"[:240])

        await _dismiss_consent(page)
        await asyncio.sleep(SETTLE_DELAY_SEC)

        # Try to wait for the main heading to actually render
        try:
            await page.wait_for_selector(SEL_NAME, timeout=15_000)
        except Exception:
            pass

        name = await _text(page, SEL_NAME)
        address = await _text(page, SEL_ADDRESS)
        phone = await _text(page, SEL_PHONE)
        if not phone:
            phone = await _phone_from_aria(page)
        website = await _attr(page, SEL_WEBSITE, "href")
        if website and "google.com/url" in website:
            website = None

        result = MapsResult(business_name=name, address=address, phone=phone, website=website)
        if not any([name, address, phone, website]):
            result.note = "no fields matched — selectors may be stale or page blocked"
        log.info("maps_done", got=result.model_dump(exclude_none=True))
        return result
    finally:
        try:
            await ctx.close()
        except Exception:
            pass


async def scrape_maps_many(urls: list[str], delay_sec: float = 5.0) -> list[MapsResult]:
    out: list[MapsResult] = []
    for i, url in enumerate(urls):
        out.append(await scrape_maps(url))
        if i < len(urls) - 1:
            await asyncio.sleep(delay_sec + random.uniform(0, delay_sec))
    return out
