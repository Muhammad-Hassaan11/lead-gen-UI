"""All-in-one prototype orchestrator.

Reads a list of Google Maps URLs from a text file, runs them through
Maps → Website → Email → Facebook, and writes a CSV.

This is the *prototype* runner inside `scrape/`. For the production version
(FastAPI + UI + CLI with progress bars), use `lead-scraper/main.py`.

Usage:
    python scrape/main.py --urls maps_urls.txt --out leads.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# ---------------------------------------------------------------- regexes ---

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
FB_FULL_RE = re.compile(r'https?://(?:www\.)?facebook\.com/[^\s\'"<>]+', re.I)

BAD_LOCAL = {"noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster"}
BAD_TLDS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "css", "js", "ico"}
JUNK_DOMAINS = ("wixpress.com", "sentry", "example.com", "domain.com",
                "mysite.com", "yourdomain.com", "godaddy.com")
JUNK_FB = ("sharer", "dialog", "plugins", "tr?id", "/tr/", "share.php")


def clean_email(raw: str) -> str | None:
    e = raw.strip().lower().strip(".").split("?")[0]
    if e.count("@") != 1:
        return None
    local, domain = e.split("@")
    if not local or not domain:
        return None
    if local in BAD_LOCAL:
        return None
    tld = domain.rsplit(".", 1)[-1]
    if tld in BAD_TLDS or any(j in domain for j in JUNK_DOMAINS):
        return None
    if re.fullmatch(r"[0-9a-f]{24,}", local):
        return None
    if not (6 <= len(e) <= 100):
        return None
    return e


# ---------------------------------------------------------------- scrapers ---

async def scrape_maps(page, url: str) -> dict:
    out = {"business_name": None, "address": None, "phone": None, "website": None}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(4)
        try:
            el = await page.query_selector('h1.DUwDvf, h1[class*="fontHeadlineLarge"], h1')
            if el: out["business_name"] = (await el.inner_text()).strip()
        except Exception: pass
        try:
            el = await page.query_selector('button[data-item-id="address"] div.fontBodyMedium')
            if el: out["address"] = (await el.inner_text()).strip()
        except Exception: pass
        try:
            el = await page.query_selector('button[data-item-id^="phone:tel:"]')
            if el:
                aria = (await el.get_attribute("aria-label")) or ""
                m = re.search(r"[+\d][\d\s().\-+]{5,}", aria)
                if m: out["phone"] = m.group(0).strip()
        except Exception: pass
        try:
            for sel in ['a[data-item-id="authority"]', 'a[aria-label*="website" i]']:
                el = await page.query_selector(sel)
                if el:
                    href = (await el.get_attribute("href")) or ""
                    if href.startswith("http") and "google.com" not in href:
                        out["website"] = href
                        break
        except Exception: pass
    except Exception as e:
        print(f"  ! Maps failed: {e}", file=sys.stderr)
    return out


async def scrape_emails_and_fb(page, url: str) -> tuple[list[str], str | None]:
    emails: set[str] = set()
    fb: str | None = None
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(3)
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
        except Exception: pass

        try:
            mailtos = await page.eval_on_selector_all(
                "a[href^='mailto:']", "els => els.map(e => e.getAttribute('href'))"
            )
            for h in mailtos or []:
                if h:
                    e = clean_email(h.replace("mailto:", "").split(",")[0])
                    if e: emails.add(e)
        except Exception: pass

        try:
            body = await page.inner_text("body")
            for m in EMAIL_RE.findall(body or ""):
                e = clean_email(m)
                if e: emails.add(e)
        except Exception: pass

        try:
            html = await page.content()
        except Exception:
            html = ""
        for m in EMAIL_RE.findall(html or ""):
            e = clean_email(m)
            if e: emails.add(e)

        try:
            hrefs = await page.eval_on_selector_all(
                "a[href]", "els => els.map(e => e.getAttribute('href'))"
            )
            for h in hrefs or []:
                if h and "facebook.com" in h.lower():
                    cleaned = h.split("?")[0].rstrip("/")
                    if not any(j in cleaned for j in JUNK_FB) and not cleaned.endswith("facebook.com"):
                        fb = cleaned
                        break
        except Exception: pass
        if not fb:
            for m in FB_FULL_RE.findall(html or ""):
                cleaned = m.split("?")[0].rstrip("/")
                if not any(j in cleaned for j in JUNK_FB) and not cleaned.endswith("facebook.com"):
                    fb = cleaned
                    break
    except Exception as e:
        print(f"  ! Site failed: {e}", file=sys.stderr)
    return sorted(emails), fb


# ---------------------------------------------------------------- runner ----

async def run(urls: list[str], out_path: Path, delay_sec: float = 6.0) -> None:
    rows = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await ctx.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            data = await scrape_maps(page, url)
            emails, fb = [], None
            if data["website"]:
                emails, fb = await scrape_emails_and_fb(page, data["website"])
            rows.append({
                "Business Name": data["business_name"] or "",
                "Address":       data["address"] or "",
                "Phone":         data["phone"] or "",
                "Website":       data["website"] or "",
                "Emails":        "; ".join(emails),
                "Facebook":      fb or "",
                "Source URL":    url,
            })
            print(f"  -> {data.get('business_name') or '(no name)'} · {len(emails)} emails · fb={'y' if fb else 'n'}")
            if i < len(urls):
                await asyncio.sleep(delay_sec)

        await browser.close()

    # UTF-8 BOM CSV
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else
                                ["Business Name", "Address", "Phone", "Website", "Emails", "Facebook", "Source URL"],
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows -> {out_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="All-in-one Maps → Website → Email + Facebook batch runner")
    ap.add_argument("--urls", type=Path, required=True, help="text file, one Google Maps URL per line")
    ap.add_argument("--out",  type=Path, required=True, help="output CSV path")
    ap.add_argument("--delay", type=float, default=6.0, help="seconds between Maps requests (default 6)")
    args = ap.parse_args()

    if not args.urls.exists():
        print(f"error: input file not found: {args.urls}", file=sys.stderr)
        return 2

    urls = []
    for line in args.urls.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    if not urls:
        print("error: no URLs in input file", file=sys.stderr)
        return 2

    asyncio.run(run(urls, args.out, delay_sec=args.delay))
    return 0


if __name__ == "__main__":
    sys.exit(main())
