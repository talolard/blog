"""Small UX regressions and content sanity checks."""

from __future__ import annotations

from playwright.sync_api import Page


def test_contact_page_exists_with_email_and_twitter_links(page: Page, base_url: str) -> None:
    """Contact page exists in all languages and contains the expected links."""

    for lang in ("en", "de", "he"):
        page.goto(f"{base_url}/{lang}/contact/")
        assert page.locator("main a[href^='mailto:tal@talperry.com']").count() >= 1
        assert page.locator("main a[href='https://twitter.com/thetalperry']").count() >= 1


def test_header_subtitle_removed(page: Page, base_url: str) -> None:
    """The previous tagline/subtitle should not render in the header."""

    page.goto(f"{base_url}/en/")
    assert page.locator(".brand-subtext").count() == 0


def test_header_letters_include_spacer_between_tal_and_perry(page: Page, base_url: str) -> None:
    """The lettermark should visually separate Tal from Perry."""

    page.goto(f"{base_url}/en/")
    assert page.locator(".brand-letter-spacer").count() == 1


def test_lang_shortcode_renders_lang_attribute(page: Page, base_url: str) -> None:
    """Mixed-language content can be annotated with a nested `lang` attribute."""

    page.goto(f"{base_url}/he/contact/")
    assert page.locator("span[lang='en']").filter(has_text="@thetalperry").count() == 1

