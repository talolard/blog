"""Mobile TOC layout checks for single-article pages.

These tests ensure the table of contents does not force a narrow text column
on small viewports by validating the TOC stacks above the article body.
"""

from __future__ import annotations

from typing import Iterable

import pytest
from playwright.sync_api import Browser, Page

VIEWPORTS: Iterable[tuple[int, int]] = (
    (360, 740),
    (375, 812),
    (414, 896),
)
POST_PATH = "/en/posts/genai/triton-inference-server/"


def _assert_toc_stacked(page: Page) -> None:
    """Assert TOC and article body are vertically stacked on mobile."""

    toc = page.locator(".toc")
    body = page.locator(".article-body")

    assert toc.count() == 1, "Expected a TOC on the article page."
    assert body.count() == 1, "Expected the article body container."

    assert toc.is_visible()
    assert body.is_visible()

    toc_box = toc.bounding_box()
    body_box = body.bounding_box()

    assert toc_box is not None, "TOC should have a measurable box."
    assert body_box is not None, "Article body should have a measurable box."

    toc_bottom = toc_box["y"] + toc_box["height"]
    assert body_box["y"] >= toc_bottom - 1, "Body should appear below the TOC."

    x_delta = abs(body_box["x"] - toc_box["x"])
    assert x_delta <= 6, "TOC and body should align on the same column."


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_article_toc_stacks_on_mobile_viewports(
    browser: Browser, base_url: str, viewport: tuple[int, int]
) -> None:
    """The TOC should stack above the article body on mobile viewports."""

    context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
    try:
        page = context.new_page()
        page.goto(f"{base_url}{POST_PATH}")
        page.wait_for_selector(".article-layout")
        _assert_toc_stacked(page)
    finally:
        context.close()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_article_layout_avoids_horizontal_overflow_on_mobile(
    browser: Browser, base_url: str, viewport: tuple[int, int]
) -> None:
    """The article layout should not overflow horizontally on mobile."""

    context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
    try:
        page = context.new_page()
        page.goto(f"{base_url}{POST_PATH}")
        page.wait_for_selector(".article-layout")

        metrics = page.evaluate(
            """
            () => {
              const layout = document.querySelector('.article-layout');
              const body = document.querySelector('.article-body');
              return {
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                layoutWidth: layout?.clientWidth ?? 0,
                bodyWidth: body?.clientWidth ?? 0,
              };
            }
            """
        )

        assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1, (
            "Document should not be wider than the viewport on mobile."
        )
        assert metrics["bodyWidth"] <= metrics["layoutWidth"] + 1, (
            "Article body should fit within the layout column on mobile."
        )
    finally:
        context.close()
