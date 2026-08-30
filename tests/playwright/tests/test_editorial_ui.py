"""Cool compact interface and explicit editorial-media regressions."""

from __future__ import annotations

from playwright.sync_api import Browser, Page


def test_homepage_curation_and_compact_desktop_viewport(page: Page, base_url: str) -> None:
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(f"{base_url}/en/")
    assert "Building ML systems people can actually use." in page.locator(".home-hero h1").inner_text()
    assert page.locator(".featured-piece h3").filter(has_text="Engineering Agents").count() == 1
    assert page.locator(".post-row").count() == 3
    assert page.locator(".thread-link").count() == 4
    assert page.locator(".home-grid").bounding_box()["y"] < 400  # type: ignore[index]


def test_homepage_has_no_horizontal_overflow_on_mobile(page: Page, base_url: str) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base_url}/en/")
    widths = page.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]")
    assert widths[0] <= widths[1] + 1


def test_article_picture_selects_role_for_viewport(page: Page, base_url: str) -> None:
    path = "/en/posts/genai/engineering-agents-building-trust/"
    page.set_viewport_size({"width": 1200, "height": 900})
    page.goto(f"{base_url}{path}")
    assert page.locator(".article-hero picture source[media='(max-width: 760px)']").count() == 1
    assert page.locator(".article-hero img").evaluate("image => image.currentSrc").endswith("hero-desktop.webp")
    page.set_viewport_size({"width": 390, "height": 844})
    page.reload()
    assert page.locator(".article-hero img").evaluate("image => image.currentSrc").endswith("hero-mobile.webp")


def test_archive_thumbnail_contract_search_filter_and_years(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/en/posts/")
    first = page.locator(".archive-thumb").first
    assert first.get_attribute("width") == "120"
    assert first.get_attribute("height") == "90"
    assert first.get_attribute("loading") == "lazy"
    assert page.locator(".archive-year > h2").all_inner_texts()[:3] == ["2026", "2025", "2024"]

    page.locator("[data-archive-search]").fill("Unicode surrogate")
    assert page.locator("[data-archive-row]:visible").count() == 1
    assert "Unicode" in page.locator("[data-archive-row]:visible h3").inner_text()
    page.locator("[data-archive-search]").fill("")
    page.locator("button[data-thread='Life & Learning']").click()
    assert page.locator("[data-archive-row]:visible").count() == 1


def test_archive_remains_complete_without_javascript(browser: Browser, base_url: str) -> None:
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(f"{base_url}/en/posts/")
        assert page.locator("[data-archive-row]").count() == 30
        assert page.locator("[data-archive-row]:visible").count() == 30
    finally:
        context.close()


def test_keyboard_focus_is_visible(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/en/")
    page.keyboard.press("Tab")
    outline = page.locator(":focus").evaluate("element => getComputedStyle(element).outlineStyle")
    assert outline != "none"
