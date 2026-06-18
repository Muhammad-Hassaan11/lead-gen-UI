from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MapsSelectors:
    name: tuple[str, ...] = (
        "h1.DUwDvf",  # Last verified: 2026-06-14
        'h1[class*="fontHeadlineLarge"]',  # Last verified: 2026-06-14
    )
    address: tuple[str, ...] = (
        'button[data-item-id="address"] div.fontBodyMedium',  # Last verified: 2026-06-14
    )
    phone: tuple[str, ...] = (
        'button[data-item-id^="phone:tel:"] div.fontBodyMedium',  # Last verified: 2026-06-14
    )
    website: tuple[str, ...] = (
        'a[data-item-id="authority"]',  # Last verified: 2026-06-14
    )
    rating: tuple[str, ...] = (
        'div.F7nice span[aria-hidden="true"]',  # Last verified: 2026-06-14
    )
    review_count: tuple[str, ...] = (
        'div.F7nice span[aria-label*="reviews"]',  # Last verified: 2026-06-14
    )
    category: tuple[str, ...] = (
        'button[jsaction*="category"]',  # Last verified: 2026-06-14
    )


MAPS_SELECTORS = MapsSelectors()
