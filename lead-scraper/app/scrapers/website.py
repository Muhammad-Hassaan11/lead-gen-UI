"""Extracts just the website link from a Google Maps place URL."""
from __future__ import annotations

import asyncio
from urllib.parse import urljoin, urlsplit

from pydantic import BaseModel

from app.config import settings
from app.scrapers.browser import new_page
from app.utils.log import logger
from app.utils.url import ensure_scheme

SELECTORS = [
    'a[data-item-id="authority"]',
    'a[aria-label*="website" i]',
    'a[data-tooltip="Open website"]',
]

LOAD_TIMEOUT_MS = 30_000
FOLLOW_KEYWORDS = ("contact", "about", "team", "staff", "leadership", "people", "support")
MAX_FOLLOW = 4


class CrawledPage(BaseModel):
    url: str
    status_code: int | None = None
    html: str


async def _dismiss_consent(page) -> None:
    for sel in [
        'button[aria-label*="Accept all" i]',
        'button[aria-label*="Reject all" i]',
        'button:has-text("Accept all")',
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


async def find_website(maps_url: str) -> str | None:
    """Open a Maps URL and return the linked business website. Never raises."""
    log = logger.bind(url=maps_url, scraper="website")
    try:
        ctx, page = await new_page()
    except Exception as e:
        log.error("website_browser_launch_failed", error=str(e))
        return None

    try:
        try:
            await page.goto(maps_url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        except Exception as e:
            log.warning("website_goto_failed", error=str(e))
            return None

        await _dismiss_consent(page)
        await asyncio.sleep(4.0)

        for sel in SELECTORS:
            try:
                el = await page.query_selector(sel)
                if not el:
                    continue
                href = (await el.get_attribute("href")) or ""
                if (
                    href.startswith("http")
                    and "google.com/maps" not in href
                    and "google.com/url" not in href
                ):
                    log.info("website_found", website=href)
                    return href
            except Exception:
                continue
        log.info("website_missing")
        return None
    finally:
        try:
            await ctx.close()
        except Exception:
            pass


async def crawl_website(root_url: str) -> list[CrawledPage]:
    """Load a website and a few likely contact/team pages.

    This keeps the old SQLite/Sheets pipeline working while the newer tabbed
    API can still use the smaller email/facebook scrapers.
    """
    root_url = ensure_scheme(root_url)
    log = logger.bind(url=root_url, scraper="website_crawl")
    try:
        ctx, page = await new_page()
    except Exception as e:
        log.error("website_crawl_browser_launch_failed", error=str(e))
        return []

    pages: list[CrawledPage] = []
    seen: set[str] = set()

    async def visit(url: str) -> None:
        if url in seen:
            return
        seen.add(url)
        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=settings.website_timeout_sec * 1000,
            )
            await asyncio.sleep(1.5)
            html = await page.content()
            pages.append(
                CrawledPage(
                    url=page.url,
                    status_code=response.status if response is not None else None,
                    html=html,
                )
            )
        except Exception as e:
            log.warning("website_crawl_visit_failed", visit_url=url, error=str(e))

    try:
        await visit(root_url)
        for href in await _follow_candidates_from_page(page, root_url):
            if len(pages) >= MAX_FOLLOW + 1:
                break
            await visit(href)
        log.info("website_crawl_done", pages=len(pages))
        return pages
    finally:
        try:
            await ctx.close()
        except Exception:
            pass


async def _follow_candidates_from_page(page, base_url: str) -> list[str]:
    try:
        hrefs = await page.eval_on_selector_all(
            "a[href]", "els => els.map(e => e.getAttribute('href'))"
        )
    except Exception:
        return []

    base_host = (urlsplit(base_url).hostname or "").removeprefix("www.")
    out: list[str] = []
    seen: set[str] = set()
    for href in hrefs or []:
        if not href:
            continue
        lowered = href.lower()
        if not any(keyword in lowered for keyword in FOLLOW_KEYWORDS):
            continue
        full = urljoin(base_url, href).split("#", 1)[0]
        parsed = urlsplit(full)
        host = (parsed.hostname or "").removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or host != base_host:
            continue
        if full in seen:
            continue
        seen.add(full)
        out.append(full)
        if len(out) >= MAX_FOLLOW:
            break
    return out
