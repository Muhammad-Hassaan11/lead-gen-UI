"""Quick Playwright sanity check.

    python diagnose.py
    python diagnose.py https://www.google.com/maps/place/Kboq/...

If this prints a real page title and html length, Playwright is healthy.
"""
from __future__ import annotations

import asyncio
import sys

# Same Windows fix as server.py — must be set BEFORE asyncio.run().
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

TEST_URL = sys.argv[1] if len(sys.argv) > 1 else "https://samrahayatofficial.com/"


async def main() -> int:
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        print("FAIL: Playwright not installed:", e)
        print("Fix:  pip install playwright && playwright install chromium")
        return 2

    print(f"Launching Chromium (headless) -> {TEST_URL}")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except NotImplementedError:
            print("FAIL: Windows asyncio cannot spawn subprocess.")
            print("      This script already sets WindowsProactorEventLoopPolicy.")
            print("      If you still see this, you're on a very old Python — upgrade to 3.11+.")
            return 3
        except Exception as e:
            print("FAIL: chromium launch:", e)
            print("Fix:  playwright install chromium")
            return 3

        ctx = await browser.new_context()
        page = await ctx.new_page()
        try:
            await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(3)
            title = await page.title()
            html = await page.content()
            print("OK   title:", title or "(empty)")
            print(f"OK   html length: {len(html)} bytes")

            mails = [a for a in await page.eval_on_selector_all(
                "a[href^='mailto:']", "els => els.map(e => e.getAttribute('href'))"
            ) if a]
            tels = [a for a in await page.eval_on_selector_all(
                "a[href^='tel:']", "els => els.map(e => e.getAttribute('href'))"
            ) if a]
            print(f"OK   mailto: links: {mails or '(none)'}")
            print(f"OK   tel:    links: {tels or '(none)'}")
        except Exception as e:
            print("FAIL: goto/probe:", e)
            return 4
        finally:
            await browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
