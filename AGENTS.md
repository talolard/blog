# Repository Guidelines

## Project Structure & Module Organization
- Hugo site root: `hugo.toml`, content under `content/`, layouts and partials in `layouts/`, styles in `assets/scss/`. Theme overrides live in `layouts/` and `assets/` (we don’t edit the theme directly).
- Media: letter art stored as WebP in `assets/letters/` (Git LFS). Post-specific images live alongside their Markdown files in `content/posts/**/`.
- Workflows: GitHub Actions in `.github/workflows/`. VS Code defaults in `.vscode/settings.json`.
- SCSS entrypoint: `assets/scss/styles.scss` imports modular partials: `base/` (variables/reset/typography), `layout/` (shell/header), `components/` (hero/cards/article/footer), `utilities/` (a11y, animations, media queries). Add new styles as partials and import from the entrypoint.

## Build, Test, and Development Commands
- `make serve`: run `hugo server -D --disableFastRender --gc` for local preview.
- `make build`: production build (`hugo` with defaults set in `hugo.toml`).
- `make clean`: remove `public/` and `resources/` build artifacts.
- Note: install Git LFS (`git lfs install && git lfs pull`) before builds so letter assets are available.

## Coding Style & Naming Conventions
- Hugo templating: prefer overrides in `layouts/partials/`, `_default/`, and shortcodes. Keep templates concise and avoid logic-heavy constructs.
- SCSS: resides in `assets/scss/styles.scss`; use CSS variables defined at `:root`, clamp-based typography, and keep comments minimal and purposeful.
- Markdown content: front matter in TOML/shortcode style; co-locate images with posts when specific to that post.

## Testing Guidelines
- Primary check is a clean `hugo --minify` build; run `make build` before committing. No automated test suite beyond build validation.

## Commit & Pull Request Guidelines
- Commit messages: present-tense, concise (e.g., “Add letter gallery shortcode”, “Refine card grid alignment”).
- PRs: include a brief summary of visual/UX changes and screenshots when altering layout or styles; link related issues if applicable. Ensure Git LFS pointers are committed for `assets/letters/*.webp`.

## Tooling & Pre-commit
- Install pre-commit: `pip install pre-commit` then `pre-commit install`.
- Hooks run stylelint (SCSS), markdownlint, vale, djlint, yamllint, lychee, plus custom image handling:
  - `convert_to_webp.py` converts staged png/jpg/jpeg to WebP and re-stages them.
  - `enforce_lfs_webp.py` ensures WebP files use Git LFS. LFS rule: `*.webp` in `.gitattributes`.
- Configs: `.stylelintrc.json`, `.markdownlint.yaml`, `.vale.ini`, `.djlintrc`, `.yamllint.yml`, `.lychee.toml`.
