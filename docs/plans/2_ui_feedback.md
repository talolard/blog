# UI Feedback & i18n Improvements

## Setup

* Setup Playwright and directories. Use the python playwright with pytest, manage that with uv and package.toml in a tests/playwright directory
* Add a beads formula (<https://steveyegge.github.io/beads/workflows/formulas>) that capture implementing, the tests that need to be added to verify etc.
* Create a main epic (Jan UI Feedback) subepics per headers here and individual tasks. Each task should derive from the formula where the formula specifies what to test, how we test (According to how playwright is setup )

## UX Fixes

*Fix the following UX issues and write a test for each:*

* The language selector should be a button with the flag or two letter lang code
* We don't have a contact page, make one with my email, twitter (thetalperry)
* Remove the subtitle `Writing on leadership, product, and machine learning`
* In the header image that is composed of letters, add a space between the Tal and Perry

## i18n Attributes

*Ensure and test the following attributes:*

* Set the page language: `<html lang="en">` according to the language
* Use `rel="alternate"` with `hreflang` to link translations
* Include `hreflang="x-default"` for a fallback page
* Use consistent, language-specific URLs (`/en/`, `/fr/`)
* Translate `<title>` and `<meta name="description">`
* Canonicalize each page to itself (per language)
* Use `lang` on elements for mixed-language content
* Always include `<meta charset="utf-8">`
* Add `dir="rtl"` for right-to-left languages

## Meta Tags

* **Declare the page encoding**
  * `<meta charset="utf-8">`
* **Make the page responsive**
  * `<meta name="viewport" content="width=device-width, initial-scale=1">`
* **Provide a translated, page-specific description**
  * `<meta name="description" content="Short description of this page">`
* **Allow search engines to index the page**
  * `<meta name="robots" content="index, follow">`
* **Add Open Graph metadata for social sharing** - Derive from Front Matter, add where needed
  * `<meta property="og:title" content="Page title">`
  * `<meta property="og:description" content="Page description">`
  * `<meta property="og:url" content="https://example.com/page">`
  * `<meta property="og:image" content="https://example.com/og.png">`
* **Add Twitter Card metadata** Derive from Front Matter, add where needed
  * `<meta name="twitter:card" content="summary_large_image">`
  * `<meta name="twitter:title" content="Page title">`
  * `<meta name="twitter:description" content="Page description">`
  * `<meta name="twitter:image" content="https://example.com/og.png">`
* **Set a theme color (optional)** Derive from Front Matter, add where needed
  * `<meta name="theme-color" content="#ffffff">`
