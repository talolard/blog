# Restore the LightTag Blog Archive

## Summary

Restore all 23 LightTag articles from Git commit
`cf732457d8bc850314c48b887a9db10f2787dfa8`, using the Internet Archive copy to
verify published content and recover missing media. Publish them as English
Hugo page bundles under `/en/posts/lighttag/`, preserving original publication
dates and graphics while conservatively proofreading the prose.

Do not use or reinitialize Beads.

## Implementation

- Import the 22 source `index.md` articles plus the Hugging Face tokenizer
  alignment companion article. Include the acquisition
  announcement and `/how-to-label-data/`; exclude Gatsby code, the notebook,
  and unused assets.
- Derive lowercase kebab-case slugs from the original published paths,
  correcting `imporvement` to `improvement`; use
  `code-to-align-annotations-with-huggingface-tokenizers` for the companion.
- Add complete TOML front matter, original publication provenance, per-post
  social metadata, and enabled English share packs.
- Render the exact, unlinked notice “Originally published at LightTag.io.”
  immediately below imported article headers, without affecting other posts.
- Conservatively correct spelling, grammar, punctuation, title casing,
  malformed Markdown, and metadata while preserving voice, structure,
  historical claims, code, and technical meaning.
- Rewrite archive cross-links locally, remove links to defunct LightTag product
  pages while preserving their labels, and retain valid third-party links.
- Convert referenced media to descriptive WebP files, preserving animation,
  and recover the acquisition announcement graphic from the archived social
  presentation.
- Use original representative artwork for `hero.webp` when available. Compose
  a unique 1200×630 `social.webp` for every post without generating replacement
  artwork.

## URLs and provenance

- Canonical URLs: `/en/posts/lighttag/<clean-slug>/`.
- Original paths remain only in `[original_publication]` front matter and are
  never linked.
- Existing canonical, Open Graph, and structured-data behavior remains
  unchanged apart from post-specific descriptions and social images.

## Verification

- Parameterize all 23 slug/date/title records and verify rendering, original
  dates, exact unlinked attribution, and image responses.
- Verify existing posts have no attribution, no imported content links to
  `lighttag.io` or `guide.lighttag.io`, and local cross-post links resolve.
- Verify animated WebPs remain animated and all WebPs use Git LFS.
- Visually inspect representative image-, animation-, code-, and table-heavy
  posts plus one without an original hero on desktop and mobile.
- Run Vale/pre-commit checks on changed files, `hugo --minify`, `make validate`,
  and the complete Playwright suite.

## Assumptions

- Git front-matter dates are authoritative, including surprising dates.
- The archive is English-only.
- Attribution is plain text with no original or archived link.
- No factual modernization or retrospective rewriting is included.
- Unrelated uncommitted work is preserved.
