---
name: Dengue · LSTM Forecast
description: Painel de previsão de dengue com casca de artigo científico (JBCS), verde-terroso, trilíngue, claro/escuro, WCAG AAA.
colors:
  brand-ink: "#1F3B2C"
  surface: "#F3EFE6"
  surface-raised: "#FBFAF5"
  surface-sunken: "#E9E4D6"
  text: "#1C2620"
  text-muted: "#414741"
  border: "#D9D4C7"
  green: "#3E7A4F"
  green-ink: "#2B5540"
  green-accent: "#A9CDA4"
  terra: "#A8501A"
  topbar: "#1C2620"
  on-brand: "#F3EFE6"
  focus: "#2B5540"
  level-green: "#2E9E5B"
  level-yellow: "#D9A404"
  level-orange: "#EF7D2D"
  level-red: "#D6364C"
typography:
  display:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(2rem, 5vw, 3rem)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 3.4vw, 2.125rem)"
    fontWeight: 600
    lineHeight: 1.18
  title:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(1.35rem, 3vw, 1.625rem)"
    fontWeight: 600
    lineHeight: 1.23
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.46
  serif:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  mono:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.54
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
  callout: "12px"
  pill: "999px"
spacing:
  "2xs": "4px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  "2xl": "48px"
  "3xl": "72px"
components:
  button-primary:
    backgroundColor: "{colors.green-ink}"
    textColor: "{colors.surface-raised}"
    rounded: "{rounded.pill}"
    padding: "10px 18px"
  button-on-brand:
    backgroundColor: "{colors.green-accent}"
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: "10px 18px"
  card:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "16px"
  pill-level:
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: "2px 9px"
  dropdown:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
---

# Design System: Dengue · LSTM Forecast

## Overview

**Creative North Star: "O Periódico Vivo" (The Living Journal)**

É um **artigo científico que se pode consultar**: a página tem o peso e as convenções de um periódico on-line (padrão JBCS — cabeçalho corrido, legendas numeradas, declarações, referências, "como citar") e, embutido no topo, um painel interativo que responde à pergunta operacional "onde a dengue deve subir?". A identidade é **verde-terrosa**, derivada dos slides do estudo de Curitiba — sóbria, de laboratório, nunca "dashboard de produto". A densidade é calma na coluna de leitura (modo Read) e precisa no painel (modo Operate); a cor trabalha a serviço do dado, não da decoração.

A expressão vive **nos detalhes exatos** — o mapa de duas camadas, os glifos de forma por nível, a banda conformal — não em efeitos. Rejeições confirmadas: nada de arco-íris em gráficos, nada de sombra em repouso nas superfícies de leitura, nada de cor como canal único de informação.

**Key Characteristics:**
- Verde-terroso de laboratório; Inter + Source Serif 4 + IBM Plex Mono, auto-hospedadas.
- Casca de periódico (JBCS) + painel embutido; dois modos na mesma página.
- Cor nunca é o único canal (forma + rótulo sempre acompanham).
- WCAG **AAA** nos dois temas; claro/escuro/sistema sem flash.

## Colors

Paleta verde-terrosa de baixa saturação sobre cremes quentes (claro) ou carvões esverdeados (escuro); um único acento terracota para "fora da faixa".

### Primary
- **Brand Ink** (`#1F3B2C`): fundo do hero e de blocos de marca; o verde mais escuro, "tinta" da identidade.
- **Green** (`#3E7A4F`) / **Green Ink** (`#2B5540`): verde de ação e de texto-acento; `green-ink` é a cor do foco (`--focus`), de links e de destaques em superfícies claras (garante AAA).
- **Green Accent** (`#A9CDA4` claro / `#8FD3A4` escuro): acento sobre fundo de marca (título, botão on-brand).

### Secondary
- **Terra** (`#A8501A` claro / `#E59A5E` escuro): **acento semântico único** — marca o excepcional (ex.: "pico fora da faixa de treino"). Nunca decorativo.

### Neutral
- **Surface** (`#F3EFE6`) / **Surface Raised** (`#FBFAF5`) / **Surface Sunken** (`#E9E4D6`): fundo da página, dos cartões/painéis e de blocos recuados. No escuro: `#14181A` / `#1E2428` / `#222A2D`.
- **Text** (`#1C2620`) / **Text Muted** (`#414741`): corpo e texto secundário. No escuro: `#ECEFEA` / `#B6BEB7`.
- **Border** (`#D9D4C7` claro / `#313A39` escuro): a linha de 1px que declara elevação (ver Elevation).

### Named Rules
- **A Regra das Duas Camadas.** O mapa usa dois sistemas de cor *propositalmente distintos*: choropleth **teal** (intensidade estadual) vs. bolhas **verde→vermelho** (nível por cidade). Nunca unificar os matizes — a separação existe para que "estado verde + bolha verde" não seja lido como "tudo sob controle".
- **A Regra da Forma.** Todo nível de alerta carrega **forma + rótulo**, não só cor: verde ●, amarelo ▲, laranja ◆, vermelho ⬣ (octógono), via `clip-path`. Cor nunca é o único canal.
- **A Regra do Terracota.** `terra` só aparece onde há significado excepcional. Sua raridade é a mensagem.

### Alert levels (cor + forma + rótulo)
`level-green #2E9E5B ●` · `level-yellow #D9A404 ▲` · `level-orange #EF7D2D ◆` · `level-red #D6364C ⬣`. Os mesmos matizes nos dois temas; os **fundos** das pílulas é que mudam por tema (sempre AAA com texto `ink`).

## Typography

**Display/Body Font:** Inter (com `system-ui`). **Serif Font:** Source Serif 4 (citações ABNT, toques formais). **Mono Font:** IBM Plex Mono (BibTeX, DOI, IC/SE, valores alinhados).

**Character:** Inter dá a voz neutra e legível do dado; Source Serif 4 traz a autoridade de periódico onde o texto é citação formal; a mono é reservada a **medida e código**, nunca a "cara de técnico". Numerais tabulares (`tabular-nums`) em tabelas, KPIs, horizontes e eixos.

### Hierarchy
- **Display** (Inter 700, `clamp(2rem, 5vw, 3rem)`, lh 1.12, tracking −0.02em): h1 do hero; `.acento` em `green-accent`.
- **Headline** (Inter 600, `clamp(1.5rem, 3.4vw, 2.125rem)`, lh 1.18): título do artigo.
- **Title** (Inter 600, `clamp(1.35rem, 3vw, 1.625rem)`, lh 1.23): títulos de seção (`.sec-titulo`), número KPI (`.sit-total`).
- **Body** (Inter 400, `1rem`, lh 1.5): corpo; medida do artigo **65–75ch** (`--measure: 760px`).
- **Lede** (Inter 400, `1rem`→`1.0625rem`, `text-muted`): subtítulo do hero, máx. ~60ch.
- **Label/Aux** (Inter 400, `0.8125rem`, `text-muted`, lh 1.46): rótulos, notas, metadados.
- **Mono** (IBM Plex Mono 400, `0.8125rem`, lh 1.54): BibTeX, DOI, IC, SE.

**Escala & regras:** pesos disponíveis — Inter 400/500/600/700, Source Serif 4 400/400i/600, Plex Mono 400/500. Tracking **nunca** abaixo de −0,04em. `text-wrap: balance` em display/títulos, `pretty` em parágrafos (a aplicar na fase de tipografia).

## Layout

- **Mobile-first**, breakpoints `min-width` **481 / 768 / 980 / 1200**.
- Containers: `--container: 1344px` (largura total), `--measure: 760px` (coluna de leitura), `--topbar-h: 56px` (topbar sticky).
- **Gutter** lateral `16px`, igual nos dois lados em todas as larguras; **sem overflow horizontal** de 320 a 1440px (verificado na Fase 0).
- Escala de espaçamento 4/8/12/16/24/32/48/72: grupos internos apertados, separação generosa entre blocos; **mais espaço acima de um título do que abaixo**.
- Painel: no desktop (≥980px) hero em 2 colunas (h1 à esquerda, Situação à direita); no mobile empilha.

## Elevation & Depth

**Sistema plano com camadas tonais.** A elevação é declarada **uma vez por superfície** — por **borda de 1px tingida** (`--border`), não por sombra. Superfícies de leitura e painéis (`.card`, `.panel`, `.stat`, `.tbl-wrap`) são **planas** (borda, sem `box-shadow` em repouso).

**A sombra de duas camadas (`--shadow`: `0 1px 2px` + `0 8px 24px`, mais densa no escuro) é reservada ao que flutua** — dropdown aberto, menu mobile, tooltip. Nunca aplicar sombra de repouso a cartões. Sem halos de offset-zero, sem sombras de bloco (neobrutalismo).

## Shapes

Raios: `sm 6px` (foco, controles pequenos), `md 10px` (avisos, ícones), `lg 14px` (`--radius`: cartões, painéis, tabelas), `callout 12px` (`.finding`), `pill 999px` (botões, pílulas de nível, `.seg`, chips). Bordas sempre `1px solid var(--border)`. Formas dos níveis via `clip-path` (ver Regra da Forma). Usar **propriedades lógicas** (`border-inline-start`, `padding-inline`) no CSS novo/tocado.

## Components

- **Button (primary)** — fundo `green-ink`, texto `surface-raised`, pílula, `10px 18px`. **On-brand**: fundo `green-accent`, texto `text` (sobre hero escuro).
- **Segmented control (`.seg`)** — idioma/tema; pílula, **44×44px** (AAA target), ativo = fundo claro fixo `#F3EFE6` + texto escuro `#1C2620` (não segue tema, por contraste).
- **Card/Panel** — `surface-raised`, borda 1px, raio `lg`, padding `16px`, plano.
- **Pill (nível)** — forma+rótulo+cor; texto `ink`, fundo tingido por nível (AAA), raio pílula.
- **Dropdown (`dcc.Dropdown`, Dash 4.5)** — trigger `surface-raised`/`text`, raio `sm`; o `<button>` é o tab stop de teclado (shim `aria-hidden` inerte, ver `assets/a11y_dropdown.js`); menu aberto flutua (sombra 2 camadas).
- **Focus ring** — `3px solid var(--focus)`, offset 2px, raio 6px; aplicado também a superfícies incorporadas (dropdown, `<summary>` do Plotly).

## Do's and Don'ts

**Do**
- Manter cor + forma + rótulo em todo nível de alerta.
- Declarar elevação por borda; reservar sombra para o que flutua.
- Rotear **todo número/data** por um formatador por idioma (PT/ES `.`/`,`; EN `,`/`.`).
- Numerais tabulares em dados; medida de leitura 65–75ch.
- Tokens: usar os **semânticos** (`--surface`, `--text`, `--border`, `--focus`, `--level-*`); os primitivos são a paleta-base.

**Don't**
- Eyebrow/kicker acima de título (ban); `border-left` colorido >1px (ban); glifo Unicode/emoji como ícone (ban); mono como enfeite.
- Arco-íris em gráficos; cor como canal único.
- Sombra de repouso em cartões; nova origem externa (fontes são auto-hospedadas; CSP intacta).
- Reintroduzir Google Fonts ou qualquer CDN.

<!-- Exceções deliberadas (não são defeitos):
     • Numeração de seções do artigo (1 Introdução … 5 Conclusão) — convenção JBCS, a sequência informa.
     • Cabeçalho corrido em mono — convenção de periódico (JBCS), uso legítimo.
     • Inter como sans da identidade (detector marca overused-font) — fonte do projeto, waiver registrado. -->
