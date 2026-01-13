"""Language-dependent HTML metadata.

These tests validate the i18n requirements from `docs/plans/2_ui_feedback.md`:
- `<html lang>` and `dir` reflect the active language
- canonical is per-language and self-referential
- `rel=alternate` + `hreflang` links exist for all languages + `x-default`
- `<meta name="description">` is translated for the home page
- OpenGraph `og:url` matches the canonical URL per language
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from tests.helpers import content_attr, lang_dir, normalized_path


def test_language_prefixed_home_pages_render(page: Page, base_url: str) -> None:
    """Each language must be served under its own prefix (`/en/`, `/de/`, `/he/`)."""

    for lang in ("en", "de", "he"):
        page.goto(f"{base_url}/{lang}/")
        assert page.locator("header.site-header").count() == 1


@pytest.mark.parametrize(
    ("path", "slug"),
    [
        ("/", ""),
        ("/contact/", "contact"),
        ("/posts/genai/triton-inference-server/", "posts/genai/triton-inference-server"),
    ],
)
@pytest.mark.parametrize("lang", ["en", "de", "he"])
def test_language_dependent_head_metadata(
    page: Page, base_url: str, path: str, slug: str, lang: str
) -> None:
    """Validate head metadata that should vary or be scoped per language."""

    normalized = normalized_path(path)
    page.goto(f"{base_url}/{lang}{normalized}")

    assert page.locator("html").get_attribute("lang") == lang
    assert page.locator("html").get_attribute("dir") == lang_dir(lang)

    canonical = page.locator("head link[rel='canonical']").get_attribute("href")
    assert canonical is not None and canonical.endswith(f"/{lang}{normalized}")

    og_url = content_attr(page, "head meta[property='og:url']")
    assert og_url is not None and og_url.endswith(f"/{lang}{normalized}")

    for target_lang in ("en", "de", "he"):
        expected = f"/{target_lang}/"
        if slug:
            expected = f"{expected}{slug}/"

        link = page.locator(f"head link[rel='alternate'][hreflang='{target_lang}']")
        assert link.count() == 1
        href = link.get_attribute("href")
        assert href is not None and href.endswith(expected)

    x_default = page.locator("head link[rel='alternate'][hreflang='x-default']").get_attribute(
        "href"
    )
    assert x_default is not None and x_default.endswith(f"/en{normalized}")


@pytest.mark.parametrize(
    ("lang", "expected_description"),
    [
        ("en", "Notes on building products, applied machine learning, and life in Berlin."),
        (
            "de",
            "Notizen über Produktentwicklung, angewandtes Machine Learning und das Leben in Berlin.",
        ),
        ("he", "הערות על בניית מוצרים, למידת מכונה יישומית והחיים בברלין."),
    ],
)
def test_home_page_description_is_translated(
    page: Page, base_url: str, lang: str, expected_description: str
) -> None:
    """The home page should use a translated description fallback per language."""

    page.goto(f"{base_url}/{lang}/")
    assert content_attr(page, "head meta[name='description']") == expected_description


def test_base_meta_tags_present(page: Page, base_url: str) -> None:
    """Verify required non-language-specific baseline head tags exist."""

    page.goto(f"{base_url}/en/")

    assert page.locator("head meta[charset='utf-8']").count() == 1
    assert page.locator("head meta[name='viewport'][content*='width=device-width']").count() == 1
    assert page.locator("head meta[name='robots'][content='index, follow']").count() == 1
    assert content_attr(page, "head meta[name='theme-color']") not in (None, "")

