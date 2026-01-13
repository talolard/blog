"""RTL-only layout regressions.

Hebrew is an RTL language, but specific UI elements should keep LTR order
(`Tal Perry` lettermark and the nav row). Separately, the TOC should not push
the article body below it due to RTL grid overrides.
"""

from __future__ import annotations

from playwright.sync_api import Page


def test_header_nav_and_letters_keep_ltr_order_in_rtl_language(page: Page, base_url: str) -> None:
    """Force LTR direction for header nav + lettermark while keeping document RTL."""

    page.goto(f"{base_url}/he/")

    nav_direction = page.evaluate(
        "() => getComputedStyle(document.querySelector('.nav-list')).direction"
    )
    assert nav_direction == "ltr"

    brand_direction = page.evaluate(
        "() => getComputedStyle(document.querySelector('.brand-letters a')).direction"
    )
    assert brand_direction == "ltr"


def test_hebrew_post_toc_does_not_push_body_below(page: Page, base_url: str) -> None:
    """TOC + body should share the same grid row in Hebrew posts with a TOC."""

    page.goto(f"{base_url}/he/posts/genai/triton-inference-server/")
    page.wait_for_selector(".article-layout:has(.toc)")

    toc_box = page.locator(".article-layout .toc").bounding_box()
    body_box = page.locator(".article-layout .article-body").bounding_box()
    assert toc_box is not None and body_box is not None
    assert abs(toc_box["y"] - body_box["y"]) < 5


def test_hebrew_post_code_blocks_render_ltr(page: Page, base_url: str) -> None:
    """Code blocks should remain LTR even on RTL pages."""

    page.goto(f"{base_url}/he/posts/genai/triton-inference-server/")
    page.wait_for_selector("pre code")

    direction = page.evaluate(
        "() => getComputedStyle(document.querySelector('pre')).direction"
    )
    assert direction == "ltr"
