# Impeccable Audit + Critique — Source Audit (Phase 0 baseline)

⚠️ DEGRADED: single-context (diagnostic subagent; not permitted to spawn the two
isolated A/B sub-agents, and the running app is owned by another agent so no browser
overlay). Method: design review + mechanical detector (Assessment B CLI ran; browser
visualization skipped — waiver below).

Surface **mode: Operate / Read** — an interactive epidemiological panel embedded in a
scientific-article shell (JBCS). Success = the visitor reads a forecast and understands
the method. Ambition shows as precision and restraint, not expression.

No source modified. Detector run: `impeccable detect --json assets/` against
`assets/style.css` + `assets/fonts.css` (CSS-only; the detector does not parse the
Python templates, so markup-level findings are reasoned from source).

---

## Assessment B — Deterministic detector (ran)

`node .../impeccable/cli/bin/cli.js detect --json assets/` → **6 findings**:

| # | antipattern | severity | file:line | snippet |
|---|---|---|---|---|
| 1 | overused-font | warning | `assets/fonts.css:4` | `font-family: 'Inter'` (400) |
| 2 | overused-font | warning | `assets/fonts.css:12` | `font-family: 'Inter'` (500) |
| 3 | overused-font | warning | `assets/fonts.css:20` | `font-family: 'Inter'` (600) |
| 4 | overused-font | warning | `assets/fonts.css:28` | `font-family: 'Inter'` (700) |
| 5 | side-tab | warning | `assets/style.css:215` | `.finding` `border-left: 4px solid var(--green)` |
| 6 | side-tab | warning | `assets/style.css:474` | `.resumo` `border-left: 3px solid var(--green)` |

Detector/skill agreement: both `side-tab` hits are the colored `border-left >1px`
craft-floor ban (= A9, confirmed open). `overused-font` (Inter) is a real slop signal,
but partially waived here: fonts are self-hosted by design and Inter pairs with Source
Serif 4 + IBM Plex Mono, which lifts it above a bare Inter-only AI default — still, Inter
is the single most AI-defaulted face and the identity would read as more authored on a
less-defaulted sans. Not a false positive; a known trade-off.

Not surfaced by the detector but found by review (markup not parsed): Unicode-glyph
icons, monospace-as-costume, the eyebrow ban, the hero-metric template, identical
entrance reuse — all below.

## Assessment B — Browser overlay (SKIPPED — waiver)

Live overlay and screenshots at ship sizes were **not run**: the app's single instance on
:8050 is owned by another agent and this audit is static/source-based per the task. No
reliable user-visible overlay is available. This is a documented waiver, not a clean pass.
Rendered-pixel checks (computed contrast ratios, real overflow at each breakpoint, focus
rings in situ) are therefore reasoned from source and should be re-verified in a running
instance during a later phase.

---

## Assessment A — Design review

### Design Health Score (Nielsen heuristics)

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 2 | City selection swaps the card with no `aria-live` and no visible "updating" state; Render cold start is a bare "Loading…" (A4). |
| 2 | Match System / Real World | 3 | Strong domain language (SE weeks, t+1…t+4, 90% interval); but EN/ES users see PT number/date formats (A1) and ◼/↗/☾ glyphs as icons. |
| 3 | User Control and Freedom | 3 | Dropdowns `clearable=False` (sane), map click = single flow; but no URL state to undo/share a selection (A15). |
| 4 | Consistency and Standards | 3 | Coherent token system, consistent pills/glyphs across legend/card/table. Minor: mono used both as data and as decoration (A8) blurs the "mono = measurement" rule. |
| 5 | Error Prevention | 3 | `_geo_valido` guards forged geo (good); constrained dropdowns. Little to get wrong in a read-only app. |
| 6 | Recognition Rather Than Recall | 3 | Legend + "como ler" steps + labelled controls aid recognition; Tabela 1 restates the map textually. Good. |
| 7 | Flexibility and Efficiency | 2 | No keyboard shortcuts, no deep links, no way to compare two cities; one rigid path. |
| 8 | Aesthetic and Minimalist Design | 2 | Chrome-heavy first screen (running header + brand + lang/theme bar before h1; A11), 4 eyebrows + 4 hero chips + 4 KPI tiles + hero situação card compete; eyebrow ban + hero-metric template present. |
| 9 | Error Recovery | n/a | Read-only panel with constrained inputs; no user-facing error/recovery surface exists to score (no forms, no submit, no destructive paths). |
| 10 | Help and Documentation | 3 | "Como ler o painel", figure captions, method cards, and a full article serve as inline help; no search, but task-appropriate. |
| **Total** | | **24/36** | **Acceptable (67%)** |

(9 heuristics scored; max 36. Band read off percentage per the guide: 67% = Acceptable,
upper edge.)

### Design Specificity Verdict

**Authored for this product, with generic scaffolding bolted on.** The genuinely specific
parts are strong: the two-layer map (teal choropleth deliberately off-hue from the
green→red alert bubbles so a green state + green bubble never reads as "all clear"), the
shape-coded alert glyphs (circle/triangle/diamond/octagon via `clip-path`) as a non-color
channel, the SE-week origin line on the detail chart, and the JBCS article shell are a
real point of view you could not lift onto an unrelated product. But the top of the page
is category-interchangeable dashboard furniture: an eyebrow over nearly every heading,
four inverse hero chips, and a four-up KPI row with one dark-filled tile — the exact
"hero-metric template" the craft floor names. The identity is in the data viz; the shell
around it is defaulted.

### Craft-floor check (bans + defaults)

- **[BAN] Eyebrow/kicker above a heading** — `style.css:77` `.eyebrow` (+ `--inverse`,
  `--alarm`) used on the hero, every numbered section (`layout.py:232,317,336`), the
  situação card (`layout.py:47`), the panel head (`layout.py:420`), and "como ler"
  (`layout.py:462`). The craft floor marks this a ban no brief earns back. (= A7.) **P2.**
- **[BAN] Colored `border-left >1px`** — `.finding` 4px (`style.css:215`), `.finding.warn`
  (`:217`), `.resumo` 3px (`style.css:474`). Detector-confirmed. (= A9.) **P2.**
- **[BAN] Unicode glyphs standing in for an icon system** — theme `☀ 🖥 ☾`
  (`layout.py:131-133`), external-link `↗` (`layout.py:272`), city-scope `◼`
  (`app.py:257`), stat arrow `→` (`layout.py:406`), pipeline `→` (`style.css:487`), aviso
  `⚠`/`ℹ` (`layout.py:89,400`). No drawn icon set; mixed emoji + geometric glyphs. (= A12.)
  **P2.**
- **[default→ban here] Monospace as a costume for "technical"** — IBM Plex Mono on the
  running header (`style.css:304`), article discipline/licence/meta lines
  (`style.css:467`), the `t+1 · 01/11` horizon labels + IC (`figuras.py:163,165`),
  recency badge (`layout.py:424`), footer notice (`layout.py:480`). Some of this is real
  measurement (IC ranges, SE labels — legitimate), but the running header, article meta,
  and footer notice are decoration. (= A8.) **P2/P3.**
- **[default] Hero-metric template** — `.stats` four tiles via `stat()` (`layout.py:405-410`,
  `style.css:140-147`), one `stat--brand` dark-filled (`layout.py:408`). Big-number +
  small-label + accent is the named template. The dark fill marks the "−14%" good-news
  tile, so there is weak semantic intent, but four identical cards with one inverted is
  the default container, not a decision. (= A10.) **P2.**
- **[default] Same-size icon+heading+text cards as page structure** — `.card`/`.card-etapa`
  grids (method, future-work, findings). Legitimate for a method summary, but it is the
  lazy container pattern repeated four times. **P3.**
- **[VERIFY] Depth** — `--shadow` (`style.css:36`) has offset + soft blur (good, not a
  zero-offset halo). `.brand-dot` uses a `0 0 0 4px` ring as an intentional status dot,
  not card depth — acceptable.
- **[VERIFY] Motion** — one keyframe (`rise`) reused on `#painel` and every stat tile
  (`style.css:291-295`); the floor wants one authored moment, not one identical entrance
  repeated. (= A16.) **P3.**
- **[VERIFY] Browser surfaces** — `::selection`, caret, scrollbar NOT themed; focus ring
  IS (resolved). The floor calls this the cheapest "built vs assembled" tell. (= A14.) **P3.**
- **[OK] Gradient text** — none. **[OK] Glass/blur decoration** — none. **[OK] Hard offset
  shadows** — none. **[OK] System display face** — self-hosted faces, not platform sans.

### Cognitive load

5 of 8 checklist items pass. Failures: **Visual hierarchy** (eyebrow+chips+KPIs+situação
all shout on the first screen — the "visual noise floor"), **Minimal choices** (hero
offers 4 chips + 3 CTAs + lang×3 + theme×3 = many simultaneous controls above the fold),
and **Single focus** on mobile (chrome pushes the h1 and the situação card below the fold —
A11). Intrinsic load (forecasts, intervals) is handled well with scaffolding (legend,
"como ler", captions). → **moderate, address soon.**

### Emotional journey

Peak is the interactive map + detail card (the reason to visit) — well composed, but it
sits *below* a dense indicators/KPI band on mobile, so the first scroll is chrome and
stats, not the payoff. End (footer/citation) is calm and credible. Reassurance at the
high-stakes moment (an alarming forecast) is good: shape glyph + label + interval, never
color alone.

### Priority issues

- **[P1] First screen spends itself on chrome, not the forecast.** Running header + brand
  bar + lang/theme segmented controls + eyebrow + 4 chips all precede the h1, and on
  mobile the situação card and the map fall below the fold (A11). *Why:* the panel's whole
  value is the forecast; the visitor scrolls past furniture to reach it. *Fix:* collapse
  the running header on mobile, demote chips/eyebrow, pull the situação summary or a map
  entry higher. *Command:* `/impeccable layout` (then `distill`).
- **[P1] Locale correctness is broken for EN/ES numbers and dates.** Hardcoded `"15.389"`,
  `"1,16"` KPI literals (`layout.py:406,410`), `%{:.0f}` map hover (`figuras.py:78`),
  unformatted `int()` in card/hover templates, and `strftime("%d/%m")` (A1). *Why:* a
  trilingual scientific panel showing "1,16" to an English reader (= 1,160) or "15.389"
  (= 15.389) is a credibility bug in the core data. *Fix:* route every displayed number
  through `fmt_int`/a locale date formatter; set Plotly `separators` on the map figure.
  *Command:* `/impeccable harden`.
- **[P2] Craft-floor bans cluster at the top of the page.** Eyebrow ban (A7), colored
  border-left (A9), Unicode-glyph icons (A12), mono-as-decoration (A8), hero-metric
  template (A10). *Why:* together they make an otherwise authored page read as generated
  dashboard scaffolding. *Fix:* delete eyebrows (let headings carry weight), drop or
  ≤1px the left borders, adopt one drawn icon set, reserve mono for data. *Command:*
  `/impeccable polish`.
- **[P2] No deep-linkable / shareable state.** UF, city, language, theme never touch the
  URL (A15). *Why:* a public forecast panel whose selections cannot be linked loses its
  most natural sharing path (email a city's forecast). *Fix:* sync `sel`/`dd-uf`/`lang`
  to query string via `dcc.Location`. *Command:* `/impeccable harden`.
- **[P2] Unthemed browser surfaces + missing theme-color.** `::selection`, caret,
  scrollbar unthemed (A14); no `<meta name="theme-color">` (A6). *Why:* the dark theme
  leaks default-blue selection and light mobile chrome, breaking the green-earthy world.
  *Fix:* add the four surface rules + theme-color per scheme. *Command:* `/impeccable polish`.

### Persona red flags

- **Sam (accessibility):** level meaning is NOT color-alone (glyph+label — resolved, good);
  dropdown keyboard preserved via `a11y_dropdown.js` (good); BUT city-selection card
  updates are silent to a screen reader (no `aria-live`), and the map canvas is
  AT-opaque with only a loosely-associated Tabela 1 fallback. Map has no WebGL-failure
  fallback (A5) — if MapLibre fails, Sam (and everyone) loses the primary figure with no
  graceful substitute beyond the always-present ranking table.
- **Casey (distracted mobile):** primary payoff (map/detail) is below a tall chrome+KPI
  stack (A11); no state persistence in URL so an interrupted visit can't be resumed by
  link (A15); 352 KiB of fonts + MapLibre on a cold Render free-tier dyno behind a bare
  "Loading…" (A4) on a slow connection. Touch targets for nav/TOC/ORCID below 44px (A3).
- **Jordan (first-timer):** well served — "como ler o painel" steps, labelled controls,
  captions, plain-language method cards. Main risk: `☀/🖥/☾` theme glyphs and `◼` scope
  marker are unlabelled-by-shape icons (the aria-labels help AT, but a sighted first-timer
  still decodes glyphs).

### What's working

1. The two-layer map hue strategy (teal choropleth vs green→red bubbles) is a genuine,
   defensible design decision that prevents a specific misread.
2. Shape-coded alert glyphs + label + interval everywhere a level appears — color is never
   the only channel. Textbook non-color encoding.
3. Disciplined perf/theme engineering: `Patch`-based map recolor (no 128 KB re-send),
   pre-paint theme script (no FOUC), versioned-immutable caching, reduced-motion gating.

### Minor observations

- `.cards-2` has duplicate identical rules at 980px (`style.css:521-525`) — dead CSS.
- ORCID `<img>` lacks intrinsic `width`/`height` (CSS-only sizing).
- Placeholder "Selecione…" has the ellipsis but no example city.

### Questions to consider

- What if the first viewport opened on the map + one headline number, and the chrome
  (chips, eyebrows, KPI row) came after?
- Does a trilingual scientific panel earn *three* decorative mono contexts, or should mono
  mean "this is a measured value" and nothing else?
- If MapLibre/WebGL fails on a locked-down browser, what does the visitor see — and is the
  ranking table enough to stand in?

---

Questions skipped: diagnostic/non-interactive subagent run; findings delivered to the
caller rather than an interactive action-planning dialogue (5 Priority Issues recorded
above for a later `/impeccable polish` / `harden` / `layout` pass).
