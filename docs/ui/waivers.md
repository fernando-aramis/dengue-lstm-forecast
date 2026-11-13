# Waivers — regras de skill e ferramentas ignoradas (com motivo)

Registro de cada regra de skill deliberadamente não seguida e de cada ferramenta que não
rodou, conforme a precedência da seção 2.2 do brief (brief/ciência > craft-floor Impeccable
> Web Interface Guidelines > ferramentas Taste). Atualizar a cada fase.

## Ferramentas que não rodaram nativamente

| Ferramenta | Situação | Motivo | Mitigação |
|---|---|---|---|
| **Taste `consistency.mjs`** | Não rodou | Bug determinístico do Node v24.19.0 (undici `ERR_ASSERTION assert(!this.paused)` ao ler resposta gzip/chunked da app); não é falha de Chrome | Sonda própria de overflow em Playwright (`raw/overflow-probe.json`), 320–1440px → 0 overflow. Reavaliar com `--no-sweep` ou Node LTS numa fase futura |
| **Taste `gate.mjs`** | Não armado (por decisão) | As *house rules* da Taste 2.5 são para sites de marketing (fotos reais, 1 seção/tela, momentos animados, hover-lift, cenas WebGL) — contradizem um painel científico | Usadas só as ferramentas de medição (`perf`, `copy-lint`, overflow); `deal`/`moments`/`photos`/`effects` não rodados |
| **Impeccable — overlay de browser + screenshots** | Pulado | A instância :8050 era do outro agente; o audit foi estático/source-based | Detector CLI rodou (CSS/markup); checagens de pixel renderizado (contraste computado, overflow in-situ, foco) reavaliar em instância rodando numa fase futura |
| **Impeccable `critique` A/B isolado** | Degradado (single-context) | Subagente diagnóstico não autorizado a spawnar os 2 sub-agentes isolados | Assessment A (review) + Assessment B (detector) inline; 5 Priority Issues registrados |

## Regras de skill conscientemente não aplicadas (ou adiadas)

| Regra | Skill | Decisão | Motivo |
|---|---|---|---|
| **≥2 camadas de sombra** | Web Interface Guidelines | Não aplicar em superfícies de leitura/painéis | Conflito resolvido no brief (2.2): superfícies planas (1px borda tingida); sombra 2-camadas só no que flutua (dropdown aberto, menu, tooltip). Precedência: craft-floor Impeccable (elevação declarada 1×) > Vercel |
| **APCA para contraste** | Web Interface Guidelines | Manter **WCAG AAA** como piso | O projeto já garante AAA nos 2 temas (testes de contraste). APCA medido só como informação extra |
| **`overused-font: Inter` ×4** | Impeccable (detector) | Parcialmente waived | Inter é a fonte da identidade do projeto, auto-hospedada e pareada com Source Serif 4 + IBM Plex Mono (acima do default Inter-only). Trade-off conhecido, não falso-positivo. **Registrado** na Fase 1: `.impeccable/config.json` → `ignoreValues` `overused-font=inter` |
| **Numeração de seções** | Impeccable (craft-floor) | **Manter** "1 Introdução … 5 Conclusão" | A sequência informa (convenção de periódico JBCS); o craft-floor aceita números quando a sequência significa algo |
| **JS bundle / nº de arquivos (FAIL perf)** | Taste `perf.mjs` | Waiver | Bundle Dash/Plotly/MapLibre (1735 KiB gz / 15 arq.) é inerente ao framework no caminho de serving; não "burlar". Ganhos reais ficam em CLS, fontes e cold-start |
| **`em-dash` ×15 / `eyebrows` ×10 (copy-lint)** | Taste `copy-lint.mjs` | Eyebrows: **acatar** (= A7, remover). Em-dash: avaliar na Fase 3 | Orçamento de em-dash (2) é calibrado p/ marketing; prosa de artigo científico usa travessão legitimamente. Reduzir onde for ruído, manter onde a pontuação pede |

## Decisões tomadas por conta própria (revisar)

- **ORCID** corrigido na pass de a11y como **SVG logo oficial** (`assets/icons/orcid.svg`) em vez do texto "iD" — isenção de logotipo (WCAG 1.4.3) + fiel à marca. Falta `width/height` intrínseco (P3).
- **Estado "sem cobertura"**: as ramificações `card_prompt`/`sem_cob_cartao` são código morto (todas as UF/cidades têm previsão). Não desenhar estado vazio para algo inalcançável — decidir na fase de estados se vale manter o código defensivo.
