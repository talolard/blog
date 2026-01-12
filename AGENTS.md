# Repository Guidelines

* We use beads for task managment. Please follow the beads workflows described below.
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

* Primary check is a clean `hugo --minify` build; run `make build` before committing. No automated test suite beyond build validation.

## Commit & Pull Request Guidelines

* Commit messages: present-tense, concise (e.g., “Add letter gallery shortcode”, “Refine card grid alignment”).
* PRs: include a brief summary of visual/UX changes and screenshots when altering layout or styles; link related issues if applicable. Ensure Git LFS pointers are committed for `*.webp`.

## Tooling & Pre-commit

* Install pre-commit: `pip install pre-commit` then `pre-commit install`.
* Hooks: hygiene (YAML/EOF/trailing whitespace/large files), image handling (convert_to_webp.py, enforce_lfs_webp.py), stylelint (SCSS), yamllint. Markdownlint/vale/djlint can be run manually if desired. Lychee is currently disabled.
* Config files: `.stylelintrc.json`, `.markdownlint.yaml`, `.vale.ini`, `.djlintrc`, `.yamllint.yml`.

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

* Dependency-aware: Track blockers and relationships between issues
* Git-friendly: Auto-syncs to JSONL for version control
* Agent-optimized: JSON output, ready work detection, discovered-from links
* Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

### Preferred templates (protos)

Use these templates first (they encode this repo’s Hugo + media + validation conventions). Templates are epics labeled `template` and can be instantiated with `bd mol pour` (persistent) or `bd mol wisp` (ephemeral).

**List templates:**

```bash
bd list --label template --include-templates --pretty
```

**Show a template and required variables:**

```bash
bd --no-daemon mol show <proto-id>
```

**Instantiate a template:**

```bash
bd mol pour <proto-id> --var key=value --var other=value
```

**Templates in this repo:**

- Generic epic: `tb-mft`
- Generic issue: `tb-2nn`
- Maintenance task: `tb-ehl`
- Post editing: `tb-epp`
- Translation: `tb-4dx`

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

* `bug` - Something broken
* `feature` - New functionality
* `task` - Work item (tests, docs, refactoring)
* `epic` - Large feature with subtasks
* `chore` - Maintenance (dependencies, tooling)

### Priorities

* `0` - Critical (security, data loss, broken builds)
* `1` - High (major features, important bugs)
* `2` - Medium (default, nice-to-have)
* `3` - Low (polish, optimization)
* `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   * `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:

* Exports to `.beads/issues.jsonl` after changes (5s debounce)
* Imports from JSONL when newer (e.g., after `git pull`)
* No manual export/import needed!

### Important Rules

* ✅ Use bd for ALL task tracking
* ✅ Always use `--json` flag for programmatic use
* ✅ Link discovered work with `discovered-from` dependencies
* ✅ Check `bd ready` before asking "what should I work on?"
* ❌ Do NOT create markdown TODO lists
* ❌ Do NOT use external issue trackers
* ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

<!-- END BEADS INTEGRATION -->

### Writing issues in BD

* Always use cleanly formated markdown
* Epics should state our overall goal
* Issues should refer to epics and have self contained context
* Each issue should speficy:
  * Commit with clear commit message
  * Run our lints often
