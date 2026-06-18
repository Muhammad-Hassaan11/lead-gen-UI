from __future__ import annotations

import asyncio
import time
from urllib.parse import parse_qs, urljoin, urlsplit

import httpx
from selectolax.parser import HTMLParser, Node


DDG_HTML_URL = "https://html.duckduckgo.com/html/"
MAX_RESULTS = 10
MIN_DELAY_SECONDS = 10.0

_search_semaphore = asyncio.Semaphore(1)
_last_call_at = 0.0


async def search_ddg(query: str) -> list[dict]:
    global _last_call_at

    query = query.strip()
    if not query:
        return []

    async with _search_semaphore:
        elapsed = time.monotonic() - _last_call_at
        if _last_call_at and elapsed < MIN_DELAY_SECONDS:
            await asyncio.sleep(MIN_DELAY_SECONDS - elapsed)

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
                follow_redirects=True,
                headers={
                    "User-Agent": "LeadScraperBot/1.0 (+contact@local)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            ) as client:
                response = await client.get(DDG_HTML_URL, params={"q": query})
                response.raise_for_status()
                return _parse_results(response.text)
        finally:
            _last_call_at = time.monotonic()


def _parse_results(html: str) -> list[dict]:
    tree = HTMLParser(html)
    results: list[dict] = []

    for result in tree.css(".result"):
        title_node = result.css_first(".result__a") or result.css_first("a[href]")
        if title_node is None:
            continue

        snippet_node = (
            result.css_first(".result__snippet")
            or result.css_first(".result__body")
            or result.css_first(".result__extras")
        )
        url_node = result.css_first(".result__url")

        title = _node_text(title_node)
        snippet = _node_text(snippet_node)
        url = _clean_result_url(title_node.attributes.get("href", ""))
        if not url and url_node is not None:
            url = _clean_display_url(_node_text(url_node))

        if not title or not url:
            continue

        results.append({"title": title, "snippet": snippet, "url": url})
        if len(results) >= MAX_RESULTS:
            break

    return results


def _node_text(node: Node | None) -> str:
    if node is None:
        return ""
    return " ".join(node.text(separator=" ", strip=True).split())


def _clean_result_url(href: str) -> str:
    href = href.strip()
    if not href:
        return ""

    url = urljoin("https://duckduckgo.com", href)
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    uddg = query.get("uddg")
    if uddg:
        return uddg[0]

    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url

    return ""


def _clean_display_url(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://")):
        return text
    return f"https://{text}"
