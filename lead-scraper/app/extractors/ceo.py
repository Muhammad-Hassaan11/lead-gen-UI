from __future__ import annotations

import asyncio
import re
import threading
from urllib.parse import urlsplit

from pydantic import BaseModel
from selectolax.parser import HTMLParser, Node

from app.scrapers.ddg import search_ddg
from app.scrapers.website import CrawledPage


TITLE_RE = re.compile(
    r"\b(CEO|Chief Executive(?:\s+Officer)?|Founder|Co[-\s]?Founder|President|Owner|Managing Director|MD|Proprietor)\b",
    re.I,
)
NAME_RE = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})")
STOPWORD_NAMES = {
    "Privacy Policy",
    "Contact Us",
    "About Us",
    "Our Team",
    "Read More",
    "Learn More",
    "Get Started",
    "Sign Up",
    "Log In",
}

PRIORITY_PAGE_RE = re.compile(r"/(?:team|leadership|about|our-team|people|staff|management)(?:[/._-]|$)", re.I)
TEAM_PAGE_RE = re.compile(r"/(?:team|leadership|our-team)(?:[/._-]|$)", re.I)
CARD_CLASS_RE = re.compile(r"(card|team|member|profile|person|leader|staff|management|executive)", re.I)
LINKEDIN_IN_RE = re.compile(r"linkedin\.com/in/", re.I)
TITLE_HIGH_VALUE_RE = re.compile(r"\b(?:CEO|Founder)\b", re.I)
DDG_SNIPPET_RE = re.compile(
    rf"(?P<name>{NAME_RE.pattern})\s*\|\s*(?P<title>[^|]{{0,120}}\bat\b[^|]{{0,120}}|[^|]{{0,120}})"
    r"(?:\s*\|\s*LinkedIn)?",
    re.I,
)
BLOCK_CONTEXT_CHAR_LIMIT = 800


class CeoCandidate(BaseModel):
    name: str
    title: str
    linkedin: str | None
    source_url: str
    confidence: float


def find_ceo(pages: list[CrawledPage]) -> CeoCandidate | None:
    if not pages:
        return None

    priority_pages = _priority_pages(pages)
    candidate = _best_confident_onsite_candidate(priority_pages)
    if candidate is not None:
        return candidate

    if len(priority_pages) != len(pages):
        candidate = _best_confident_onsite_candidate(pages)
        if candidate is not None:
            return candidate

    return _ddg_fallback(pages)


def _priority_pages(pages: list[CrawledPage]) -> list[CrawledPage]:
    priority = [page for page in pages if PRIORITY_PAGE_RE.search(urlsplit(page.url).path)]
    return priority or pages


def _best_confident_onsite_candidate(pages: list[CrawledPage]) -> CeoCandidate | None:
    candidates = _onsite_candidates(pages)
    if not candidates:
        return None

    best = max(candidates, key=lambda candidate: candidate.confidence)
    if best.confidence >= 0.5:
        return best
    return None


def _onsite_candidates(pages: list[CrawledPage]) -> list[CeoCandidate]:
    candidates_by_key: dict[tuple[str, str, str], CeoCandidate] = {}

    for page in pages:
        tree = HTMLParser(page.html)
        for node in tree.css("*"):
            text = _clean_text(node.text(separator=" ", strip=True))
            if not text or not TITLE_RE.search(text):
                continue
            if _has_descendant_title(node):
                continue

            for candidate in _node_candidates(node, page):
                key = (candidate.name.lower(), candidate.title.lower(), candidate.source_url)
                current = candidates_by_key.get(key)
                if current is None or candidate.confidence > current.confidence:
                    candidates_by_key[key] = candidate

    return list(candidates_by_key.values())


def _node_candidates(node: Node, page: CrawledPage) -> list[CeoCandidate]:
    block = _nearest_block(node)
    local_text = _context_text(node, block)
    if not local_text:
        return []

    candidates: list[CeoCandidate] = []

    for title_match in TITLE_RE.finditer(local_text):
        title = _clean_text(title_match.group(0))
        name = _nearest_name(local_text, title_match.start(), title_match.end())
        if name is None:
            continue

        confidence = _score_candidate(name, title, block, page.url)
        linkedin = _nearby_linkedin(block)
        candidates.append(
            CeoCandidate(
                name=name,
                title=title,
                linkedin=linkedin,
                source_url=page.url,
                confidence=round(min(confidence, 1.0), 2),
            )
        )

    return candidates


def _context_text(node: Node, block: Node) -> str:
    block_text = _clean_text(block.text(separator=" ", strip=True))
    if block != node and len(block_text) <= BLOCK_CONTEXT_CHAR_LIMIT:
        return block_text
    return _surrounding_text(node)


def _surrounding_text(node: Node) -> str:
    chunks: list[str] = []
    if node.prev is not None:
        chunks.append(_clean_text(node.prev.text(separator=" ", strip=True))[-200:])
    chunks.append(_clean_text(node.text(separator=" ", strip=True)))
    if node.next is not None:
        chunks.append(_clean_text(node.next.text(separator=" ", strip=True))[:200])
    return _clean_text(" ".join(chunk for chunk in chunks if chunk))


def _nearest_name(text: str, title_start: int, title_end: int) -> str | None:
    before = text[max(0, title_start - 200) : title_start]
    after = text[title_end : title_end + 200]

    nearby_names: list[tuple[int, str]] = []
    nearby_names.extend((len(before) - match.end(), match.group(1)) for match in NAME_RE.finditer(before))
    nearby_names.extend((match.start(), match.group(1)) for match in NAME_RE.finditer(after))
    nearby_names.sort(key=lambda item: item[0])

    for _, raw_name in nearby_names:
        name = _clean_text(raw_name)
        if _is_valid_name(name):
            return name

    return None


def _has_descendant_title(node: Node) -> bool:
    return any(
        child != node and TITLE_RE.search(_clean_text(child.text(separator=" ", strip=True)))
        for child in node.css("*")
    )


def _score_candidate(name: str, title: str, block: Node, source_url: str) -> float:
    score = 0.0
    block_text = _clean_text(block.text(separator=" ", strip=True))

    if _same_block(block, block_text, name, title):
        score += 0.4
    if block.css_first("img") is not None:
        score += 0.2
    if _nearby_linkedin(block):
        score += 0.2
    if TITLE_HIGH_VALUE_RE.search(title):
        score += 0.1
    if TEAM_PAGE_RE.search(urlsplit(source_url).path):
        score += 0.1

    return score


def _same_block(block: Node, block_text: str, name: str, title: str) -> bool:
    return (
        (block.tag in {"div", "li"} or _is_card_like(block))
        and name in block_text
        and re.search(rf"\b{re.escape(title)}\b", block_text, re.I) is not None
    )


def _nearest_block(node: Node) -> Node:
    current: Node | None = node
    while current is not None:
        if current.tag in {"div", "li"} or _is_card_like(current):
            return current
        current = current.parent
    return node


def _is_card_like(node: Node) -> bool:
    attrs = " ".join(
        value
        for key, value in node.attributes.items()
        if key in {"class", "id", "itemtype", "role"}
    )
    return bool(CARD_CLASS_RE.search(attrs))


def _nearby_linkedin(block: Node) -> str | None:
    for anchor in block.css("a[href]"):
        href = anchor.attributes.get("href", "").strip()
        if LINKEDIN_IN_RE.search(href):
            return href
    return None


def _is_valid_name(name: str) -> bool:
    return name not in STOPWORD_NAMES and TITLE_RE.search(name) is None


def _ddg_fallback(pages: list[CrawledPage]) -> CeoCandidate | None:
    trigger_page = pages[0]
    company_name = _company_name(trigger_page)
    if not company_name:
        return None

    try:
        results = _run_ddg_search(f"{company_name} CEO linkedin")
    except Exception:
        return None
    candidates = [_ddg_candidate(result, company_name, trigger_page.url) for result in results]
    candidates = [candidate for candidate in candidates if candidate is not None]
    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate.confidence)


def _ddg_candidate(result: dict, company_name: str, source_url: str) -> CeoCandidate | None:
    text = _clean_text(f"{result.get('title', '')} | {result.get('snippet', '')}")
    for match in DDG_SNIPPET_RE.finditer(text):
        name = _clean_text(match.group("name"))
        title = _clean_text(match.group("title"))
        if not _is_valid_name(name) or not TITLE_RE.search(title):
            continue

        url = str(result.get("url", ""))
        confidence = 0.3
        if LINKEDIN_IN_RE.search(url):
            confidence += 0.05
        if _company_tokens(company_name) & _company_tokens(text):
            confidence += 0.05

        return CeoCandidate(
            name=name,
            title=title,
            linkedin=url if LINKEDIN_IN_RE.search(url) else None,
            source_url=source_url,
            confidence=round(min(confidence, 0.4), 2),
        )

    return None


def _run_ddg_search(query: str) -> list[dict]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(search_ddg(query))

    result: list[dict] = []
    error: BaseException | None = None

    def runner() -> None:
        nonlocal result, error
        try:
            result = asyncio.run(search_ddg(query))
        except BaseException as exc:
            error = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if error is not None:
        raise error
    return result


def _company_name(page: CrawledPage) -> str:
    tree = HTMLParser(page.html)
    for selector in (
        'meta[property="og:site_name"]',
        'meta[name="application-name"]',
    ):
        node = tree.css_first(selector)
        if node is not None:
            value = node.attributes.get("content", "")
            if value.strip():
                return _clean_company_name(value)

    for selector in ("title", "h1"):
        node = tree.css_first(selector)
        if node is not None:
            text = _clean_text(node.text(separator=" ", strip=True))
            if text:
                return _clean_company_name(text)

    hostname = urlsplit(page.url).hostname or ""
    hostname = hostname.removeprefix("www.").split(".", 1)[0]
    return _clean_company_name(hostname.replace("-", " ").replace("_", " "))


def _clean_company_name(text: str) -> str:
    text = _clean_text(text)
    for separator in (" | ", " - ", " \u2013 ", " \u2014 "):
        if separator in text:
            text = text.split(separator, 1)[0]
    return text


def _company_tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z]{3,}", text)}


def _clean_text(text: str) -> str:
    return " ".join(text.split())
