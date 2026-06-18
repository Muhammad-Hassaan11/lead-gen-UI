"""CLI orchestrator for Prospector. No FastAPI, no UI — just batch runs.

Usage:
    python main.py all      --urls maps_urls.txt --out leads.csv
    python main.py maps     --urls maps_urls.txt --out leads.csv
    python main.py website  --urls maps_urls.txt --out websites.csv
    python main.py email    --urls websites.txt  --out emails.csv
    python main.py facebook --urls websites.txt  --out facebook.csv

The .txt file is one URL per line. Blank lines and lines starting with '#' are
ignored.

Output is a UTF-8 BOM CSV that opens cleanly in Excel and Google Sheets.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.csv_export import leads_to_csv
from app.jobs import store
from app.pipeline import dispatch
from app.scrapers.browser import manager
from app.utils.log import configure_logging, logger

KINDS = ("maps", "website", "email", "facebook", "all")


def _read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def _bar(done: int, total: int, width: int = 32) -> str:
    if total == 0:
        return ""
    filled = int(width * done / total)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {done}/{total}"


async def _run(kind: str, urls: list[str], out: Path) -> int:
    configure_logging("INFO")
    job = store.create(kind, urls)  # type: ignore[arg-type]
    logger.info("cli_start", kind=kind, total=len(urls), out=str(out))

    # Drive the job, ticking the progress bar every second.
    task = asyncio.create_task(dispatch(job))
    while not task.done():
        sys.stdout.write("\r" + _bar(job.done + job.failed, job.total))
        sys.stdout.flush()
        await asyncio.sleep(1.0)
    sys.stdout.write("\r" + _bar(job.done + job.failed, job.total) + "\n")
    await task

    out.write_bytes(leads_to_csv(job.leads))
    logger.info("cli_done", done=job.done, failed=job.failed, out=str(out))
    return 0 if job.failed == 0 else 1


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Prospector CLI batch runner")
    sub = p.add_subparsers(dest="kind", required=True)
    for k in KINDS:
        sp = sub.add_parser(k, help=f"Run the {k} scraper")
        sp.add_argument("--urls", type=Path, required=True, help="text file, one URL per line")
        sp.add_argument("--out", type=Path, required=True, help="output CSV path")
    return p


def main() -> int:
    args = _parser().parse_args()
    if not args.urls.exists():
        print(f"error: input file not found: {args.urls}", file=sys.stderr)
        return 2
    urls = _read_urls(args.urls)
    if not urls:
        print("error: no URLs found in input file.", file=sys.stderr)
        return 2

    try:
        return asyncio.run(_run(args.kind, urls, args.out))
    finally:
        try:
            asyncio.run(manager.shutdown())
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
