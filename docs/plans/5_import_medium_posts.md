# Import and Consolidate the Medium Archive

## Summary

Import the six standalone articles from Tal's Medium feed that are not already
on the site. Publish them as English Hugo page bundles under
`/en/posts/medium/`, preserving their original publication dates, media, code,
and historical meaning while conservatively proofreading the prose.

Exclude the short 2020 response and avoid duplicating the three Medium articles
already on TalPerry.com. After deployment, consolidate SEO signals for all nine
standalone Medium stories by setting their Medium canonical links to the
corresponding TalPerry.com pages.

## Import Set

| Published | Corrected title | Local slug |
| --- | --- | --- |
| 2019-05-27T23:27:30Z | Four Mistakes You Make When Labeling Data | `four-mistakes-you-make-when-labeling-data` |
| 2019-01-28T12:28:36Z | Five Mistakes I Made as a New CEO | `five-mistakes-i-made-as-a-new-ceo` |
| 2019-01-14T16:13:03Z | I Went to the German Alps and Applied Reinforcement Learning to Financial Portfolio Optimization | `i-went-to-the-german-alps-and-applied-reinforcement-learning-to-financial-portfolio-optimization` |
| 2018-05-14T11:40:41Z | Announcing LightTag: The Easy Way to Annotate Text | `announcing-lighttag-the-easy-way-to-annotate-text` |
| 2018-02-19T14:08:12Z | Getting Text into TensorFlow with the Dataset API | `getting-text-into-tensorflow-with-the-dataset-api` |
| 2018-01-15T22:14:38Z | On Labeled Data | `on-labeled-data` |

The existing canonical destinations for the other three stories are:

- Active Learning:
  `/en/posts/lighttag/active-learning-optimization-is-not-improvement/`
- Convolutional Methods for Text: `/en/posts/classics/cmft/`
- Deep Learning the Stock Market: `/en/posts/classics/dlsm/`

## Implementation Changes

- Use Medium RSS as the authoritative source for content, timestamps, tags,
  canonical Medium paths, figures, and captions.
- Add TOML front matter with the original `date`, a migration-time `lastmod`, a
  faithful description, normalized Medium tags, complete social metadata,
  English share-pack configuration, and:

  ```toml
  [original_publication]
  site = "Medium.com"
  path = "/original/medium/path-with-post-id"
  ```

- Generalize the attribution template to render `.original_publication.site`.
  Medium posts display exactly “Originally published at Medium.com.” without a
  link; existing LightTag attribution remains unchanged.
- Convert Medium HTML into Hugo-safe Markdown. Remove tracking pixels,
  syndication boilerplate, duplicate headings, and unsupported embeds.
- Correct spelling, grammar, punctuation, title casing, captions, and malformed
  Markdown while preserving Tal's voice, historical claims, code, and technical
  meaning.
- Rewrite self-links to local TalPerry.com pages. Preserve valid third-party
  links and remove defunct LightTag product links while retaining their visible
  prose.
- Recover all 39 referenced graphics, convert them to descriptively named
  WebPs, and preserve all eight animations. Track every WebP with Git LFS.
- Replace seven Gist embeds with local fenced code blocks copied verbatim.
  Replace three YouTube iframes with ordinary links to the exact videos and
  original timestamp where applicable.
- Use a dedicated original cover as `hero.webp` only where Medium clearly
  supplied one. Keep narrative figures in their original positions and prevent
  generated social cards from becoming article heroes.
- Create six unique, crop-safe 1200×630 social cards from original artwork and
  corrected titles; do not generate AI artwork.
- Create complete English `share.toml` files with canonical
  `/en/posts/medium/<slug>/` paths and platform-specific copy.

## SEO Migration and Release

- Keep every TalPerry.com page self-canonical. Verify `rel=canonical`, `og:url`,
  `BlogPosting.mainEntityOfPage`, original `datePublished`, migration
  `dateModified`, and `index, follow` all point or apply to the TalPerry.com
  page.
- Verify all nine target URLs appear in `https://talperry.com/sitemap.xml` and
  are linked from the English archive or relevant article cross-links.
- Commit only the Medium migration changes, preserving unrelated working-tree
  changes, then deploy through the existing GitHub Pages workflow.
- Wait until all nine TalPerry.com destinations return HTTP 200 with their final
  canonical metadata before changing Medium.
- Using the signed-in author account, edit each of the nine Medium stories and
  set “This story was originally published elsewhere” to its exact
  TalPerry.com URL. Medium documents this as the supported author-controlled
  canonical mechanism:
  <https://help.medium.com/hc/en-us/articles/360033930293-Set-a-canonical-link>.
- Republish each Medium settings change, then verify from unauthenticated page
  source that Medium's canonical tag resolves to the intended TalPerry.com URL.
  Do not delete the Medium stories or make them unlisted.
- In Google Search Console, submit or refresh
  `https://talperry.com/sitemap.xml` and request indexing for all nine
  TalPerry.com URLs. If the account lacks access or Google's request quota is
  reached, leave the sitemap submitted and report the exact remaining manual
  actions.
- Do not create TalPerry.com aliases for Medium paths: the repository cannot
  issue redirects from `medium.com`, and Medium's canonical setting is the
  strongest supported migration signal short of a source-host 301.

## Test Plan

- Add a parameterized test for the six imported slug, timestamp, title,
  provenance, and canonical records.
- Verify all pages render, attribution is unlinked, images return valid image
  content types, local cross-links resolve, and no tracking pixels, unsupported
  iframes, defunct LightTag links, or unresolved Medium-media URLs remain.
- Assert the response and three duplicate stories do not receive new Medium
  bundles.
- Verify all eight animations retain multiple frames and every imported WebP
  uses Git LFS.
- Confirm existing LightTag attribution and the three existing destination
  canonicals remain unchanged.
- Validate sitemap inclusion, archive discovery, self-canonical URLs, Open Graph
  URLs, robots metadata, and BlogPosting structured data for all nine
  destinations.
- Visually inspect media-heavy, animation-heavy, code-heavy, long-title, and
  no-hero pages on desktop and mobile.
- Run pre-commit/Vale checks, `hugo --minify`, `make validate`, the complete
  Playwright suite, and the remote deployment workflows.

## Assumptions

- The migration is English-only and includes no factual modernization or
  retrospective warnings.
- Canonical tags are search-engine hints, not guaranteed ranking transfers;
  search engines may take time to consolidate signals.
- Medium and Search Console changes proceed only through Tal's authenticated
  accounts and stop cleanly for any story or property where permissions are
  unavailable.
- Preserve the current unrelated changes in `AGENTS.md`, `Makefile`,
  `README.md`, `docs/plans/4_restore_lighttag_redirects.md`, and `infra/`.
