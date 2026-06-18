from __future__ import annotations

import re
from urllib.parse import unquote

import phonenumbers
from phonenumbers import PhoneNumberFormat
from selectolax.parser import HTMLParser


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
OBFUS_RE = re.compile(
    r"([a-zA-Z0-9._%+-]+)\s*[\[\(]?\s*(?:at|@)\s*[\]\)]?\s*"
    r"([a-zA-Z0-9.-]+)\s*[\[\(]?\s*(?:dot|\.)\s*[\]\)]?\s*([a-zA-Z]{2,})",
    re.I,
)

JUNK_DOMAINS = {
    "wixpress.com",
    "sentry.io",
    "example.com",
    "domain.com",
    "mysite.com",
    "placeholder.com",
    "email.com",
    "test.com",
}
JUNK_LOCAL = {"noreply", "no-reply", "donotreply", "mailer-daemon"}
IMAGE_EXTENSIONS = {"avif", "bmp", "gif", "ico", "jpeg", "jpg", "png", "svg", "webp"}
OBFUS_TOKEN_RE = re.compile(r"\b(?:at|dot)\b", re.I)


def extract_emails(html: str, source_url: str) -> list[str]:
    candidates: list[str] = []
    candidates.extend(match.group(0) for match in EMAIL_RE.finditer(html))
    candidates.extend(_deobfuscated_emails(html))
    candidates.extend(_mailto_emails(html))

    emails: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        email = candidate.strip().strip(".,;:()[]{}<>").lower()
        if not email or email in seen or not _is_valid_email(email):
            continue
        seen.add(email)
        emails.append(email)

    return emails


def extract_phones(html: str, default_region: str = "PK") -> list[str]:
    candidates: list[phonenumbers.PhoneNumber] = []
    text = _visible_text(html)
    candidates.extend(match.number for match in phonenumbers.PhoneNumberMatcher(text, default_region))
    candidates.extend(_tel_numbers(html, default_region))

    phones: list[str] = []
    seen: set[str] = set()
    for number in candidates:
        if not phonenumbers.is_valid_number(number):
            continue
        formatted = phonenumbers.format_number(number, PhoneNumberFormat.E164)
        if formatted in seen:
            continue
        seen.add(formatted)
        phones.append(formatted)

    return phones


def _deobfuscated_emails(html: str) -> list[str]:
    emails: list[str] = []
    for match in OBFUS_RE.finditer(html):
        if not OBFUS_TOKEN_RE.search(match.group(0)):
            continue
        local, domain, tld = match.groups()
        emails.append(f"{local}@{domain}.{tld}")
    return emails


def _mailto_emails(html: str) -> list[str]:
    tree = HTMLParser(html)
    emails: list[str] = []

    for anchor in tree.css("a[href]"):
        href = anchor.attributes.get("href", "")
        if not href.lower().startswith("mailto:"):
            continue

        recipient = unquote(href[7:].split("?", 1)[0])
        emails.extend(match.group(0) for match in EMAIL_RE.finditer(recipient))

    return emails


def _is_valid_email(email: str) -> bool:
    if "@" not in email:
        return False

    local, domain = email.rsplit("@", 1)
    domain_parts = domain.split(".")
    tld = domain_parts[-1].lower() if domain_parts else ""

    if not local or not domain or "." not in domain:
        return False
    if domain in JUNK_DOMAINS:
        return False
    if local in JUNK_LOCAL:
        return False
    if tld in IMAGE_EXTENSIONS:
        return False
    if _local_part_looks_like_asset(local):
        return False
    if "sentry" in local or "sentry" in domain:
        return False

    return True


def _local_part_looks_like_asset(local: str) -> bool:
    parts = local.rsplit(".", 1)
    return len(parts) == 2 and parts[1].lower() in IMAGE_EXTENSIONS


def _visible_text(html: str) -> str:
    tree = HTMLParser(html)
    for node in tree.css("script, style, noscript, svg"):
        node.decompose()

    body = tree.body
    node = body if body is not None else tree.root
    return node.text(separator=" ", strip=True) if node is not None else html


def _tel_numbers(html: str, default_region: str) -> list[phonenumbers.PhoneNumber]:
    tree = HTMLParser(html)
    numbers: list[phonenumbers.PhoneNumber] = []

    for anchor in tree.css("a[href]"):
        href = anchor.attributes.get("href", "")
        if not href.lower().startswith("tel:"):
            continue

        raw_number = unquote(href[4:].split("?", 1)[0].split(";", 1)[0]).strip()
        if not raw_number:
            continue

        try:
            numbers.append(phonenumbers.parse(raw_number, default_region))
        except phonenumbers.NumberParseException:
            continue

    return numbers
