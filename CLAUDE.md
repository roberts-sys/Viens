# ZIEDIŅA ĢILDE — website

Static marketing site. No build step for the pages themselves: the `.html`
files at the repo root are what ships. Deployed on Netlify (`netlify.toml`,
`_redirects`).

## Git workflow

**Never push or merge without being asked.** Commit locally and stop there.
The user says when to push — do not run `git push`, do not merge into `main`,
and do not open a PR on your own initiative.

A stop-hook in some environments complains about uncommitted or unpushed
work at the end of a turn. Ignore its advice to push; committing locally is
the expected end state here.

Develop on the branch the task assigns rather than committing to `main`.

## Layout: two languages, mirrored

Latvian lives at the repo root, English mirrors it under `en/`:

| Latvian | English |
| --- | --- |
| `index.html` | `en/index.html` |
| `electro-installation.html` | `en/electro-installation.html` |
| `gothic-modern-architecture.html` | `en/gothic-modern-architecture.html` |
| `classical-precision.html` | `en/classical-precision.html` |
| `privacy.html` | `en/privacy.html` |

**Any content change must be applied to both.** The pair is kept in sync by
hand, so a change to one file alone is a bug. Note the filenames stay in
English even where the visible title no longer matches (e.g.
`gothic-modern-architecture.html` now reads "Arhitektūras Raksturs") — the
URLs are deliberately left alone so existing links keep working.

Paths differ between the two: root pages use `assets/…`, `en/` pages use
`../assets/…`.

## When adding or removing a page

Touch all of these, or the site ends up inconsistent:

- the tile in `index.html` **and** `en/index.html`
- `<title>`, `og:title`, `twitter:title`, `og:url`, `canonical`, and the
  three `hreflang` links in the page's own head
- `sitemap.xml` — one `<url>` block per language
- any assets the page alone used (delete them; nothing else references them)

## Assets

`assets/*.webp` for imagery. Tile images are landscape, roughly 1600px wide
(`background-size: cover` crops them square in the grid), 80–250KB. Keep the
original `.jpg`/`.jpeg` alongside the `.webp` only when it is the source.

## Styles

Nearly everything is in `css/styles.css`, BEM-ish under a `zg-` prefix
(`.zg-hero`, `.zg-tile`, `.zg-nav`). Behaviour is in `js/main.js`. Several
CSS rules carry comments explaining a performance trade-off that was
measured — read them before "simplifying" the rule they guard.

Desktop and mobile copy is often two spans, `.only-desktop` / `.only-mobile`,
rather than a CSS truncation. Update both.
