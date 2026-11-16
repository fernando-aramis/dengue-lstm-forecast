# Findings A1–A16 — Status Against Current Branch (Phase 0 baseline)

Diagnostic only, source-based. Each item checked against the code as it stands on this
branch (post the prior a11y pass). Status: RESOLVED / PARTIAL / CONFIRMED (still open) / N/A.

| ID | Sev | Summary | Status | Evidence |
|----|-----|---------|--------|----------|
| A1 | P1 | Mixed number/date formats per language | **CONFIRMED** | `layout.py:406` hardcodes `"913 "`/`" 15.389"`, `:410` `"1,16"` (PT grouping/decimal in all langs); `figuras.py:78` map hover `%{customdata[1]:.0f}` (no separators on mapa fig); `figuras.py:88,195-196` + `i18n.py:240-241` pass raw `int()` to `"{v} casos"` (ungrouped); `figuras.py:163` & `layout.py:47-48` `strftime("%d/%m"/"%d/%m/%Y")`. `conteudo.py:24-25` `ESTUDO` holds PT literals (unused). Only `fmt_int` (`i18n.py:465`) is locale-aware, and the literals bypass it. |
| A2 | P1 | Alert level depends on color (same glyph) | **PARTIAL** | RESOLVED on HTML surfaces: `.glifo` distinct `clip-path` shapes circle/triangle/diamond/octagon (`style.css:406-410`) + label, in legend (`layout.py:140`), pills/card (`figuras.py:198`), Tabela 1 (`layout.py:170`), situação (`layout.py:41`). STILL OPEN on the map: Scattermap bubbles are color-only circles (`figuras.py:90-95`, `color=CORES_NIVEL[nv]`), no shape channel on the canvas. |
| A3 | P1 | Small touch targets (nav, TOC, footer, ORCID) | **PARTIAL** | RESOLVED: `.seg` lang/theme buttons `min-width/height:44px` (`style.css:117`). STILL OPEN: `.nav-a` desktop (`style.css:313`, no min size), `.toc a` (`style.css:463`, gap 4-6px), footer links (plain text), ORCID link ~16px (`style.css:471-472`); nav-mobile items 40px (`style.css:325`, <44). |
| A4 | P1 | Cold start shows only "Loading…" (no shell/skeleton) | **CONFIRMED** | `app.py:62-80` `index_string` body is `<body>{%app_entry%}<footer>…`; only the pre-paint theme script is injected. No branded shell/skeleton; Render free-tier cold start shows Dash's default loader. |
| A5 | P1 | Map has no fallback if WebGL fails | **CONFIRMED** (mitigated) | `figura_mapa` (`figuras.py:54-108`) builds Choroplethmap/Scattermap (MapLibre GL) with no `<noscript>`, no WebGL feature-detect, no still-image fallback. Partial mitigation: Tabela 1 (`layout.py:158`) always renders as a textual equivalent, but is not presented as the map's fallback nor programmatically linked. |
| A6 | P2 | Missing `<meta name="theme-color">` | **CONFIRMED** | `app.py:36-55` meta_tags = viewport + citation/DC/og only; no `theme-color`. `color-scheme` set in CSS (`style.css:39,57`) is a different control. |
| A7 | P2 | Eyebrows/kickers everywhere + hero chips | **CONFIRMED** | `.eyebrow` (`style.css:77`, +`--inverse`/`--alarm`) on hero (`layout.py:379`), every numbered section (`layout.py:232,308-333`), situação (`:47`), panel head (`:420`), declarações (`:336`), "como ler" (`:462`); `.chips` 4 inverse chips (`layout.py:374-378`). `.kicker` defined (`style.css:153`). Craft floor marks eyebrow a hard ban. |
| A8 | P2 | Monospace used as decoration | **CONFIRMED** (partly legit) | `.mono`/`--font-mono` on running header (`style.css:304`), article disc/lic/meta (`style.css:467`; `layout.py:295-300`), horizon `t+… · dd/mm` + IC (`figuras.py:163,165`), recency badge (`layout.py:424`), footer notice (`layout.py:480`), bibtex/doi (legit code). Decorative: running header, article meta, footer notice, recency badge. |
| A9 | P2 | Colored left border >1px on `.finding` + summary | **CONFIRMED** | `.finding` `border-left: 4px solid var(--green)` (`style.css:215`), `.finding.warn` terra (`:217`), `.resumo` `border-left: 3px solid var(--green)` (`:474`). Detector-confirmed (`side-tab`, 2 hits). |
| A10 | P2 | Hero-metric template: 4 KPI cards, one dark-filled | **CONFIRMED** (weak intent) | `.stats` 4 tiles via `stat()` (`layout.py:405-410`); `stat2` `tom="brand"` → `.stat--brand` dark fill (`style.css:392-394`) marks the "−14%" good-news tile (weak semantic reason). Big-number+label+accent four-up is the named template. |
| A11 | P2 | Mobile first screen wasted on chrome | **CONFIRMED** (partly improved) | `serve_layout` order (`layout.py:488-502`): skip-link → running-header → topbar(brand+nav+lang/theme) → `<main>` → hero h1. Mobile running header now 1 line (`rh-esq-curto`, `style.css:308-309`) — improved from 3 — but brand + segmented lang/theme bar still precede h1, and situação stacks below `hero-main` (`.hero-grid` single col until 980px, `style.css:401`) → below fold. |
| A12 | P2 | Unicode glyphs as icons | **CONFIRMED** | Theme `☀ 🖥 ☾` (`layout.py:131-133`; 🖥 monitor emoji, not ◼), link `↗` (`layout.py:272`), scope `◼` (`app.py:257`), KPI arrow `→` (`layout.py:406`), pipeline `→` (`style.css:487`), aviso `⚠`/`ℹ` (`layout.py:89,400`). No drawn icon library; ORCID is the lone real SVG. |
| A13 | P2 | Fonts over budget (3 families, 9 files, ~348 KiB) | **CONFIRMED** | `assets/fonts/` = 9 woff2, du ≈ 352 KiB: Inter 400/500/600/700, Source Serif 4 400/400-italic/600, IBM Plex Mono 400/500 (`fonts.css`). Detector flags Inter `overused-font` ×4. Self-hosting intentional; count/weight is the finding. No `rel=preload` for the critical weight. |
| A14 | P3 | Unthemed browser surfaces | **PARTIAL** | RESOLVED: focus ring unified + applied to embedded surfaces (`style.css:86,91-95`). STILL OPEN: no `::selection`, `caret-color`, `accent-color`, `scrollbar-color`, `text-underline-offset` in `style.css` (grep: 0 hits). |
| A15 | P3 | Selection state not in URL | **CONFIRMED** | State in `dcc.Store` (`layout.py:503-506`: `lang` localStorage, `theme`, `theme-eff`, `sel`); no `dcc.Location`, no query-string sync. UF/city/lang/theme not shareable/deep-linkable. |
| A16 | P3 | Identical entrance animation across blocks | **CONFIRMED** (narrow) | `style.css:291-295`: `.enter` and `.stats .stat` both `opacity:0; translateY(10px); animation: rise`. Scope narrower than "every block" — only `#painel` has `.enter` (`layout.py:417`) + 4 staggered stat tiles. Still the single reused entrance the craft floor flags. |

## Verdict tally

- RESOLVED (fully): 0
- PARTIAL (a11y pass closed part): 4 — A2, A3, A11, A14
- CONFIRMED (still open): 12 — A1, A4, A5, A6, A7, A8, A9, A10, A12, A13, A15, A16
- N/A: 0

The prior a11y pass genuinely moved A2, A3, A11, A14 to partial (shape glyphs on HTML
surfaces, 44px `.seg`, 1-line mobile running header, unified focus ring) but closed none
end-to-end — each keeps an open remainder (map bubbles color-only; nav/TOC/ORCID <44px;
chrome still above the h1; selection/caret/scrollbar unthemed).
