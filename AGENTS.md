# Repository Guidelines

* Put plans in docs/plans/{num}_{name}.md

## Project Structure & Module Organization

* Hugo site root: `hugo.toml`, content under `content/`, layouts and partials in `layouts/`, styles in `assets/scss/`. Theme overrides live in `layouts/` and `assets/` (we don’t edit the theme directly).
* Media: letter art stored as WebP in `assets/letters/` (Git LFS). Post-specific images live alongside their Markdown files in `content/posts/**/`.
* Workflows: GitHub Actions in `.github/workflows/`. VS Code defaults in `.vscode/settings.json`.
* SCSS entrypoint: `assets/scss/styles.scss` imports modular partials: `base/` (variables/reset/typography), `layout/` (shell/header), `components/` (hero/cards/article/footer), `utilities/` (a11y, animations, media queries). Add new styles as partials and import from the entrypoint.
* Styling concepts: cards align via grid rows (cover/meta/title/excerpt/tags); covers framed with thin borders and gradient fade; clamp-based typography and 16:9 covers with `object-fit: cover`.

## Build, Test, and Development Commands

* `make serve`: run `hugo server -D --disableFastRender --gc` for local preview.
* `make build`: production build (`hugo` with defaults set in `hugo.toml`).
* `make clean`: remove `public/` and `resources/` build artifacts.
* Note: install Git LFS (`git lfs install && git lfs pull`) before builds so letter assets are available.

## Coding Style & Naming Conventions

* Hugo templating: prefer overrides in `layouts/partials/`, `_default/`, and shortcodes. Keep templates concise and avoid logic-heavy constructs.
* SCSS: resides in `assets/scss/` partials; use `:root` tokens, clamp-based typography, and minimal comments.
* Markdown content: TOML-style front matter; co-locate post-specific media. Prefer WebP; templates should provide width/height on `<img>` where practical.
* Post images: when cleaning imported posts, rename assets to descriptive filenames, convert PNG/JPEG/GIF to WebP (use `cwebp` for stills and `gif2webp` for animations), remove originals, and update markdown links with meaningful alt text. Preserve animation intent when converting GIFs.

## Testing Guidelines

* Primary check is a clean `hugo --minify` build; run `make build` before committing.
* UI regression tests live in `tests/playwright/` (Python + pytest + Playwright, managed with `uv`).
  * First-time setup: `cd tests/playwright && uv sync && uv run playwright install --with-deps chromium`
  * Run: `cd tests/playwright && uv run -m pytest`
  * Tests start a local `hugo server` and assert rendered HTML/CSS behavior (i18n + meta + RTL layout).
* CI runs the Playwright suite via `.github/workflows/playwright.yaml`.

## Commit & Pull Request Guidelines

* Commit messages: present-tense, concise (e.g., “Add letter gallery shortcode”, “Refine card grid alignment”).
* PRs: include a brief summary of visual/UX changes and screenshots when altering layout or styles; link related issues if applicable. Ensure Git LFS pointers are committed for `*.webp`.

## Tooling & Pre-commit

* Install pre-commit: `pip install pre-commit` then `pre-commit install`.
* Hooks: hygiene (YAML/EOF/trailing whitespace/large files), image handling (convert_to_webp.py, enforce_lfs_webp.py), stylelint (SCSS), yamllint. Markdownlint/vale/djlint can be run manually if desired. Lychee is currently disabled.
* Config files: `.stylelintrc.json`, `.markdownlint.yaml`, `.vale.ini`, `.djlintrc`, `.yamllint.yml`.

## Social previews and share packs

* Follow `docs/social_share_pack.md` for metadata and `share.toml` requirements.
* For each published post, populate complete front matter social fields and a complete `share.toml` (unless explicitly disabled).
* When using AI to fill fields, optimize for engagement while staying true to Tal's voice and the post's real content.
* Do not leave placeholder text or partial platform entries; fill all required fields for each post language.
* Run `make validate` before finishing metadata/share-pack changes.

## LightTag redirect operations

* The sole tracker for the two-phase redirect migration is
  `docs/plans/4_restore_lighttag_redirects.md`; update its root checklist and
  evidence log rather than creating a second tracker or checklist.
* Keep worker ownership disjoint: one worker owns each declared file scope,
  and workers must not concurrently edit the same file. The P1.C operability
  scope is `infra/lighttag-redirects/README.md`, the root `Makefile`, this root
  `README.md`, and this file; preserve unrelated changes.
* Luna owns implementation coordination and Sol performs the independent
  review. A redirect implementation is not production-complete until the Sol
  review gate in the plan is accepted.
* The redirect map is explicit. Unknown LightTag paths must return `410 Gone`;
  never add a catch-all redirect to the home page or an unrelated article.
* Search-engine and IndexNow submissions are external side effects. They are
  Phase 2 owner-approved operations and must never be tests, validation, or CI.
* Retain the redirect stack and mappings for at least one year, preferably
  indefinitely, because historical backlinks and crawlers are long-lived.
