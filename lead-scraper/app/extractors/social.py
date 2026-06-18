from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser, Node


SOCIAL_KEYS = ("facebook", "linkedin", "instagram", "twitter")
SOCIAL_PATTERNS = {
    "facebook": re.compile(r"^https?://(www\.)?facebook\.com/[^/?#]+", re.I),
    "linkedin": re.compile(r"^https?://(www\.)?linkedin\.com/(company|in)/[^/?#]+", re.I),
    "instagram": re.compile(r"^https?://(www\.)?instagram\.com/[^/?#]+", re.I),
    "twitter": re.compile(r"^https?://(www\.)?(twitter|x)\.com/[^/?#]+", re.I),
}
FACEBOOK_JUNK_RE = re.compile(r"(facebook\.com/(?:sharer|dialog|plugins|tr\b)|tr\?id=)", re.I)
LINKEDIN_JUNK_RE = re.compile(r"(shareArticle|sharing/share-offsite)", re.I)
INSTAGRAM_JUNK_RE = re.compile(r"(instagram\.com/(?:p|reel|explore)(?:/|$))", re.I)
TWITTER_JUNK_RE = re.compile(r"((?:twitter|x)\.com/(?:intent|share)(?:/|\?)|/(?:status)(?:/|$))", re.I)
JUNK_FILTERS = {
    "facebook": FACEBOOK_JUNK_RE,
    "linkedin": LINKEDIN_JUNK_RE,
    "instagram": INSTAGRAM_JUNK_RE,
    "twitter": TWITTER_JUNK_RE,
}


def extract_socials(html: str, base_url: str) -> dict[str, str | None]:
    tree = HTMLParser(html)
    preferred_links = _preferred_region_links(tree, base_url)
    all_links = _anchor_links(tree.css("a[href]"), base_url)

    socials: dict[str, str | None] = {key: None for key in SOCIAL_KEYS}
    for platform in SOCIAL_KEYS:
        socials[platform] = _first_platform_url(platform, [*preferred_links, *all_links])

    return socials


def _preferred_region_links(tree: HTMLParser, base_url: str) -> list[str]:
    footers = tree.css("footer")
    if footers:
        return _anchor_links(footers[-1].css("a[href]"), base_url)

    body = tree.body
    anchors = body.css("a[href]") if body is not None else tree.css("a[href]")
    if not anchors:
        return []

    start = max(0, int(len(anchors) * 0.8))
    return _anchor_links(anchors[start:], base_url)


def _anchor_links(anchors: list[Node], base_url: str) -> list[str]:
    urls: list[str] = []
    for anchor in anchors:
        href = anchor.attributes.get("href", "").strip()
        if not href:
            continue

        url = urljoin(base_url, href)
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        urls.append(urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.query, "")))

    return urls


def _first_platform_url(platform: str, urls: list[str]) -> str | None:
    pattern = SOCIAL_PATTERNS[platform]
    junk_filter = JUNK_FILTERS[platform]
    seen: set[str] = set()

    for url in urls:
        if url in seen:
            continue
        seen.add(url)

        if not pattern.search(url):
            continue
        if junk_filter.search(url):
            continue

        return _clean_profile_url(platform, url)

    return None


def _clean_profile_url(platform: str, url: str) -> str:
    parsed = urlsplit(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if platform == "linkedin" and len(path_parts) >= 2:
        path = f"/{path_parts[0]}/{path_parts[1]}"
    elif path_parts:
        path = f"/{path_parts[0]}"
    else:
        path = parsed.path.rstrip("/")

    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))
