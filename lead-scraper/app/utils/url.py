"""URL helpers: normalise, validate, classify, resolve short links."""
from __future__ import annotations

import re
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

import httpx


MAPS_HOST_RE = re.compile(r"(?:^|\.)(google\.[a-z.]+|maps\.app\.goo\.gl|goo\.gl)$", re.I)
SHORT_MAPS_HOSTS = {"maps.app.goo.gl"}


def is_maps_url(url: str) -> bool:
    """Return True if the URL looks like a Google Maps place / short link."""
    try:
        parsed = urlsplit(url.strip())
    except Exception:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    if not MAPS_HOST_RE.search(parsed.netloc):
        return False
    if "google" in parsed.netloc.lower() and "/maps" not in parsed.path:
        return False
    return True


def is_website_url(url: str) -> bool:
    """Return True if the URL looks like a generic http(s) website."""
    try:
        parsed = urlsplit(url.strip())
    except Exception:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def ensure_scheme(url: str) -> str:
    """If the URL has no scheme, prepend https://."""
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def domain_of(url: str) -> str | None:
    """Return the bare domain (no www.) or None."""
    try:
        host = urlsplit(url).netloc.lower()
    except Exception:
        return None
    if not host:
        return None
    return host.removeprefix("www.")


def clean_urls(raw: list[str]) -> list[str]:
    """Strip whitespace, drop empties, dedupe preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for r in raw:
        u = (r or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def normalize_maps_url(url: str) -> str:
    """Strip UTM params, lowercase the host. Used as an idempotency key."""
    parsed = _parse_absolute_url(url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    filtered = [(k, v) for k, v in pairs if not k.lower().startswith("utm_")]
    query = urlencode(filtered, doseq=True)
    host = parsed.hostname.lower() if parsed.hostname else ""
    netloc = host
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path, query, ""))


async def resolve_short_link(url: str) -> str:
    """Follow redirects on maps.app.goo.gl / goo.gl/maps short links."""
    parsed = _parse_absolute_url(url)
    clean_url = url.strip()
    if not _is_short_maps_url(parsed):
        return clean_url
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(clean_url, follow_redirects=True)
        r.raise_for_status()
        return str(r.url)


def _parse_absolute_url(url: str) -> SplitResult:
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Expected an absolute http(s) URL, got: {url!r}")
    return parsed


def _is_short_maps_url(parsed: SplitResult) -> bool:
    host = parsed.hostname.lower() if parsed.hostname else ""
    return host in SHORT_MAPS_HOSTS or (host == "goo.gl" and parsed.path.lower().startswith("/maps"))
