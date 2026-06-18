from __future__ import annotations

from pathlib import Path

import pytest

from app.extractors.contact import extract_emails, extract_phones
from app.extractors.social import extract_socials


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sites"

EXPECTED = {
    "static.html": {
        "emails": ["info@staticco.pk"],
        "phones": ["+923001234567"],
        "socials": {
            "facebook": "https://facebook.com/staticco.pk",
            "linkedin": "https://www.linkedin.com/company/staticco",
            "instagram": "https://instagram.com/staticco_pk",
            "twitter": "https://x.com/staticco",
        },
    },
    "wordpress.html": {
        "emails": ["hello@wordpressstudio.pk", "sales@wordpressstudio.pk"],
        "phones": ["+923117654321"],
        "socials": {
            "facebook": "https://www.facebook.com/wordpressstudio",
            "linkedin": "https://www.linkedin.com/company/wordpressstudio",
            "instagram": None,
            "twitter": None,
        },
    },
    "wix.html": {
        "emails": ["contact@wixsample.pk"],
        "phones": ["+923221112233"],
        "socials": {
            "facebook": "https://facebook.com/wixsample",
            "linkedin": None,
            "instagram": "https://instagram.com/wixsample_salon",
            "twitter": None,
        },
    },
    "shopify.html": {
        "emails": ["support@shopbrand.pk", "sales@shopbrand.pk"],
        "phones": ["+923332223344"],
        "socials": {
            "facebook": None,
            "linkedin": None,
            "instagram": "https://instagram.com/shopbrandpk",
            "twitter": "https://twitter.com/shopbrandpk",
        },
    },
    "react-spa.html": {
        "emails": ["team@reactlead.io"],
        "phones": ["+923445566778"],
        "socials": {
            "facebook": None,
            "linkedin": "https://linkedin.com/company/reactlead",
            "instagram": None,
            "twitter": "https://x.com/reactlead",
        },
    },
}


@pytest.mark.parametrize(("fixture_name", "expected"), EXPECTED.items())
def test_extractors_against_site_fixtures(fixture_name: str, expected: dict[str, object]) -> None:
    html = (FIXTURE_DIR / fixture_name).read_text(encoding="utf-8")
    source_url = f"https://{fixture_name.removesuffix('.html')}.test"

    assert extract_emails(html, source_url) == expected["emails"]
    assert extract_phones(html) == expected["phones"]
    assert extract_socials(html, source_url) == expected["socials"]


def test_email_junk_domains_are_rejected() -> None:
    html = """
    <p>help@wixpress.com alerts@sentry.io hello@example.com</p>
    <a href="mailto:real@company.pk">Email</a>
    """

    assert extract_emails(html, "https://company.pk") == ["real@company.pk"]
