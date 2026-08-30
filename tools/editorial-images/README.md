# Editorial image operator guide

This tool generates the three editorial images used by each published post:

- `thumbnail.webp` — 960×720 source, displayed at 280×210 or 120×90
- `hero-desktop.webp` — 1920×640
- `hero-mobile.webp` — 960×720

For a post without a current `scene-plan.json`, a multimodal scene planner first reads
the complete article and both Tal identity photographs. It stores one canonical,
reviewable scene description. The renderer then generates the desktop hero first and
uses that result plus the identity photographs while generating the thumbnail and
mobile hero together. The plan, manifest, and all three outputs are published only
when the complete rendering set succeeds.

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

The generated `scene-plan.json` beside each post records the chosen physical metaphor,
miniature setting, humor register, Tal's role, frozen incident, materials, semantic
anchors, avoid-list, and final image instruction. A normal `--force` run reuses this
plan. To deliberately ask the planner for a different canonical scene, use both
`--replan` and `--force`:

```bash
uv run --project tools/editorial-images editorial-images \
  --post content/posts/lighttag/context-is-king --replan --force
```

The two identity sources are `me1.jpeg` and `me2.jpeg` at the repository root. Both
are hashed planning inputs and are sent as image references for every generated role.
In `me2.jpeg`, Tal is the adult behind the child; the prompts explicitly exclude the
child as an identity reference.

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
command line. The planner defaults to the pinned `gpt-5.4-mini-2026-03-17` snapshot;
override it with `--planner-model MODEL` only when intentionally testing the planning
stage.

Generation writes timestamped progress to the console as it runs. It reports each
post and role as they are queued, request-rate waits, API request starts and IDs,
retries, skips, failures, and the atomic publication of each complete three-image set.

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
Scene-planning requests also overlap according to `--jobs`; the image-request cadence
does not apply to those text-and-vision requests.

For example, if your account supports at least 20 image requests per minute:

```bash
uv run --project tools/editorial-images editorial-images \
  --all-eligible --jobs 4 --requests-per-minute 20 --commit
```

Raise the request rate only to a limit your account actually supports. A larger
`--jobs` value alone does not bypass the four-request ceiling. If you intentionally
want a different ceiling, change `maximum_concurrent=4` in `generate_posts()` and run
the concurrency tests before generating.

`--dry-run`, `--stale`, `--validate`, `--review`, and the test suite make no model
requests. A generation command makes one paid planning request when a current scene
plan is unavailable, followed by three paid image requests. Reusing a current plan
skips the planning request.

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
