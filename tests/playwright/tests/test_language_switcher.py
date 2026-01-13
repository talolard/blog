"""Language switcher behavior.

The header language switcher must:
- display the current language as a button
- link to the translated version of the *current page* (not always home)
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from tests.helpers import normalized_path


def test_language_selector_is_button_with_lang_codes(page: Page, base_url: str) -> None:
    """Render a button and show available languages as two-letter codes."""

    page.goto(f"{base_url}/en/")
    assert page.locator(".lang-switcher__button").inner_text().strip() == "EN"

    page.locator(".lang-switcher__button").click()
    assert page.locator(".lang-switcher__menu a[lang='en']").text_content().strip() == "EN"
    assert page.locator(".lang-switcher__menu a[lang='de']").text_content().strip() == "DE"
    assert page.locator(".lang-switcher__menu a[lang='he']").text_content().strip() == "HE"


@pytest.mark.parametrize(
    ("path", "slug"),
    [
        ("/", ""),
        ("/contact/", "contact"),
        ("/posts/genai/triton-inference-server/", "posts/genai/triton-inference-server"),
    ],
)
@pytest.mark.parametrize("current_lang", ["en", "de", "he"])
def test_language_switcher_links_to_translated_current_page(
    page: Page, base_url: str, path: str, slug: str, current_lang: str
) -> None:
    """Always link to the equivalent translated page for each language."""

    page.goto(f"{base_url}/{current_lang}{normalized_path(path)}")
    page.locator(".lang-switcher__button").click()

    for target_lang in ("en", "de", "he"):
        expected = f"/{target_lang}/"
        if slug:
            expected = f"{expected}{slug}/"
        assert (
            page.locator(f".lang-switcher__menu a[lang='{target_lang}']").get_attribute("href")
            == expected
        )

