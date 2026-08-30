# Editorial image operator guide

This tool generates the three editorial images used by each published post:

- `thumbnail.webp` — 960×720 source, displayed at 280×210 or 120×90
- `hero-desktop.webp` — 1920×640
- `hero-mobile.webp` — 960×720

It generates the desktop hero first, then uses that result as the visual reference
while generating the thumbnail and mobile hero together. Outputs are published only
when all three images succeed.

## Change the art for a post

The main art brief is in [`data/editorial_posts.toml`](../../data/editorial_posts.toml).
Each post has these controls:

- `concept` is the requested visual outcome. Change this first when you want a
  different metaphor, subject, mood, or composition.
- `references` lists bundle-local images that may inform the concept. Remove a
  reference when it anchors the generator too strongly; add an existing image when
  its subject matter is useful. Diagrams and screenshots are treated as semantic
  references, not layouts to copy.
- `alt_de` and `alt_he` are localized descriptions of the concept. Update them when
  a changed concept makes the old descriptions inaccurate.
- `audit_mode` records how the image relates to the old art and groups the review
  gallery. It does not select a different generation algorithm.
- `thread` controls the post's editorial category on the site; it is not primarily
  an art control, although it is included in the prompt.

The shared visual language and role-specific composition rules are in
[`src/editorial_images/prompting.py`](src/editorial_images/prompting.py). Edit
`COMMON_DIRECTION` for a site-wide style change and `role_constraints()` for a
particular placement. Whenever prompt behavior changes, increment `PROMPT_VERSION`.
That makes affected manifests appear in `--stale` instead of silently looking
current.

The exact filenames and dimensions live in
[`src/editorial_images/models.py`](src/editorial_images/models.py) as `ROLE_SPECS`.
Changing them also requires coordinated Hugo template, CSS, manifest, and test
changes, so concepts and prompts are the safer everyday controls.

## Preview and generate

Commands run from the repository root. Read-only preview of one post:

```bash
uv run --project tools/editorial-images editorial-images \
  --post content/posts/lighttag/context-is-king --dry-run
```

Generate one post, or repeat `--post` to generate an exact set:

```bash
uv run --project tools/editorial-images editorial-images \
  --post content/posts/lighttag/context-is-king \
  --post content/posts/lighttag/indexeddb-for-nlp \
  --commit
```

List missing or changed posts without making paid requests:

```bash
uv run --project tools/editorial-images editorial-images --stale
```

Resume the archive rollout safely:

```bash
uv run --project tools/editorial-images editorial-images \
  --all-eligible --jobs 2 --requests-per-minute 5 --commit
```

`--all-eligible` skips posts whose manifest and files are current, so the command is
also the normal resume command. Add `--force` only when you deliberately want to pay
to replace otherwise-current art. Use `--model MODEL` to test another supported image
model. The API key is loaded from the repository `.env` and is never needed on the
command line.

One operational detail: `--commit` commits generated posts only after the entire
selected run returns. If you stop a run, any fully published bundles remain safe but
uncommitted; incomplete staging output is discarded. Commit those completed bundles
before resuming, because generation refuses to overwrite a dirty post bundle.

## Do more in parallel

Two settings govern throughput:

- `--jobs N` is the number of posts allowed to progress at once. The default is 2.
- `--requests-per-minute N` spaces API request starts to match your account's image
  rate limit. The default is 5.

There is also a safety ceiling of four simultaneous image requests in
[`src/editorial_images/runner.py`](src/editorial_images/runner.py). More jobs help
while desktop heroes are in flight and while each post's two dependent variants run,
but they cannot exceed that request ceiling or the configured start rate.

For example, if your account supports at least 20 image requests per minute:

```bash
uv run --project tools/editorial-images editorial-images \
  --all-eligible --jobs 4 --requests-per-minute 20 --commit
```

Raise the request rate only to a limit your account actually supports. A larger
`--jobs` value alone does not bypass the four-request ceiling. If you intentionally
want a different ceiling, change `maximum_concurrent=4` in `generate_posts()` and run
the concurrency tests before generating.

`--dry-run`, `--stale`, `--validate`, `--review`, and the test suite do not generate
images. Other generation commands make paid API requests.

## Check the result

Validate a specific completed post before reviewing it:

```bash
uv run --project tools/editorial-images editorial-images \
  --post content/posts/lighttag/context-is-king --validate
```

Build and serve the local contact-sheet gallery:

```bash
make art-review
make art-review-serve
```

The gallery is written to `artifacts/editorial-image-review/`, which is intentionally
not committed. Run the tool tests after changing the pipeline itself:

```bash
uv run --project tools/editorial-images pytest
uv run --project tools/editorial-images basedpyright
```
