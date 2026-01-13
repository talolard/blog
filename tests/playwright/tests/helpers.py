"""Test helpers for Playwright UI tests.

These helpers keep the actual test functions short and focused on intent:
- normalize Hugo paths consistently (`/en/`, `/de/contact/`, …)
- fetch head metadata content attributes
- compute expected directionality per language
"""

from __future__ import annotations

from playwright.sync_api import Page


def content_attr(page: Page, selector: str) -> str | None:
    """Return the `content` attribute for the first matching element, if any."""

    element = page.locator(selector).first
    if element.count() == 0:
        return None
    return element.get_attribute("content")


def lang_dir(lang: str) -> str:
    """Return the expected `dir` value for a given language code."""

    return "rtl" if lang == "he" else "ltr"


def normalized_path(path: str) -> str:
    """Normalize a path into Hugo-style URL form (leading and trailing slash)."""

    if not path.startswith("/"):
        path = f"/{path}"
    if not path.endswith("/"):
        path = f"{path}/"
    return path

