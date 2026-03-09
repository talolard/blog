# Social Previews and Share Pack

This document defines the required metadata and share-pack workflow for post bundles under `content/posts/**/`.

## Goals

- Rich previews with images across WhatsApp, LinkedIn, X/Twitter, Reddit, Slack, and other Open Graph unfurlers.
- Consistent, high-quality metadata for search engines and AI systems that read page metadata.
- Complete, reusable cross-platform posting copy in TOML sidecar files.

## Required Front Matter Fields

For each published post (`draft = false`), set these fields in front matter:

```toml
+++
title = "..."
date = 2026-03-09T02:11:00+01:00
draft = false
description = "..."

[social]
image = "social.png"
image_alt = "..."

[share]
disable = false
# Optional override; default is all available language files in the bundle.
# languages = ["en", "de", "he"]
+++
```

Rules:
- `description` must be post-specific, not the site tagline.
- `social.image` should usually point to a local bundle file.
- `social.image_alt` is required and should describe what matters in the image.

## Social Image Rules

Image validator (`scripts/validate_social_meta.py`) enforces:
- minimum dimensions: `1200x630`
- aspect ratio: between `1.86` and `1.96`
- hard size cap: `5MB`

Image source selection order:
1. `social.image` in front matter
2. `social.*` in the page bundle
3. `hero.*` in the page bundle
4. first image resource in bundle
5. global fallback `static/og/default.png`

If any article resolves to a non-compliant image, build validation fails.
If an article resolves to the global fallback image, build validation fails.
If multiple different posts reuse the same social image bytes, build validation fails.

## share.toml Schema (Required)

Each published bundle must include `share.toml` unless `share.disable = true`.

```toml
version = 1

[languages.en]
canonical_path = "/en/posts/.../"
one_liner = "..."
hook = "..."
cta = "..."

[twitter.en]
post_text = "..."
alt_text = "..."
hashtags = ["...", "..."]
emoji = false
# Optional
# thread = ["...", "..."]

[linkedin.en]
post_text = "..."
alt_text = "..."
# Optional
# tags = ["...", "..."]

[reddit.en]
title = "..."
# Optional
# subreddit = "..."
post_text = "..."

[hn.en]
title = "..."
# Optional
# submission_text = "..."
first_comment = "..."
```

For translated posts, include equivalent tables for each language unless you set `share.languages` to a subset.

## Validation Commands

- `make validate-social` builds the site and validates rendered metadata + image compliance.
- `make validate-share` validates all `share.toml` files against required fields.
- `make validate` runs both.

## AI Authoring Instructions

When asking AI to populate `description`, social front matter, and `share.toml`, use this brief:

1. Read the full post content (and translations if present) before writing any field.
2. Optimize for engagement while staying true to Tal's voice and the post's actual claims.
3. Fill all required fields completely; do not leave placeholders or blank strings.
4. Keep copy concrete and specific. Avoid hype language and invented outcomes.
5. Produce platform-native copy, not one generic sentence repeated everywhere.

Prompt template:

```text
You are writing metadata and share copy for talperry.com.

Task:
- Read the full post markdown.
- Generate front matter fields:
  - description
  - social.image_alt
- Generate a complete share.toml with every required field populated for all post languages.

Quality bar:
- Optimize for engagement while staying faithful to the actual post and Tal's voice.
- Voice: direct, reflective, technical, not salesy.
- No clickbait, no invented claims, no generic filler.
- Each platform copy must include a clear hook, concrete value, and a real invitation to respond.

Output format:
- Return exact TOML for share.toml.
- Return exact front matter snippets per language file.
- No markdown fences. No placeholders.
```

## Writing Guidance by Platform

- X/Twitter:
  - first sentence carries the core idea
  - include one clear takeaway and one ask
  - keep under 280 characters unless using `thread`
- LinkedIn:
  - short opening thesis line
  - 3-5 short lines with concrete details
  - close with a discussion invitation
- Reddit:
  - transparent context, plain language, non-promotional title
  - share what you learned and one open question
- Hacker News:
  - neutral title
  - concise first comment focused on the core argument and why it matters
