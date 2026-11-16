# AFTER — Fase 8 (estado "depois")

**Projeto:** painel `dengue-lstm-forecast` (Dash 4.5 + Plotly 7.1, PT/EN/ES, claro/escuro, casca de artigo JBCS).
**Branch:** `fix/a11y-ui-remediation` · **Baseline:** [`BASELINE.md`](BASELINE.md) (Fase 0, 2026-11-13).
**Escopo:** refino de UI/UX — *refino, não redesign* (identidade verde-terrosa, casca JBCS, AAA e trilíngue preservados).

Evidência bruta: [`raw/axe-after.json`](raw/axe-after.json) · [`raw/perf-after.json`](raw/perf-after.json) ·
[`raw/overflow-after.json`](raw/overflow-after.json) · capturas em [`shots/after/`](shots/after/)
(as `*full*.png` ficam fora do git por decisão; as de dobra, cidade e fallback estadual estão versionadas).
Exceções conhecidas do Dash: [`A11Y-EXCECOES.md`](A11Y-EXCECOES.md) · waivers antigos: [`waivers.md`](waivers.md).

---

## 1. Medições: antes × depois

Mesmo método do baseline (Chromium headless, app local :8050). **Atenção:** CPU de máquina de desenvolvimento;
LCP/FCP servem só de comparação relativa, não de promessa.

| Métrica | Antes (Fase 0) | Depois | Observação |
|---|---|---|---|
| **axe-core** | 0 violações (wcag2a…22aa + best-practice; 360/1440 × 2 temas, PT) | **0 violações** com `wcag2a/aa/aaa`, `21a/aa`, `22aa`, `best-practice` em **30 combinações** (320/390/768/1024/1440 × 2 temas × PT/EN/ES) | O baseline **não rodava regras AAA**; a medição de agora é mais rigorosa. "Incomplete" = revisão manual (contraste sobre o canvas do mapa, como antes; `aria-allowed-role` do dropdown, ver exceções) |
| **Overflow horizontal** | 0 em 320–1440 | **0** nas 30 combinações | |
| **CLS** | **0,690 @1440 (FAIL)** · 0,146 @390 | **0** @1440 e @390 (mediana de 7 execuções) | Causas tratadas: barra do topo (1,15→0,03), footer do Dash, 1º render em idioma errado, fontes, `content-visibility` |
| **Fontes** | 3 famílias / 7 arq. / ~310 KiB / sem preload | **3 famílias / 3 arq. no carregamento (112 KiB)**; 5 no repositório (145 KiB, itálico e Mono 500 sob demanda); `preload` de Inter e Source Serif; **teste trava os 3 woff2 (≤120 KiB) na carga inicial** | O Google servia os **mesmos bytes** do Inter sob 4 URLs e do Serif sob 2 |
| **Transferência total** | ~2220 KiB | **~2004 KiB** (`transferSize`) | JS ~1726 KiB gz (Dash/Plotly/MapLibre): inerente, ver [waivers](waivers.md) |
| **CSS** | 11,4 KiB | **15,9 KiB** (+4,5) | Aumentou: menu de acessibilidade, paleta CVD, ícones por máscara, estados novos |
| **LCP** | 440 ms @1440 | ~115 ms @1440 · ~465 ms @390 | Comparação só indicativa (host diferente) |
| **Testes automatizados** | — | **183** (unit + formato + i18n + sem cobertura + E2E + axe AAA) | Cada correção de bug tem teste, provado por mutação quando possível |
| **Copy-lint** | em-dash ×15, eyebrows ×10, stat-strip ×3 | em-dash **×6** (limite 2), eyebrows **0**, stat-strip ×3 | Em-dashes de interface trocados por `:` `,` `;` (PT/EN/ES). Os 6 restantes são prosa do artigo (decisão editorial do autor). `stat-strip` é falso positivo: o detector lê linhas de tabelas de dados como "faixa de números" |
| **Nielsen** | 24/36 | _ver §5_ | Qualitativo (julgamento de modelo), não métrica |
| **impeccable detect** | side-tab ×2 + advisories | **63 advisories** (font-size 36, color 23, radius 4); **0 antipadrões bloqueantes** | Job não bloqueante no CI |

---

## 2. Achados A1–A16 e NEW-1…5: antes × depois

Legenda: ✅ resolvido e testado · 🟡 resolvido com ressalva · ⏳ aberto (baixo risco).

| # | Achado | Depois | Evidência / commit |
|---|---|---|---|
| **A1** | Formatos numéricos/data por idioma | ✅ `formato.py` é o único ponto; `separators` e `hoverformat` por idioma; **locale inline do Plotly** (meses em PT/ES) | `040c1f8`, `5fbd7aa`; `test_formato.py`, E2E de formato por idioma |
| **A2** | Nível só por cor (bolhas) | ✅ glifo + rótulo nas superfícies HTML, **anel de espessura 1→4 px por nível** nas bolhas, paleta CVD opt-in; contraste do contorno testado | `3d02420`, `dde7156`, `5eeeb59`; 🟡 amarelo CVD sobre painel claro segue baixo — o anel compensa |
| **A3** | Alvos de toque | ✅ controles 44 px; links ≥24 px; dropdown 44 px; menu de acessibilidade 44 px | `3d02420`, `cae1cca`; `test_alvos_de_toque_*` |
| **A4** | Cold-start só com "Loading…" | ✅ shell estático **trilíngue** + `<noscript>` com DOI, `position:fixed` (sem CLS) | `1918477`; `test_shell_estatico_e_noscript_sem_javascript` |
| **A5** | Mapa sem plano B se WebGL falhar | ✅ fallback com link à Tabela 1 — **e um bug introduzido na Fase 2** (faixa sempre visível) foi achado e corrigido | `3d02420`, `fd23446` |
| **A6** | Sem `theme-color` | ✅ meta segue o tema resolvido | `1918477`; `test_meta_theme_color_acompanha_o_tema` |
| **A7** | Eyebrows e chips | ✅ removidos; hierarquia pelo título | `c0f640c` |
| **A8** | Mono como decoração | ✅ mono só em cabeçalho corrido, código, DOI e medidas | `c0f640c` |
| **A9** | `border-left` colorido >1 px | ✅ fundo tingido + marcador de estado; detector sem `side-tab` | `c0f640c` |
| **A10** | 4 KPIs iguais, um escuro | ✅ faixa plana, cor só com significado | `c0f640c` |
| **A11** | 1ª tela mobile = cromo | ✅ h1 → lede → Situação → CTAs; idioma/tema/menus recolhem | `c0f640c`, `e82d496` |
| **A12** | Glifos Unicode/emoji como ícone | ✅ SVG por máscara, `aria-label` trilíngue | `7ca9031` |
| **A13** | Fontes acima do orçamento | ✅ ver tabela acima | `d5ff333` |
| **A14** | Superfícies do navegador sem tema | ✅ `::selection`, `caret-color`, `accent-color`, `scrollbar-color`, sublinhado | `7ca9031` |
| **A15** | Estado fora da URL | ✅ `?lang=&cidade=` (`replaceState`, validado); o **1º render já nasce no idioma da URL** (via `Referer`) | `df2d3e6`, `031e1c4` |
| **A16** | Mesma animação em tudo | ✅ uma entrada autoral; `content-visibility` (−28% de custo de layout no desktop, −27% no mobile) | `36d6fb4` |
| **NEW-1** | Troca de cidade sem anúncio | ✅ `#cartao-status` (`role=status`), inclusive no estado sem cobertura | `7ca9031`, `4a01b53` |
| **NEW-2** | `scroll-margin-top` | ✅ nos alvos de âncora, testado em 3 idiomas × 2 larguras | `36d6fb4` |
| **NEW-3** | Mobile-nativo (`touch-action`, safe-area…) | ✅ | `7ca9031` |
| **NEW-4** | `text-wrap`, `translate`, NBSP | ✅ `text-wrap: balance/pretty`; nomes próprios com `notranslate` (o Dash não aceita `translate=`) | `96a0aac` |
| **NEW-5** | Preload de fontes | ✅ | `d5ff333` |

---

## 3. O que a verificação encontrou **além** dos achados originais

Diagnóstico por capturas e por auditoria com 3 agentes (a11y, i18n, arquitetura) revelou problemas que o baseline não via.
Todos corrigidos e com teste:

- **Gráfico sobre os cartões t+1…t+4 abaixo de 980 px**, **meses em inglês** em página PT, **banda de 90% com contraste 1,3:1**, painel sem recuo.
- **Barra do topo** quebrando em 2–3 linhas (CLS 1,15) e **cabeçalho corrido** quebrando entre 768 e 1179 px.
- **Races**: trocar idioma depois de escolher cidade revertia a seleção; trocar idioma no tema escuro devolvia o mapa claro; o Patch de tema não recolorava o contorno.
- **Cache**: um 404/500 transitório ficava 1 ano como `immutable`; `/_dash-layout` varia por `Referer`/`Accept-Language` e agora declara isso.
- **Validação**: tipos forjados em callbacks, `?cidade=` sem limite, contrato de dados (`nivel_alerta`, NaN).
- **AAA que o axe padrão não roda**: botões da barra no escuro a 6,2:1; anel de foco 1,4–1,8:1 sobre barra/hero; popover cortado a 320 px; marca quebrando a 320 px.
- **i18n**: `Figura/Tabela N.` fixos em PT, `SE` em vez de `EW` em inglês, `lang` errado na nota, `<html lang>` tardio, `<title>` e rótulos do dropdown só em PT.
- **Texto CVD sem lastro**: o comentário citava "pior par 59,3"; medido (ΔE76, Machado 2009): protanopia 17,4→26,9 e deuteranopia 10,1→11,6. Texto corrigido e travado em teste.

---

## 4. O que **segue aberto** (decisão consciente ou fora de alcance)

- **Exceções do Dash 4.5** nos menus abertos (`aria-allowed-role`, `nested-interactive`, `aria-dialog-name`, `aria-input-field-name`): conjunto **fechado e com teto** em teste; reavaliar a cada atualização do Dash.
- **Tabela 1** lista 8 de 33 cidades (decisão: o anel nas bolhas resolve o canal não cromático do mapa).
- **Links do menu na barra** com ~33 px (passam de 24 px, não de 44 px); **foco sobre a atribuição de terceiros** do mapa.
- **Cabeçalho corrido** em `.72rem` (exceção do piso tipográfico: o texto longo estouraria 1180 px).
- **Pares de contraste antigos** em hex digitado em `test_unit.py` (os novos derivam dos tokens).
- **Copy-lint**: 6 em-dashes na prosa do artigo e `stat-strip` ×3 (falso positivo) ficam como exceção documentada.
- **CI no GitHub não foi executado** (repositório ainda local): YAML e comandos do job foram validados localmente.
