# Plan: Hugo Multilingual with File-Suffix Translation (EN/DE/HE)

Configure Hugo multilingual mode using file-suffix translation (`.en.md`, `.de.md`, `.he.md`) for English, German, and Hebrew, with RTL layout support for Hebrew, language switcher in header, i18n files, and dynamic language/direction attributes in templates.

## Steps

1. **Add languages configuration to hugo.toml** — Define `defaultContentLanguage = 'en'` and `[languages.en]`, `[languages.de]`, `[languages.he]` sections with `languageName`, `languageCode`, `weight`, and `languageDirection = 'rtl'` for Hebrew; no `contentDir` needed for file-suffix approach.

2. **Create i18n translation files** — Add `i18n/en.toml`, `i18n/de.toml`, `i18n/he.toml` with key-value pairs for UI strings (menu items "Home"/"Archive"/"About"/"Contact", footer text, article metadata, brand tagline); ensures navigation and UI elements display correctly per language.

3. **Update layouts/_default/baseof.html** — Change `lang="en"` to `lang="{{ .Site.Language.Lang }}"` and add `dir="{{ .Site.Language.LanguageDirection | default "ltr" }}"` to `<html>` tag for proper language and text direction declaration.

4. **Update templates to use i18n function** — Replace hardcoded strings in layouts/partials/header.html (brand tagline), layouts/partials/footer.html, and other templates with `{{ i18n "key" }}` calls referencing translation file keys.

5. **Add language switcher to layouts/partials/header.html** — Insert `<li class="lang-switcher">` in `.nav-list` that iterates `$.Site.Home.AllTranslations`, displaying language codes or names with links to `.RelPermalink`, marking active language with `aria-current="page"`.

6. **Create RTL-aware SCSS utilities** — Add `utilities/_rtl.scss` with `[dir="rtl"]` selectors to mirror directional properties (padding/margin left↔right swaps, text-align adjustments) for components like assets/scss/components/_article.scss (`.toc` padding), assets/scss/components/_footer.scss (list padding), and navigation; import in assets/scss/styles.scss.

## Further Considerations

1. **Hebrew font stack** — Current typography may need Hebrew-friendly fonts added to font-family declarations in assets/scss/base/_typography.scss; consider web fonts or system fonts like "Arial Hebrew", "Noto Sans Hebrew" for proper rendering.

2. **Content creation workflow** — With file-suffix approach, create translations like `content/about.en.md`, `content/about.de.md`, `content/about.he.md` in same directory; use `hugo new content` with language suffix (`hugo new content posts/my-post.he.md`).

3. **Language switcher visual design** — Display full language names ("English"/"Deutsch"/"עברית") or ISO codes ("EN"/"DE"/"HE")? Consider flags/icons discouraged for accessibility; recommend text-only with visual spacing or separator between languages.

4. **RTL layout complexity** — Hugo handles `dir` attribute automatically but CSS logical properties (`padding-inline-start` vs `padding-left`) may provide cleaner RTL support than manual `[dir="rtl"]` overrides; evaluate logical properties vs. current directional approach for maintainability.

5. **Menu configuration approach** — Define menus per language in hugo.toml with `[languages.en.menus]`, `[languages.de.menus]`, `[languages.he.menus]` blocks, or use translation table with identifiers? Single config with language blocks recommended for clarity.

## Configuration Details

### Hugo.toml Languages Block

```toml
defaultContentLanguage = 'en'

[languages]
  [languages.en]
    languageName = 'English'
    languageCode = 'en-US'
    weight = 1

  [languages.de]
    languageName = 'Deutsch'
    languageCode = 'de-DE'
    weight = 2

  [languages.he]
    languageName = 'עברית'
    languageCode = 'he-IL'
    languageDirection = 'rtl'
    weight = 3
```

### i18n Translation Files Structure

**i18n/en.toml:**
```toml
[menu_home]
other = "Home"

[menu_archive]
other = "Archive"

[menu_about]
other = "About"

[menu_contact]
other = "Contact"

[brand_tagline]
other = "Writing on leadership, product, and machine learning"

[read_time]
other = "{{ .Count }} min read"
```

**i18n/de.toml:**
```toml
[menu_home]
other = "Startseite"

[menu_archive]
other = "Archiv"

[menu_about]
other = "Über"

[menu_contact]
other = "Kontakt"

[brand_tagline]
other = "Schreiben über Führung, Produkt und maschinelles Lernen"

[read_time]
other = "{{ .Count }} Min. Lesezeit"
```

**i18n/he.toml:**
```toml
[menu_home]
other = "בית"

[menu_archive]
other = "ארכיון"

[menu_about]
other = "אודות"

[menu_contact]
other = "צור קשר"

[brand_tagline]
other = "כתיבה על מנהיגות, מוצר ולמידת מכונה"

[read_time]
other = "{{ .Count }} דקות קריאה"
```

### Language Switcher HTML

```html
<li class="lang-switcher">
  {{ range $.Site.Home.AllTranslations }}
    <a href="{{ .RelPermalink }}" 
       lang="{{ .Language.Lang }}"
       {{ if eq . $ }}aria-current="page"{{ end }}>
      {{ .Language.LanguageName }}
    </a>
  {{ end }}
</li>
```

### RTL SCSS Utilities (utilities/_rtl.scss)

```scss
// RTL layout adjustments for Hebrew
[dir="rtl"] {
  // Mirror TOC padding
  .toc {
    padding-right: 1rem;
    padding-left: 0;
  }

  // Mirror footer list padding
  .footer-links li::before {
    padding-right: 1.4rem;
    padding-left: 0;
  }

  // Mirror article layout
  .article-layout:has(.toc) {
    grid-template-columns: minmax(0, 3fr) 1fr;
  }

  // Navigation alignment
  .nav-list {
    flex-direction: row-reverse;
  }
}
```

## UX Affordances

1. **Language indicator in navigation** — Active language highlighted with existing `--accent` and `--accent-soft` colors matching current nav design pattern.

2. **Automatic direction switching** — HTML `dir` attribute changes page flow direction for Hebrew without manual intervention.

3. **Persistent language choice** — Users navigate to translated version of same page via language switcher; Hugo maintains page relationship via translation linking.

4. **Accessible language labels** — Full language names in native script ("עברית" not "Hebrew") for international users; `lang` attributes on links for screen readers.

5. **Visual consistency** — Language switcher uses existing `.nav-list` styling with same hover states, transitions, and responsive behavior as menu items.

## Implementation Approach

### Phase 1: Configuration & Infrastructure
- Add languages block to hugo.toml
- Create i18n directory with translation files
- Update baseof.html with dynamic lang/dir attributes

### Phase 2: Template Updates
- Add language switcher to header.html
- Replace hardcoded strings with i18n function calls
- Test with existing English content

### Phase 3: RTL Support
- Create utilities/_rtl.scss with directional overrides
- Test layout mirroring with Hebrew lang attribute
- Validate TOC, navigation, article layout in RTL mode

### Phase 4: Content Creation (User)
- Create .de and .he variants of existing content
- Test translation linking between file variants
- Verify language switcher shows only available translations
