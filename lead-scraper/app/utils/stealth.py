from __future__ import annotations

import asyncio
import random
from typing import TypedDict

from playwright.async_api import Browser, BrowserContext
from playwright_stealth import Stealth


class Viewport(TypedDict):
    width: int
    height: int


USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Safari/605.1.15",
]

VIEWPORTS: list[Viewport] = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
]


async def random_delay(min_s: float, max_s: float) -> None:
    lower = min(min_s, max_s)
    upper = max(min_s, max_s)
    await asyncio.sleep(random.uniform(lower, upper))


async def new_stealth_context(browser: Browser) -> BrowserContext:
    user_agent = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    context = await browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale="en-US",
    )
    await _stealth_for_user_agent(user_agent).apply_stealth_async(context)
    return context


def _stealth_for_user_agent(user_agent: str) -> Stealth:
    if "Chrome/" in user_agent:
        return Stealth(navigator_user_agent_override=user_agent)

    return Stealth(
        navigator_user_agent_data=False,
        sec_ch_ua=False,
    )
