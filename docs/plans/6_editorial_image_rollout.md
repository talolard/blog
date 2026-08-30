# Cool, Compact Redesign and Editorial Image Rollout

## Outcome

- Port the accepted cool-gray V2 prototype into the Hugo site with a compact,
  precise editorial layout.
- Give every published post bundle a dedicated thumbnail, desktop hero, and
  mobile hero described by a co-located `art.toml` manifest.
- Add a typed, resumable, rate-limited OpenAI image-generation tool with
  atomic writes, provenance, validation, review artifacts, and fake-API tests.
- Keep the draft `writing-better-text` and all other drafts outside the paid
  generation and published-media contract.

## Production interface

- Self-host Familjen Grotesk and IBM Plex Mono.
- Use a 1180px shell, 64px header, cool canvas, cobalt and mint accents, fine
  rules, restrained radii, and no card shadows.
- Reduce the identity mark to three `TAL` letter tiles plus “Tal Perry”.
- Use Writing, Projects, About, and language navigation. The identity links
  home; contact remains in About and the footer.
- Curate the homepage around the ML-systems thesis, current-status rail,
  Engineering Agents feature, three recent pieces, and four editorial threads.
- Add a Projects & Experiments page for LightTag, the AI reading experiment,
  and the StableNormal/Modal experiment.
- Replace the archive grid with searchable, year-grouped rows and progressive
  client-side thread filters. All posts remain visible without JavaScript.

## Editorial media contract

| Role | File | Source dimensions | Intended display |
| --- | --- | ---: | ---: |
| Thumbnail | `thumbnail.webp` | 960×720 | 280×210 featured; 120×90 archive |
| Desktop hero | `hero-desktop.webp` | 1920×640 | about 1180×393 |
| Mobile hero | `hero-mobile.webp` | 960×720 | about 362×272 |

Article heroes use `<picture>` with the mobile source at 760px and below.
Templates read paths and localized alt text from `art.toml`; social assets and
body media are never fallbacks. Published posts fail editorial validation if
the contract is incomplete, while drafts render without editorial media.

Existing body-used `hero.webp` files are preserved under descriptive names:

- `papaya-seller-market.webp`
- `character-model-problems.webp`
- `top-repeated-reddit-comments.webp`
- `tokenizer-annotation-alignment.webp`

Generated output is WebP with compression 85 and remains covered by Git LFS.

## Generation pipeline

Create `tools/editorial-images`, managed by `uv`, with strict typing, short
modules, a mockable OpenAI client, and these selection modes:

```text
editorial-images --post PATH [--post PATH ...]
editorial-images --all-eligible
editorial-images --stale
editorial-images --force
editorial-images --dry-run
editorial-images --model MODEL
editorial-images --jobs N
editorial-images --requests-per-minute N
```

Defaults are model `gpt-image-2-2026-04-21`, high quality, direct WebP at
compression 85, two posts, at most four simultaneous image requests, and five
requests per minute. Retry 429 and 5xx responses at most four times, honoring
`Retry-After` and otherwise using exponential backoff with jitter. Moderation
and invalid-request failures are terminal.

Each request combines versioned common art direction, the complete normalized
English article, declared visual references, and role-specific constraints.
Generate desktop first; use it as visual reference while generating thumbnail
and mobile variants concurrently. Different posts may overlap. Publish all
three files and the manifest atomically only after the complete set succeeds.

The manifest records eligibility, audit mode, reference and article hashes,
prompt identity, model and Git revision, timestamps and request IDs, output
hashes/dimensions/compression, placement rules, and localized alt text.
Staleness is read-only and never performs paid work.

## Audit modes

- Preserve concept for all variants: ALMa, LightTag acquisition, SnorQL,
  Unicode surrogate pairs, Machine in the Loop.
- Preserve thumbnail concept but recompose heroes: Engineering Agents, Triton,
  Database Multi-Tenancy.
- Recompose factual material as editorial art: tokenizer alignment, Complement
  Objective, Embrace the Noise, Krippendorff’s Alpha, React/dc.js, Sequence
  Labeling.
- Regenerate concept for the remaining sixteen bundles.

## Rollout and review

- Generate and validate the five-post proof of concept first: Vibe/Modal,
  Engineering Agents, Learning to Read, Triton, and Scripture App.
- Continue through the other twenty-five bundles after the real trace proves
  dependency order, sibling overlap, cross-post overlap, and configured limits.
- Serialize Git operations, reject dirty bundle scopes, stage explicit bundle
  paths, and create one `Add editorial art for …` commit per post.
- Generate an ignored `artifacts/editorial-image-review/` gallery with contact
  sheets, grouped indexes, actual-size previews, and a run report.
- Provide `make art-review` and `make art-review-serve`.

## Acceptance

- Tests cover manifest parsing, hashes and staleness, prompt assembly, exact
  selection, retry behavior, atomic publication, resumability, explicit-path
  commits, and delayed-fake concurrency behavior.
- Validate all ninety generated assets as decodable WebP with exact dimensions,
  recorded hashes, required manifest fields, localized alt text, and LFS rules.
- Ensure every Markdown image resolves and social/share inputs are unchanged.
- Add browser coverage for responsive editorial media, image loading/display,
  homepage composition, archive search/filter/year behavior, no-JS fallback,
  drafts, i18n/RTL, keyboard focus, long titles, and overflow.
- Finish with these commands and leave both local review servers responding 200:

```bash
uv run --project tools/editorial-images pytest
uv run --project tools/editorial-images basedpyright
make build
make validate
cd tests/playwright && uv run -m pytest
```

## Safety and assumptions

- Paid generation never runs in tests, CI, dry runs, validation, or stale
  reporting.
- `.env` is ignored and its API key is never printed.
- Existing social media and share packs remain unchanged.
- Existing unrelated work is preserved.
