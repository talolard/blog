# Repository Guidelines

## Project Structure & Module Organization

- Hugo site root: `hugo.toml`, content under `content/`, layouts and partials in `layouts/`, styles in `assets/scss/`. Theme overrides live in `layouts/` and `assets/` (we don’t edit the theme directly).
- Media: letter art stored as WebP in `assets/letters/` (Git LFS). Post-specific images live alongside their Markdown files in `content/posts/**/`.
- Workflows: GitHub Actions in `.github/workflows/`. VS Code defaults in `.vscode/settings.json`.
- SCSS entrypoint: `assets/scss/styles.scss` imports modular partials: `base/` (variables/reset/typography), `layout/` (shell/header), `components/` (hero/cards/article/footer), `utilities/` (a11y, animations, media queries). Add new styles as partials and import from the entrypoint.
- Styling concepts: cards align via grid rows (cover/meta/title/excerpt/tags); covers framed with thin borders and gradient fade; clamp-based typography and 16:9 covers with `object-fit: cover`.

## Build, Test, and Development Commands

- `make serve`: run `hugo server -D --disableFastRender --gc` for local preview.
- `make build`: production build (`hugo` with defaults set in `hugo.toml`).
- `make clean`: remove `public/` and `resources/` build artifacts.
- Note: install Git LFS (`git lfs install && git lfs pull`) before builds so letter assets are available.

## Coding Style & Naming Conventions

- Hugo templating: prefer overrides in `layouts/partials/`, `_default/`, and shortcodes. Keep templates concise and avoid logic-heavy constructs.
- SCSS: resides in `assets/scss/` partials; use `:root` tokens, clamp-based typography, and minimal comments.
- Markdown content: TOML-style front matter; co-locate post-specific media. Prefer WebP; templates should provide width/height on `<img>` where practical.
- Post images: when cleaning imported posts, rename assets to descriptive filenames, convert PNG/JPEG/GIF to WebP (use `cwebp` for stills and `gif2webp` for animations), remove originals, and update markdown links with meaningful alt text. Preserve animation intent when converting GIFs.

## Testing Guidelines

- Primary check is a clean `hugo --minify` build; run `make build` before committing. No automated test suite beyond build validation.

## Commit & Pull Request Guidelines

- Commit messages: present-tense, concise (e.g., “Add letter gallery shortcode”, “Refine card grid alignment”).
- PRs: include a brief summary of visual/UX changes and screenshots when altering layout or styles; link related issues if applicable. Ensure Git LFS pointers are committed for `*.webp`.

## Tooling & Pre-commit

- Install pre-commit: `pip install pre-commit` then `pre-commit install`.
- Hooks: hygiene (YAML/EOF/trailing whitespace/large files), image handling (convert_to_webp.py, enforce_lfs_webp.py), stylelint (SCSS), yamllint. Markdownlint/vale/djlint can be run manually if desired. Lychee is currently disabled.
- Config files: `.stylelintrc.json`, `.markdownlint.yaml`, `.vale.ini`, `.djlintrc`, `.yamllint.yml`.
