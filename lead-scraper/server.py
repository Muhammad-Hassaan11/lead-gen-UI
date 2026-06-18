"""Server entry point that actually works on Windows + Playwright.

Two Windows traps we have to dodge:

1. The default asyncio policy on Windows is SelectorEventLoopPolicy, which
   cannot spawn subprocesses. Playwright needs to spawn Chromium.
   -> we install WindowsProactorEventLoopPolicy first.

2. uvicorn's own asyncio loop setup forcibly re-installs
   WindowsSelectorEventLoopPolicy on Windows. With --reload, a fresh child
   process is spawned and our policy is wiped anyway.
   -> we set loop="none" so uvicorn does NOT touch the policy.
   -> we disable reload (it spawned the child that broke everything).

Restart manually after code changes — it's a small price for a working
scraper.
"""
from __future__ import annotations

import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn  # noqa: E402 — must come AFTER the policy override


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        reload=False,       # reload child resets the loop policy — disable it
        loop="none",        # do NOT let uvicorn install any loop policy
        log_config=None,    # use structlog from app.utils.log
        access_log=True,
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
