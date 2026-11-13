# Web Interface Guidelines — Source Audit (Phase 0 baseline)

Diagnostic only. No source modified. Rules from the Vercel/Web Interface Guidelines
checklist (fetched 2026-11-13). Findings are `file:line — rule — issue — fix`.
Scope: `app.py`, `layout.py`, `figuras.py`, `i18n.py`, `conteudo.py`,
`assets/style.css`, `assets/fonts.css`, `assets/a11y_dropdown.js`, `assets/icons/`.

Context accounted for: a prior a11y pass already landed (focus ring unified, `.seg`
44×44, landmarks, ORCID SVG, dropdown aria-hidden-focus shim, level glyphs). CSP is
Report-Only by design (not re-litigated). Self-hosted fonts by design.

Legend: [OK] compliant / observed good · [!] finding · [~] partial.

---

## Accessibility

- [OK] `layout.py:489` — Skip link — `html.A(tr(lang,"skip"), href="#conteudo", className="skip-link")` present and styled (`style.css:299`), targets `<main id="conteudo">`.
- [OK] `layout.py:131-133` — Icon-only buttons have labels — theme `☀/🖥/☾` buttons carry `title`+`aria-label` via `_seg()` (`layout.py:92-94`).
- [OK] `figuras.py:198`, `layout.py:41,140,170` — Decorative icons hidden — level `.glifo` spans all carry `aria-hidden="true"`.
- [OK] `layout.py:437,440` — Form controls labelled — both dropdowns preceded by `html.Label`.
- [OK] `layout.py:51-52` — Stacked bar has text alt — `role="img"` + computed `aria-label` listing counts per level.
- [OK] Heading hierarchy — single `<h1>` in hero (`layout.py:380`); sections use `<h2>`, cards/decls `<h3>`. No skipped levels observed.
- [!] `layout.py:316-324` / `app.py:316-324` — Async updates need `aria-live` — selecting a city (dropdown or map click) swaps `#cartao`, `#detalhe`, `#horizontes` with no live region; a screen-reader user gets no announcement that the forecast card changed. Add `aria-live="polite"` to the `#cartao` container (and/or a visually-hidden status node) so the new city + value is announced.
- [!] `layout.py:444` — Map is canvas-only for AT — `dcc.Graph` MapLibre/Plotly bubbles expose no semantic content; the only textual equivalent is Tabela 1 (`layout.py:158`, good) but it is not programmatically associated with the map as its alternative. Acceptable mitigation exists; consider `aria-describedby` from the figure to the ranking table.
- [~] `style.css:459` — Heading anchors `scroll-margin-top` — set for `.artigo-coluna section` only. Anchor targets outside the article (`#painel`, `#indicadores`, `#dados` wrapper, `#resumo` is inside) are not all covered, so the sticky 56px topbar can hide the top of `#painel` after a nav jump. Add `scroll-margin-top` to `#painel` and other nav targets.
- [OK] `assets/a11y_dropdown.js` — Semantic/keyboard remediation — promotes the real `<button>` to the tab stop and makes the aria-hidden shim inert; keyboard operation preserved (WCAG 4.1.2). Good.

## Focus

- [OK] `style.css:86` — Visible focus — global `:focus-visible { outline: 3px solid var(--green-ink); outline-offset:2px }`.
- [OK] `style.css:91-95` — No naked outline removal — embedded Plotly/Dash surfaces get the brand ring re-applied; `:focus:not(:focus-visible)` only suppresses the non-keyboard case. Uses `:focus-visible`, not bare `:focus`. Good.
- [!] `style.css:102,459` — Sticky header can cover focused anchor — `.topbar` is `position:sticky; top:0` (56px). Tab-focusing an in-article element near a section top, or a hash jump, can land under the bar everywhere `scroll-margin-top` is not set (see Accessibility `~`).
- [OK] No `outline:none` without replacement found.

## Forms

- [OK] `layout.py:437-443` — Both selects (`dd-uf`, `dd-cidade`) are labelled and `clearable=False` (sensible default, prevents empty state).
- [OK] `i18n.py:218` — Placeholder ends with `…` — `"Selecione…"` uses the real ellipsis character.
- [!] `i18n.py:218` — Placeholder lacks an example pattern — guideline wants placeholders to show an example ("e.g. Curitiba"), not just an instruction. Minor.
- [~] Inputs lack `autocomplete`/`inputmode`/`name` — these are Dash `dcc.Dropdown` comboboxes, not free-text inputs, so most input rules are n/a. No paste-blocking, no `type` misuse. Acceptable.
- [OK] No destructive form actions; read-only app, nothing to guard with `beforeunload`.

## Animation

- [OK] `style.css:68-70,119,290-296` — `prefers-reduced-motion` respected — body transition, `.seg` transition, and the `.enter`/`.stats .stat` entrance are all gated behind `@media (prefers-reduced-motion: no-preference)`.
- [OK] `style.css:291-295` — Only `transform`+`opacity` animated in the `rise` keyframe.
- [!] `style.css:69` — Non-compositor property animated — `body { transition: background-color .25s, color .25s }` animates `color`/`background-color` on theme switch (paint, not composite). Low cost here (one-shot on theme toggle) but technically off the transform/opacity rule.
- [!] `style.css:291-295` — Identical entrance on multiple blocks — `.enter` (the `#painel` section) and every `.stats .stat` use the same `translateY(10px)+opacity` "rise". The guideline and the craft floor both flag one identical entrance reused as decoration rather than one authored moment. (= A16.)
- [OK] No `transition: all` anywhere. No autoplaying media.

## Keyboard / Touch

- [OK] `style.css:117` — `.seg` buttons are `min-width/height:44px` (AAA target). Theme/lang controls meet 44×44.
- [!] `style.css` (global) — `touch-action: manipulation` not set — no element opts out of the 300ms tap delay / double-tap-zoom on the interactive controls, nav, or CTAs. Add to buttons/links.
- [!] `style.css` (global) — `-webkit-tap-highlight-color` never set deliberately — taps on `.btn`, `.seg`, `.nav-a`, dropdowns show the default grey flash on iOS. Set it (e.g. `transparent` + a real `:active`).
- [!] `style.css:222,508,354` — `overscroll-behavior: contain` missing on scroll regions — `.tbl-wrap` (horizontal), `.bibtex` (horizontal), and the nav-mobile popover can chain scroll to the page. Add `overscroll-behavior` to these.
- [~] Touch targets outside `.seg` — nav-desktop `.nav-a` (`style.css:313`), `.toc a` (`style.css:463`), footer links, and the ORCID logo link (`style.css:471-472`, ~16px) are below 44×44. (= A3; `.seg` resolved, these not.)

## Typography

- [OK] `style.css:75` + `.tabular` usages — `font-variant-numeric: tabular-nums` applied to the stat/card/horizon number columns and the ranking table.
- [!] `style.css:126-127,350,468,480` — No `text-wrap: balance`/`pretty` on headings — h1, `.sec-titulo`, `.artigo-titulo` can leave orphans/ragged breaks. Add `text-wrap: balance` to display headings.
- [~] `i18n.py` / `conteudo.py` — Curly quotes / ellipsis — ellipsis character `…` used in placeholders (good), but prose strings should be spot-checked for straight vs. curly quotes (not exhaustively verified here).
- [!] Non-breaking spaces in units — values like "15.389 casos", "94–98%", "CC BY 4.0", "SE 32" use regular spaces and can wrap awkwardly. Use NBSP between number and unit/label.

## Content / Localization

- [!] `layout.py:406,410` — Hardcoded number formats, not locale-aware — the KPI tiles hardcode `"913 "`, `" 15.389"` and `"1,16"` (PT grouping/decimal) in all three languages. In EN "15.389" reads as 15.389 (a decimal), and "1,16" reads as 1,160. The data-driven numbers go through locale-aware `fmt_int` (`i18n.py:465`, good), but these literals bypass it. (= A1.)
- [!] `figuras.py:78` — Hardcoded map hover number — `hover_estado` uses `%{customdata[1]:.0f}` with no thousand separator (the mapa figure sets no Plotly `separators`), so a state total renders as e.g. `15389`. Route through a locale separator (the detalhe figure sets `separators` at `figuras.py:144`; the mapa figure does not).
- [!] `figuras.py:88,195-196` / `i18n.py:240-241` — Unformatted ints in templates — `card_casos`/`card_intervalo`/`hover_cidade` receive raw `int(...)` and the `"{v} casos"` template adds no grouping, so large counts print ungrouped. Pass `fmt_int(...)` values. (= A1, `cartao_info` int() unformatted.)
- [!] `figuras.py:163`, `layout.py:47-48` — Hardcoded date format — `strftime("%d/%m")` / `"%d/%m/%Y")` forces day/month ordering in EN/ES too. Use a locale-aware formatter (guideline: dates via `Intl.DateTimeFormat`; here a per-language Python formatter). (= A1.)
- [!] `conteudo.py:24-25` — `ESTUDO` dict holds PT-formatted literals (`"15.389"`, `"1,16"`, `"7.883"`) — currently unused in rendering, but a latent locale trap if wired in.
- [!] `layout.py` / `i18n.py` — `translate="no"` missing on identifiers — brand name, BibTeX block (`layout.py:354`), DOIs (`layout.py:217`), and code-like tokens are not marked `translate="no"`, so browser auto-translation can mangle them.
- [OK] `app.py:182-186`, `layout.py:487` — Language from `Accept-Language`, not IP — `serve_layout` reads the header, `resolver()` falls back to EN, `<html lang>` synced clientside. Good.
- [OK] Copy is second-person / active and specific; CTAs name actions ("Ver painel", "Como citar").

## Performance

- [OK] `app.py:59` — `Compress(server)` (gzip/brotli) on responses.
- [OK] `app.py:137-141` — Cache-Control: versioned static assets `immutable` 1 year; HTML/callbacks `no-cache`. Good.
- [OK] `assets/fonts.css` — `font-display: swap` on every `@font-face`; latin subset `unicode-range`.
- [!] `app.py` `<head>` — Critical fonts not preloaded — no `<link rel="preload" as="font" ... crossorigin>` for the above-the-fold Inter weight(s). Self-hosted, so `preconnect` is n/a, but a preload of the hero font would cut the swap flash. (Relates to A13.)
- [~] `assets/fonts/` — 3 families / 9 files / ~352 KiB — over a lean budget for a single-view panel; Inter 400/500/600/700 + Source Serif 4 400/400-italic/600 + IBM Plex Mono 400/500. (= A13.)
- [!] `app.py:62-80` — No static shell / skeleton — `index_string` body is only `{%app_entry%}`; on a Render free-tier cold start the user sees Dash's bare "Loading…" with no branded skeleton. (= A4.)
- [OK] `figuras.py` — Theme change recolors the map via `Patch` (`app.py:228-245`) instead of re-sending the ~128 KB geojson. Good perf discipline.
- [OK] `layout.py:444,451` — `dcc.Graph` images not applicable; no large unvirtualized `.map()` of DOM nodes (ranking capped at 8 rows).

## Images

- [~] `layout.py:193` — ORCID `<img>` has no `width`/`height` attributes — sizing is CSS-only (`.orcid-id` 16px, `style.css:472`), so there is a brief pre-CSS reflow risk. `alt=""` is correct (link carries `aria-label`). Add explicit `width="16" height="16"`.
- [OK] No below-fold raster images needing `loading="lazy"`; the only asset is the inline-ish ORCID SVG.

## Navigation & State

- [OK] `layout.py:113,272` — All nav/links are real `<a href>` (Cmd/Ctrl+click and middle-click work).
- [!] `app.py` / `layout.py:503` — State not deep-linkable — selected UF, city, language, and theme live in `dcc.Store`/localStorage, never in the URL query string, so a selection cannot be shared or restored via link. (= A15.)
- [OK] No destructive actions to confirm (read-only app).

## Dark Mode & Theming

- [OK] `style.css:39,57` — `color-scheme: light`/`dark` declared on `:root`.
- [!] `app.py` meta_tags — `<meta name="theme-color">` missing — only `color-scheme` is set; mobile browser chrome won't match the dark brand background. Add theme-color (ideally per light/dark via media). (= A6.)
- [~] `style.css:238-253` — Dash dropdown given explicit `background`/`color` via tokens (good). Native `<select>` is not used, so that specific rule is n/a.
- [!] `style.css` (global) — Unthemed browser surfaces — no `::selection`, `caret-color`, `accent-color`, or `scrollbar-color` rules anywhere; text selection, the caret in the dropdown search, and scrollbars on `.tbl-wrap`/`.bibtex` render with browser defaults. Focus ring IS themed (resolved). (= A14.)

## Hydration / Misc

- [OK] `app.py:62-80` — Theme applied pre-paint by inline `<head>` script (no FOUC); server renders `<html lang="pt">` and client syncs — a controlled, intentional mismatch, not an accidental hydration bug.
- [OK] `app.py:38-39` — Viewport does NOT disable zoom (no `user-scalable=no` / `maximum-scale`); `viewport-fit=cover` set. Good (anti-pattern avoided).
- [!] `style.css` — Full-bleed surfaces don't use `env(safe-area-inset-*)` — hero, topbar, running-header, and footer are full-bleed with `viewport-fit=cover`, so on notched phones in landscape content can sit under the inset. Pad with `env(safe-area-inset-*)`.

---

## Summary counts (this checklist)

- Findings `[!]`: 23
- Partial `[~]`: 7
- Confirmed-good `[OK]`: 24

Heaviest clusters: Localization/number-date formatting (A1, 5 findings), mobile/touch
hardening (touch-action, tap-highlight, overscroll, safe-area), and unthemed browser
surfaces + theme-color (A6/A14). Strong areas: focus handling, reduced-motion,
Accept-Language i18n, cache/compression, and the map `Patch` perf pattern.
