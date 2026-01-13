# Playwright UI tests

This directory is a small, self-contained uv project that runs Playwright tests
against a local `hugo server` instance of this repo.

## Setup

```bash
cd tests/playwright
uv sync
uv run playwright install chromium
```

## Run

```bash
cd tests/playwright
uv run -m pytest
```

