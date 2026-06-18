"""Facebook page finder. Given a business website, return the first FB profile URL."""
from __future__ import annotations

import asyncio
import re
from urllib.parse import urlsplit

from app.scrapers.browser import new_page
from app.utils.log import logger
from app.utils.url import ensure_scheme

FB_HREF_RE = re.compile(r"facebook\.com", re.I)
FB_FULL_RE = re.compile(r'https?://(?:www\.)?facebook\.com/[^\s\'"<>]+', re.I)

JUNK_PATHS = ("sharer", "dialog", "plugins", "tr?id", "/tr/", "share.php")
LOAD_TIMEOUT_MS = 30_000


def _clean(url: str) -> str | None:
    if not url:
        return None
    url = url.split("#", 1)[0].strip()
    parsed = urlsplit(url)
    path = parsed.path.strip("/").lower()
    if path in {"profile.php", "plugins"}:
        return None
    url = url.split("?", 1)[0].rstrip("/")
    if any(j in url for j in JUNK_PATHS):
        return None
    if url.endswith("facebook.com") or url.endswith("facebook.com/"):
        return None
    return url


async def find_facebook(url: str) -> str | None:
    """Open a website and return the first Facebook profile URL found. Never raises."""
    url = ensure_scheme(url)
    log = logger.bind(url=url, scraper="facebook")
    try:
        ctx, page = await new_page()
    except Exception as e:
        log.error("fb_browser_launch_failed", error=str(e))
        return None

    try:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        except Exception as e:
            log.warning("fb_goto_failed", error=str(e))
            return None

        await asyncio.sleep(3.0)
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
        except Exception:
            pass

        try:
            hrefs = await page.eval_on_selector_all(
                "a[href]", "els => els.map(e => e.getAttribute('href'))"
            )
        except Exception:
            hrefs = []

        for h in hrefs or []:
            if not h or not FB_HREF_RE.search(h):
                continue
            cleaned = _clean(h)
            if cleaned:
                log.info("fb_found", fb=cleaned)
                return cleaned

        try:
            html = await page.content()
        except Exception:
            html = ""
        for m in FB_FULL_RE.findall(html or ""):
            cleaned = _clean(m)
            if cleaned:
                log.info("fb_found", fb=cleaned)
                return cleaned

        log.info("fb_missing")
        return None
    finally:
        try:
            await ctx.close()
        except Exception:
            pass
