# Visual review: Tal Perry

Date: 2026-08-30

This review proposes a direction rather than changing the live Hugo theme. The
working idea is **precision with mischief**: an editorial, nearly flat interface
with a compact fragment of the existing letter artwork as a signature.

The screenshots were captured from the local development server, which includes
drafts. Draft entries therefore appear in some current-state images.

## Executive assessment

The current site contains the right raw material but gives every element nearly
the same visual treatment. The illustrated name, intro, archive, post cards,
tags, and article chrome all compete instead of forming a hierarchy. The result
feels like a pleasant theme applied to a corpus, rather than a specific person
with a point of view.

The proposed direction makes three changes:

1. Give the homepage a clear thesis about Tal and curate the writing shown there.
2. Organize the full corpus by the questions behind it, with chronology as the
   secondary structure.
3. Replace rounded cards and soft shadows with typography, rules, spacing, and a
   few playful marks.

## Alternative V2: cool and compact

The second prototype keeps the information architecture but responds to the
first direction feeling too warm, too large, and too scroll-heavy.

- A cool gray technical canvas replaces the cream paper background.
- Familjen Grotesk replaces the large editorial serif treatment.
- The homepage hero drops from roughly half a page to 300px on desktop.
- The featured article image becomes a thumbnail rather than a dominant panel.
- Recent writing and the four editorial threads sit side by side.
- The complete desktop homepage fits inside one 1440 × 1000 viewport.
- The mobile first viewport reaches through the current focus and recent-writing
  list instead of ending inside the biography.
- Article and archive openings retain hierarchy while exposing useful content
  much sooner.

This version uses a faint blueprint grid, cobalt navigation cues, and a small
mint status rule for playfulness. It avoids both warm editorial luxury and a
generic software-dashboard card language.

## Problems and possible solutions

| Problem | Effect | Possible solution |
| --- | --- | --- |
| The eight-tile name is the strongest element on every page. | The brand overwhelms the writing, consumes horizontal space, and wraps awkwardly on mobile. | Keep three `TAL` tiles as a compact signature, then set “Tal Perry” as quiet text. The letter artwork remains memorable without becoming the entire interface. |
| The homepage is also the archive. | A reader meets every post at once and has no sense of what is important now. | Show one featured field note and three recent pieces. Move the complete corpus to Writing. |
| The homepage hero has an empty second column. | The first screen feels unfinished and undersells Tal’s perspective. | Use a full-scale thesis in the main column and a short personal note/current focus in the second. |
| Navigation reflects page types, not reader intent. | Home, Archive, About, and Contact are generic and do not reveal the site's substance. Contact also duplicates the footer. | Use Writing, Projects, and About. Let the logo provide Home and put direct contact links in the footer/About page. |
| The archive is an undifferentiated card grid. | Thirty-plus essays are hard to scan, old and new work look equally important, and subject clusters are hidden. | Add four editorial threads, topic filters, optional search, year groupings, and compact title-first rows. |
| Cards depend on inconsistent cover availability. | Posts without covers look incomplete; posts with covers carry very different visual weight. | Use images only for a selected feature and small optional thumbnails. A missing thumbnail should not change row geometry. Define a restrained topic-based fallback for article heroes. |
| Titles, summaries, tags, images, and dates compete inside every card. | The grid becomes visually noisy and long titles are truncated before their idea lands. | Make the title the primary scan target. Move topic/date to small monospaced metadata and remove summaries from catalog rows. |
| The serif/sans pairing and blue pill tags feel theme-like. | The presentation is friendly but not especially personal or contemporary. | Pair a distinctive editorial face (Instrument Serif in the prototype) with a technical, humane sans/mono family (IBM Plex). Use cobalt, vermilion, and acid yellow only as annotations. |
| Rounded panels and shadows appear almost everywhere. | The site feels soft and component-heavy rather than sleek. | Remove most container backgrounds, radii, and shadows. Use the paper background, generous space, and one-pixel rules to create structure. |
| Article pages sit inside a large rounded card. | Reading feels nested inside UI chrome, and the TOC visually competes with the prose. | Let the article live directly on the page. Give its opening a consistent label/title/dek/meta/hero sequence and reduce the TOC to a quiet rail. |
| Hero rules are implicit and depend on content assets. | Home, lists, articles, and utility pages do not feel like variants of one system. | Define explicit hero types: home thesis, collection title/dek/tools, article label/title/dek/meta/media, and utility title/purpose. |
| Mobile spends most of its first screen on a wrapped brand and navigation. | Readers do not reach the site's proposition in the first viewport. | Keep a single 68px header row, hide secondary navigation, and make the proposition the dominant mobile element. |
| The current archive taxonomy mostly leaks folder history. | “genai,” “lighttag,” and “classics” describe provenance better than the reader’s question. | Curate stable reader-facing threads such as Agents & AI, ML Systems, Building, and Life & Learning; preserve technical tags for search/filtering. |

## Proposed information architecture

- **Home** via the logo
  - Point-of-view hero
  - One featured field note
  - Three recent pieces
  - Browse by question
- **Writing**
  - Topic/thread filters
  - Search
  - Chronological groups
- **Projects**
  - LightTag and current experiments as a small portfolio, not hidden among posts
- **About**
  - Short biography, current focus, selected history, contact links
- **Language**
  - Compact control in the header; keep each page on its translated equivalent

## Consistent hero system

| Page role | Required elements | Media behavior |
| --- | --- | --- |
| Home | Identity kicker, one-sentence thesis, short personal/current note | No required hero image; the typography is the hero. |
| Writing/collection | Descriptive title, one short dek, filters/search | No decorative image. |
| Article | Thread label, full title, dek, author/date/read time | Use authored cover when present; otherwise use a quiet topic-color field or typographic fallback. |
| About/project | Title, concise purpose, key facts | Optional portrait/project image with a fixed aspect ratio. |
| Contact/utility | Title and direct action | No media. |

## Screenshot index

All pairs use matching viewports. Desktop is approximately 1440 × 1000; mobile
is approximately 390 × 844.

| View | Before | Proposed direction |
| --- | --- | --- |
| Homepage, desktop | [before/home-desktop.jpg](images/before/home-desktop.jpg) | [after/home-desktop.jpg](images/after/home-desktop.jpg) |
| Writing archive, desktop | [before/archive-desktop.jpg](images/before/archive-desktop.jpg) | [after/archive-desktop.jpg](images/after/archive-desktop.jpg) |
| Article opening, desktop | [before/article-desktop.jpg](images/before/article-desktop.jpg) | [after/article-desktop.jpg](images/after/article-desktop.jpg) |
| Homepage, mobile | [before/home-mobile.jpg](images/before/home-mobile.jpg) | [after/home-mobile.jpg](images/after/home-mobile.jpg) |

### Alternative V2 screenshots

| View | Cool, compact direction |
| --- | --- |
| Homepage, desktop | [alternative-cool-compact/home-desktop.jpg](images/alternative-cool-compact/home-desktop.jpg) |
| Writing archive, desktop | [alternative-cool-compact/archive-desktop.jpg](images/alternative-cool-compact/archive-desktop.jpg) |
| Article opening, desktop | [alternative-cool-compact/article-desktop.jpg](images/alternative-cool-compact/article-desktop.jpg) |
| Homepage, mobile | [alternative-cool-compact/home-mobile.jpg](images/alternative-cool-compact/home-mobile.jpg) |

## Prototype

The first standalone HTML/CSS prototype is in [`prototype/`](prototype/), and
the cool, compact alternative is in [`prototype-v2/`](prototype-v2/). They are
visual specifications, not production Hugo code. Links and filter controls are
illustrative. Both deliberately reuse current post artwork and the existing
letter assets instead of inventing a second identity.

## Suggested implementation order

1. Establish typography, color, spacing, header, and footer tokens.
2. Build the compact identity and responsive navigation.
3. Add curated homepage data and the question/thread taxonomy.
4. Replace the archive card grid with the filterable title-first list.
5. Implement the explicit hero variants and article reading layout.
6. Audit English, German, Hebrew, RTL, missing-cover, and long-title cases.
7. Run the existing Hugo and Playwright checks, then add screenshot assertions
   for the new header and hero variants.
