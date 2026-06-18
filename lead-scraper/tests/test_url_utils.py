from __future__ import annotations

import unittest
from types import TracebackType
from unittest.mock import patch

from app.utils.url import normalize_maps_url, resolve_short_link


class FakeResponse:
    url = "https://www.google.com/maps/place/Test+Business"

    def raise_for_status(self) -> None:
        return None


class FakeAsyncClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.kwargs = kwargs

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def get(self, url: str, follow_redirects: bool = False) -> FakeResponse:
        self.url = url
        self.follow_redirects = follow_redirects
        return FakeResponse()


class UrlUtilsTest(unittest.IsolatedAsyncioTestCase):
    def test_normalize_long_url_lowercases_host(self) -> None:
        url = "https://WWW.Google.COM/maps/place/Test+Business"
        self.assertEqual(normalize_maps_url(url), "https://www.google.com/maps/place/Test+Business")

    async def test_resolve_short_link_follows_redirects(self) -> None:
        with patch("app.utils.url.httpx.AsyncClient", FakeAsyncClient):
            resolved = await resolve_short_link("https://maps.app.goo.gl/abc123")

        self.assertEqual(resolved, "https://www.google.com/maps/place/Test+Business")

    def test_normalize_strips_utm_params(self) -> None:
        url = "https://www.google.com/maps/place/Test?cid=123&utm_source=newsletter&utm_medium=email"
        self.assertEqual(normalize_maps_url(url), "https://www.google.com/maps/place/Test?cid=123")

    def test_normalize_strips_fragment(self) -> None:
        url = "https://www.google.com/maps/place/Test?cid=123#reviews"
        self.assertEqual(normalize_maps_url(url), "https://www.google.com/maps/place/Test?cid=123")

    async def test_resolve_short_link_rejects_malformed_input(self) -> None:
        with self.assertRaises(ValueError):
            await resolve_short_link("not-a-url")


if __name__ == "__main__":
    unittest.main()
