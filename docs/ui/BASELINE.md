# BASELINE — Fase 0 (estado "antes")

**Projeto:** painel `dengue-lstm-forecast` (Dash 4.5 + Plotly 7.1, trilíngue PT/EN/ES, tema claro/escuro, casca de artigo JBCS).
**Branch:** `fix/a11y-ui-remediation` (após a pass de a11y já aplicada: regiões roláveis focáveis, landmarks, ORCID SVG, dropdown aria-hidden-focus, `.seg` 44×44, glifos de nível, foco unificado).
**Data:** 2026-11-13. **Escopo:** diagnóstico, **sem alterar código** da app.

Consolida dois levantamentos paralelos (agentes orquestrados):
- **Captura & Medição** (app rodando em :8050): matriz de 62 capturas + axe + Taste `perf`/`copy-lint` + sonda de overflow.
- **Audit de código** (estático, via skills `web-design-guidelines` e `impeccable` + detector Impeccable).

Saída bruta em [`docs/ui/raw/`](raw/) · capturas em [`docs/ui/shots/before/`](shots/before/) · exceções em [`waivers.md`](waivers.md).

---

## 1. Medições (números do "antes")

| Métrica | Resultado | Veredito |
|---|---|---|
| **axe-core** (360/1440 × claro/escuro, PT; wcag2a..22aa + best-practice) | **0 violações** em todos os estados; 1 *incomplete* `color-contrast` (11 nós — canvas Plotly/mapa, needs-review) | ✅ base limpa (a11y já corrigida) |
| **Overflow horizontal** (320/390/768/1024/1440) | **0 offenders** em toda largura, inclusive 320px | ✅ |
| **FCP** | 44 ms @1440 · 88 ms @390 (CPU-relativo) | ✅ PASS |
| **LCP** | 440 ms @1440 (h1) · 404 ms @390 | ✅ PASS |
| **CLS / layout shift** | **0,690 @1440 (FAIL)** · 0,146 @390 (WARN) | ❌ **acima do alvo <0,1** |
| **Transferência total** | ~2220 KiB @1440 | ⚠️ WARN |
| **JS** | 1735 KiB gz / 6065 KiB parseado / **15 arquivos (FAIL)** | ⚠️ inerente ao Dash/Plotly/MapLibre → [waiver](waivers.md) |
| **Fontes** | 3 famílias / **7 arquivos (FAIL)** / ~310 KiB; sem `preload` | ❌ ação (A13) |
| **CSS** | 11,4 KiB / 2 arquivos | ✅ |
| **Copy-lint** (PT+EN) | `em-dash` ×15 (orçamento 2), `eyebrows` ×10, `stat-strip` ×3 | ⚠️ estilo de artigo; em-dash é o item acionável |
| **Nielsen (Impeccable)** | **24/36 — "Aceitável" (67%)** | ⚠️ |

> **Estado "sem cobertura" é inalcançável** neste build (as 27 UF e 33 cidades têm previsão; geo inválido cai em São Paulo). As ramificações `card_prompt`/`sem_cob_cartao` são código morto defensivo. Capturado o fallback real mais próximo (escopo estadual, ex.: Acre → "UF-AC (estado)").

---

## 2. Achados consolidados por prioridade (formato `/impeccable audit`)

Severidade reflete o estado **atual** da branch (pós-a11y). `local · categoria · impacto · norma · recomendação · comando`.

### P0 — nenhum

### P1 — corrigir primeiro

| # | Local | Categoria | Impacto | Recomendação | Comando |
|---|---|---|---|---|---|
| **A1** | `layout.py:406,410`; `figuras.py:78,88,195-196`; `i18n.py:240-241`; `figuras.py:163`, `layout.py:47-48` | Localização | **Credibilidade do dado**: EN/ES veem "1,16" (=1,160) e "15.389" (=15.389) com formato pt-BR; `int()` sem agrupamento; datas `%d/%m` fixas; figura do **mapa** sem `separators` | Centralizar em `formato.py` (`fmt_int/fmt_dec/fmt_pct/fmt_data/fmt_intervalo`); rotear **todo** número/data exibido; `separators` por idioma no Plotly | `harden` |
| **CLS** | perf (mapa/plotly + `.enter` + img sem dimensões) | Performance | **0,690 FAIL** — salto de layout visível no carregamento | Reservar alturas de mapa/série; `width/height` no ORCID; revisar a animação de entrada que parte de `opacity:0`/`translateY` | `optimize` |
| **A11** | `layout.py:488-502`; `style.css:401` | Hierarquia/Operate | Primeira tela mobile é cromo (running header + marca + barras idioma/tema + eyebrow + 4 chips) — h1 e cartão **Situação** abaixo da dobra (confirmado em `390-light-pt-fold.png`) | Colapsar running header no mobile; idioma/tema no menu; ordem mobile h1 → lede → **Situação** → CTAs | `layout`→`distill` |
| **A4** | `app.py:62-80` (`index_string`) | Estado/Perf | Cold start do Render free mostra só "Loading…" (sem shell) por até ~50 s; robôs não veem conteúdo | Shell estático antes de `{%app_entry%}` (marca + título + esqueleto do painel + `<noscript>`); ocultar ao montar o React; sem CLS>0,1 | `clarify` |
| **A5** | `figuras.py:54-108` | Estado/Robustez | Se o WebGL falhar, a Figura 1 fica em branco sem aviso (a Tabela 1 existe mas não é apresentada como plano B) | Detectar falha de WebGL (clientside) e mostrar estado de erro ligando à Tabela 1 + seletores | `harden` |
| **A2** | `figuras.py:90-95` | Daltonismo | **PARCIAL**: superfícies HTML já têm forma+rótulo; bolhas do mapa ainda são círculos só-cor | Avaliar símbolo por nível no `Scattermap`; se não suportar, reforçar hover+Tabela 1 como alternativa e validar com simulação deuteranopia/protanopia | `harden` |
| **A3** | `style.css:313,463,325,471-472` | Toque (WCAG 2.5.8) | **PARCIAL**: `.seg` já 44px; `.nav-a`, `.toc a`, links de rodapé, ORCID (~16px) e nav-mobile (40px) ainda <44px | Padding (não fonte) p/ ≥24px desktop, ≥44px mobile; `scroll-margin-top` nos alvos de âncora | `harden` |
| **NEW-1** | `layout.py:316-324` (callback) | Acessibilidade | Trocar cidade recria `#cartao/#detalhe/#horizontes` **sem anúncio** — leitor de tela não sabe que mudou | `aria-live="polite"` no `#cartao` (ou nó de status visualmente oculto) com "Cidade: N casos, nível X" | `harden` |

### P2

| # | Local | Categoria | Impacto | Recomendação | Comando |
|---|---|---|---|---|---|
| **A7** | `style.css:77`; `layout.py:379,232,308-336,47,420,462,374-378` | Craft-floor (ban) | Eyebrow sobre quase todo título + 4 chips no hero → página parece scaffolding gerado | Remover eyebrows/kickers e chips; título carrega a hierarquia; "Figura 1 ·" vira legenda convencional | `polish` |
| **A9** | `style.css:215,217,474` | Craft-floor (ban) | `border-left` colorido 3–4px em `.finding`/`.resumo` (detector confirmou) | Trocar por fundo tingido + título com ícone de estado, ou linha superior de 1px; usar props lógicas | `polish` |
| **A10** | `layout.py:405-410`; `style.css:140-147,392-394` | Template | 4 KPIs iguais, 1 escuro sem razão semântica forte ("hero-metric") | Faixa de resultados-chave alinhada, sem sombra, cor só com significado | `distill` |
| **A12** | `layout.py:131-133,272,89,400`; `app.py:257` | Craft-floor (ban) | Glifos Unicode/emoji como ícones (☀ 🖥 ☾ ↗ → ◼ ⚠ ℹ) | Conjunto SVG único inline em `assets/icons/` (sem CDN); `aria-label` trilíngue em botão só-ícone | `polish` |
| **A8** | `style.css:304,467`; `layout.py:295-300,424,480`; `figuras.py:163,165` | Craft-floor | Mono como fantasia de "técnico" (running header, meta, aviso rodapé); IC/SE são uso legítimo | Reservar mono p/ BibTeX/DOI/código/valores alinhados; resto → Inter pequeno/versalete | `typeset` |
| **A6** | `app.py` meta_tags | Tema | Sem `<meta name="theme-color">` → cromo do browser mobile não casa com o tema | `theme-color` com `media` claro/escuro, atualizado ao trocar tema | `polish` |
| **A14** | `style.css` (global) | Craft-floor | **PARCIAL**: foco unificado ✓; `::selection`, `caret-color`, `accent-color`, `scrollbar-color`, `text-underline-offset` sem tema | Definir as 5 superfícies a partir dos tokens nos 2 temas | `polish` |
| **A13** | `assets/fonts/` (7 arq.) | Performance | 3 famílias / 7 arquivos / ~310 KiB; sem `preload` | ≤4 arquivos (Inter subset/variável; cortar pesos); `preload` da fonte do corpo acima da dobra; `size-adjust` no fallback | `optimize` |
| **A15** | `layout.py:503-506` | Navegação | UF/cidade/idioma fora da URL → não dá p/ compartilhar nem usar Voltar | `dcc.Location(refresh=False)` sincronizando `?uf=&cidade=&lang=`; `replaceState` no clique | `harden` |
| **NEW-2** | `style.css:459,102` | Foco/Navegação | `scroll-margin-top` só no artigo → topbar sticky (56px) cobre o topo de `#painel` após salto de âncora | Adicionar `scroll-margin-top` a `#painel` e demais alvos de nav | `harden` |
| **NEW-3** | `style.css` (global) | Mobile hardening | Sem `touch-action: manipulation`, `-webkit-tap-highlight-color`, `overscroll-behavior` (em `.tbl-wrap`/`.bibtex`/nav-mobile), `env(safe-area-inset-*)` apesar de `viewport-fit=cover` | Adicionar o conjunto mobile-nativo | `harden` |
| **NEW-4** | `style.css:126-127,350,468`; `layout.py:354,217` | Tipografia/Localização | Sem `text-wrap: balance/pretty` em títulos; sem `translate="no"` em marca/BibTeX/DOI (auto-tradução corrompe identificadores) | `text-wrap` em display; `translate="no"` nos identificadores; NBSP número+unidade | `typeset` |
| **NEW-5** | `app.py` `<head>` | Performance | Fontes críticas sem `rel=preload` (flash de swap) | `preload` da fonte do corpo/título acima da dobra | `optimize` |

### P3

- **A16** `style.css:291-295` — mesma entrada (`rise` de `opacity:0`) em `#painel` + 4 KPIs; manter **um** momento autoral partindo de estado visível. `polish`
- **Minor** — `.cards-2` duplicado morto (`style.css:521-525`); ORCID `<img>` sem `width/height` intrínsecos (`layout.py:193`); placeholder "Selecione…" sem cidade-exemplo (`i18n.py:218`); `body { transition: color/background-color }` anima propriedade de paint (custo baixo, 1-shot).

---

## 3. Status A1–A16 (tally)

**0 resolvidos · 4 parciais (A2, A3, A11, A14) · 12 confirmados abertos · 0 N/A.** Tabela completa com evidência file:line em [`raw/findings-A1-A16.md`](raw/findings-A1-A16.md). A pass de a11y moveu A2/A3/A11/A14 para parcial, mas nenhum fechou ponta-a-ponta — cada um tem remanescente aberto.

## 4. O que já está forte (não regredir)

1. **Mapa de 2 camadas** — choropleth teal deliberadamente fora do matiz verde→vermelho dos alertas (evita "estado verde + bolha verde" lido como "tudo ok").
2. **Nível nunca é só cor** — glifo de forma (`clip-path`) + rótulo + intervalo em legenda/cartão/Tabela 1/situação.
3. **Engenharia disciplinada** — recolorir mapa via `Patch` (sem reenviar 128 KB), script de tema pré-paint (sem FOUC), cache imutável versionado, `prefers-reduced-motion`, i18n via `Accept-Language`, axe 0 violações.

## 5. Fontes de evidência

- Capturas "antes": [`docs/ui/shots/before/`](shots/before/) — 62 PNGs (5 larguras × 2 temas × 3 idiomas × fold/full + cidade selecionada + fallback estadual).
- axe: [`raw/axe-before.json`](raw/axe-before.json) · perf: [`raw/perf.json`](raw/perf.json) · overflow: [`raw/overflow-probe.json`](raw/overflow-probe.json) · copy: [`raw/copy-lint-pt.json`](raw/copy-lint-pt.json)/[`-en`](raw/copy-lint-en.json) · HTML renderizado: [`raw/page-pt.html`](raw/page-pt.html)/[`-en`](raw/page-en.html).
- Audits: [`raw/findings-A1-A16.md`](raw/findings-A1-A16.md) · [`raw/web-guidelines.md`](raw/web-guidelines.md) · [`raw/impeccable-audit.md`](raw/impeccable-audit.md).
