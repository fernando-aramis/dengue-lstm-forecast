# Painel de previsão de dengue — Brasil (Dash)

Mapa nacional com previsão semanal de dengue para **capitais e principais cidades** de cada
estado, com **fallback estadual** quando a cidade do usuário não tem modelo. Interface em
**Dash + Plotly**. É a "Opção 1" da arquitetura: **o app não treina e não re-prevê** — ele
só lê previsões já calculadas.

O mapa tem **duas camadas**: um *choropleth* estadual (fundo, colorido pelo total previsto) e
**bolhas** por cidade (frente, pela cor do nível de alerta) — inspirado no painel de COVID do
Ministério da Saúde, mas leve e sem servidor BI. Além do mapa, a página traz o **contexto do
estudo** (resumo, metodologia, resultados e limites do artigo LSTM de Curitiba) e segue a
**identidade visual** do projeto (paleta verde-terrosa + Inter, derivadas do `.pptx`), com
contraste WCAG AA, foco visível e movimento discreto (respeita `prefers-reduced-motion`).

> ✅ **Os dados em `data/*.csv` são REAIS** — gerados por `pipeline/gerar_previsoes_reais.py`
> (InfoDengue → EDA → LSTM A + conformal) para 33 cidades, **pipeline completo** (500 épocas),
> origem na semana de 2026-10-25. Os **33 geocodes foram validados contra o IBGE**. O
> `data/br_uf.geojson` é a malha do IBGE **simplificada** (~128 KB; ver `pipeline/simplificar_geojson.py`).
>
> **Acessibilidade e responsividade:** contraste de cores no padrão **WCAG 2.x AAA** (texto
> normal ≥ 7:1, grande ≥ 4,5:1) **nos temas claro e escuro**, e layout **mobile-first**
> validado em 480 / 767 / 768 / 980 / 1200 px — ver `tests/`.
>
> **Tema e idioma:** pílula de tema (claro / sistema / escuro, com `prefers-color-scheme` e
> `localStorage`) e pílula de idioma **PT / EN / ES** — detecta o idioma do navegador
> (`Accept-Language`) e cai em **EN** sem correspondência. Textos em `i18n.py`; o mapa e os
> gráficos trocam de paleta junto com o tema.

## Arquitetura

```
OFFLINE (semanal, ex.: GitHub Action)          WEB (sempre leve)
┌────────────────────────────────────┐        ┌─────────────────────────────┐
│ InfoDengue (casos) + clima          │        │ Dash app (app.py)           │
│   → features (log1p, janela 12)     │        │   lê data/*.csv (em cache)  │
│   → modelo POOLED (1 só, município  │  CSV   │   → mapa (bolhas por cidade)│
│     como feature) → ONNX/TFLite     │ ─────▶ │   → clique/seletor UF→cidade│
│   → conformal 90% + agregado estad. │        │   → fallback estadual       │
│   grava historico.csv / previsoes.csv│       │   → gráfico 4 sem. + banda  │
└────────────────────────────────────┘        └─────────────────────────────┘
```

Nada é treinado no request → o deploy fica leve e grátis. Se exportar o modelo para
**ONNX/TFLite**, o servidor nem precisa de TensorFlow.

## Rodar localmente

```bash
cd webapp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# os dados REAIS já estão em data/ — basta subir o app:
python app.py            # -> http://127.0.0.1:8050   (DASH_DEBUG=1 liga o modo debug)

# (opcional) instalação ENDURECIDA/reprodutível, com verificação de hash — idêntica à da imagem:
#   pip install --require-hashes -r requirements.lock
# (regere o lock quando requirements.txt mudar — ver o comando `uv pip compile` no Dockerfile)
```

## Estrutura

| Arquivo | Papel |
|---|---|
| `app.py` | App Dash: init, callbacks, cabeçalhos de segurança e gzip. Só **lê** `data/`. |
| `dados.py` | Carga de CSV/GeoJSON + globais derivados (cap do intervalo, `_meta.json`). |
| `figuras.py` | Figuras Plotly (mapa, detalhe) e cartão, com paleta por tema (claro/escuro). |
| `layout.py` | Blocos editoriais, barra de controles (idioma/tema) e montagem da página. |
| `i18n.py` | Traduções PT/EN/ES da interface (detecção por `Accept-Language`, fallback EN). |
| `assets/style.css` | Identidade visual (paleta do `.pptx` + Inter), temas claro/escuro, responsivo e acessível (AAA). |
| `data/previsoes.csv` · `data/historico.csv` | Previsão t+1..t+4 + banda 90% (cidade **e** estado) · casos observados. |
| `data/_meta.json` · `data/snapshots/` | Proveniência (coleta, modelo, origem) · snapshots datados (backtesting). |
| `data/br_uf.geojson` | Malha das 27 UFs (IBGE, **simplificada** ~128 KB; chave `properties.sigla`). |
| `pipeline/infodengue.py` | Coleta a série semanal real (API alertcity) + **validação de schema**. |
| `pipeline/preparacao.py` · `pipeline/modelo.py` | EDA/preparação (19 etapas) · LSTM A + conformal 90%. |
| `pipeline/gerar_previsoes_reais.py` | **Pipeline completo**: InfoDengue → EDA → modelo → CSVs + `_meta.json` + snapshot. |
| `pipeline/simplificar_geojson.py` | Simplifica a geometria da malha (offline, shapely) p/ reduzir o payload do mapa. |
| `pipeline/validar_geocodes.py` | Confere os geocodes de `cidades.py` contra o IBGE (33/33 OK). |
| `pipeline/_log.py` | Logging padrão do pipeline (stdlib). |
| `tests/test_unit.py` · `tests/test_e2e.py` | Validação (AAA claro/escuro, contrato, _meta, geojson, segurança) · Playwright (5 breakpoints, idioma/tema). |
| `.github/workflows/` | CI (testes) e refresh semanal — **inertes** até o projeto ir para o GitHub. |

## Testes

```bash
cd webapp && source .venv/bin/activate
pip install -r tests/requirements.txt
python -m playwright install chromium     # 1ª vez (navegador do E2E)
pytest tests/ -q                          # 30 testes: validação + E2E
```

As prévias ficam em `tests/screenshots/` (`bp-*` por breakpoint; `dark-*` no tema escuro).

O schema de `previsoes.csv` / `historico.csv` é o **contrato** entre o pipeline e o app:
mantenha as colunas e o app não muda.

## Operação / produção

- **Variáveis de ambiente:** `DASH_DEBUG=1` liga o debug (padrão **desligado** — nunca ligar em
  produção), `HOST`/`PORT` (padrão `127.0.0.1:8050`), `LOG_LEVEL` (padrão `INFO`).
- **Segurança (hardening de exposição):** cabeçalhos `X-Content-Type-Options`, `Referrer-Policy`,
  `X-Frame-Options`, HSTS, `Permissions-Policy` e uma **CSP em Report-Only** — mantida assim por
  **decisão documentada**: o renderer do Dash exige `script-src 'unsafe-inline' 'unsafe-eval'` e os
  mapas (MapLibre) exigem `worker-src blob:`, então enforçar agregaria pouco sobre os demais
  cabeçalhos (ver a docstring de `_cabecalhos_seguranca` em `app.py`). Sem auth/DB/PII por design.
- **Desempenho:** respostas com **gzip** (flask-compress) e geojson simplificado; o tema recolore
  o mapa via `Patch` parcial, **sem reenviar** o geojson.
- **Regerar a malha enxuta:** `python pipeline/simplificar_geojson.py` (lê sempre o backup
  `data/br_uf.full.geojson`; idempotente). `TOLERANCIA=0.03` para reduzir ainda mais.
- **Container:** `docker build -t dengue . && docker run -p 7860:7860 dengue` — roda como
  usuário **não-root**, com `HEALTHCHECK`.

## Deploy — Render (Docker, free tier)

O repositório traz um **`render.yaml`** (Blueprint) e o `Dockerfile` já pronto. A porta é dinâmica
via `$PORT` (o Render injeta), e `WEB_CONCURRENCY=1` mantém o uso de memória dentro do free tier.

1. Em [render.com](https://render.com), faça *Sign up with GitHub* e autorize o repositório.
2. **New → Blueprint** → selecione este repo. O Render lê o `render.yaml`, builda o `Dockerfile`
   e publica o web service (monitorando `/health`).
3. Deploy automático a cada push em `main`. Em *Settings* dá para exigir **"After CI Checks Pass"**.
4. Para atualizar a previsão: rode o pipeline offline (ou o workflow `refresh.yml`) e faça commit
   dos novos `data/*.csv` — o push redispara o deploy.

> Hugging Face Spaces exige **plano pago** para Spaces com compute (Docker/Gradio); só *Static* é
> grátis e não roda o servidor Dash. A imagem é portável: Render, Fly.io, Koyeb etc. servem o mesmo
> `Dockerfile` (ou `gunicorn app:server`).

## Pipeline real (previsão de verdade)

Já implementado em `pipeline/`. Fluxo por cidade:

```
InfoDengue (alertcity)  →  EDA + preparação  →  LSTM A + conformal  →  próximas 4 semanas
   casos_est (nowcast)      replica a planilha    versão univariada       + intervalo 90%
```

Rodar (precisa de TensorFlow — ver `pipeline/requirements.txt`):

```bash
cd webapp && source .venv/bin/activate
pip install -r pipeline/requirements.txt
cd pipeline
# teste rápido numa cidade:
CIDADES_GEO=4106902 MODO_RAPIDO=1 python gerar_previsoes_reais.py
# todas as cidades (lento em CPU; ideal rodar no Colab/GPU como o estudo):
python gerar_previsoes_reais.py
```

Isso sobrescreve `data/historico.csv` e `data/previsoes.csv` com previsões **reais** e grava
`data/eda.json` (estatísticas por cidade). O app passa a mostrar previsão real sem nenhuma mudança.

**Decisões do pipeline (fiéis ao estudo):**
- **Modelo univariado (só casos)** — foi o melhor no artigo; o clima causou sobreajuste. Isso
  também contorna o fato de a alertcity não trazer precipitação.
- **Nowcast `casos_est`** como série — corrige o atraso de notificação das semanas recentes
  (use `casos` em `preparacao.preparar(...)` para reproduzir o notificado do estudo).
- **Normalização Min-Max só com o treino**, log1p, seno/cosseno da semana — iguais à planilha.
- Zeros e outliers mantidos; semanas finais sinalizadas (`semana_incompleta`).

### Próximos passos
1. ✅ **Geocodes validados** contra o IBGE (33/33 — `pipeline/validar_geocodes.py`).
2. ✅ **Pipeline completo** rodado (épocas plenas). Para re-treinar no futuro: Colab/GPU ou o
   workflow `refresh.yml` quando o projeto estiver no GitHub.
3. Evoluir para o **modelo pooled** (município como feature) — ver a análise do projeto original.
4. **GitHub Actions** (`.github/workflows/ci.yml` e `refresh.yml`) já prontos — **inertes** até
   subir o repositório; ao subir, revisar o pin do `tensorflow-cpu` para o Python do runner.
5. **CSP** mantida em Report-Only por **decisão documentada** (o Dash exige `unsafe-eval`/
   `unsafe-inline`; o MapLibre exige `worker-src blob:`) — ver a docstring de
   `_cabecalhos_seguranca`. Próximo passo possível: adicionar um coletor `report-to`/`report-uri`
   para o Report-Only gerar telemetria útil.
6. (Opcional) Geolocalização do browser para pré-selecionar a cidade, com fallback ao estado.

## Créditos e colaboração

**Autor:** Fernando Aramis Colque — IAGA04 (Aprendizado Profundo), Especialização em IA Generativa
Aplicada, **UTFPR** (2026). O painel estende ao mapa nacional o estudo *"Previsão semanal de casos de
dengue em Curitiba com redes LSTM"*.

**Dados e referências:** casos prováveis do SINAN via **InfoDengue** e clima ERA5 via **Mosqlimate**
(Coelho et al., 2024 — Infodengue-Mosqlimate Sprint 2024, Zenodo 10.5281/zenodo.13328231); malha
estadual do **IBGE**. Referências: Araujo et al. (2026, PNAS), Chen & Moraga (2025, BMC Public
Health), Mussumeci & Coelho (2020), Hochreiter & Schmidhuber (1997).

> 🤖 **Co-autoria e validação com IA:** este projeto foi desenvolvido com a colaboração do
> **[Claude Code](https://claude.com/claude-code) (Anthropic)** — planejamento, revisão de código,
> testes, acessibilidade (WCAG 2.x AAA / 3.0 APCA), hardening de segurança e CI/CD. A revisão e as
> decisões finais são do autor.
