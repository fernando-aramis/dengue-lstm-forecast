# Baseline da Fase 0 (2026-11-27)

Referência para a DoD: **nenhuma piora > 10%** nos valores abaixo. Commit medido: `73b83ab` (+ esta página).
Ambiente: WSL2, Docker 29.10.0, build do `Dockerfile` do repositório (sem cache de camadas de runtime).

| Métrica | Valor | Comando de medição |
|---|---|---|
| Suíte de testes | **225 passed** (~7 min) | `source .venv/bin/activate && pytest tests/ -q` |
| Tamanho da imagem | **905 MB** | `docker build -q -t dengue-baseline . && docker image ls dengue-baseline --format '{{.Size}}'` |
| Tempo de build | ~59 s | `time docker build -q -t dengue-baseline .` |
| Tempo até `/health` 200 | **2,7 s** | `t0=$(date +%s.%N); docker run -d --name dengue-bl -p 17860:7860 dengue-baseline; until [ "$(curl -s -o /dev/null -w '%{http_code}' localhost:17860/health)" = 200 ]; do sleep 0.2; done; echo "$(date +%s.%N) - $t0" \| bc` |
| Memória (container, ocioso, após 1 GET `/`) | **200 MiB** | `docker stats --no-stream --format '{{.MemUsage}}' dengue-bl` (RSS do gunicorn ≈ valor do container) |
| HTML inicial (`/`) | **15.792 B** | `curl -s localhost:17860/ -o idx.html -w '%{size_download}'` |
| `_dash-layout` (gzip) | **53.478 B** | `curl -s -H 'Accept-Encoding: gzip' --compressed -o /dev/null -w '%{size_download}' localhost:17860/_dash-layout` |
| JS+CSS iniciais (gzip, soma dos `src`/`href` de `/`) | **315.486 B** | para cada URL em `idx.html`: `curl -s -H 'Accept-Encoding: gzip' -o /dev/null -w '%{size_download}' localhost:17860$url` |

Observações: medido uma vez (sem média); a variação de tempo de boot entre execuções é da ordem de ±0,5 s.

## Correção do baseline da imagem e efeito do Q.7 (2026-11-27)

**O baseline de 905 MB estava inflado pela árvore local:** `docs/ui/shots/` e outras pastas de screenshots estão no `.gitignore`, mas existem em disco e entravam no contexto do `docker build` local. Em **clone limpo** (`git clone` em diretório temporário, como o CI e o Render), a imagem da `main` (d3b7480) tem **652 MB**. Comparações de tamanho devem usar clone limpo.

| Métrica (clone limpo) | Antes (main) | Depois (`chore/imagem-enxuta`) |
|---|---|---|
| Tamanho (`docker image ls`) | 652 MB | **513 MB (−21%)** |
| Tempo até `/health` 200 (3 execuções) | 1,85–1,98 s | 1,81–2,90 s (ruído do WSL2; sem piora sistemática) |
| Memória do container, ocioso (3 execuções) | 184–200 MiB | 186–212 MiB |

Mudanças (lock e base intactos): `tests/` de pandas/numpy removidos no `RUN` do pip; `docs/` e docs de apoio no `.dockerignore`; `COPY --chown` no lugar de `chown -R`; `pip`/`setuptools`/`wheel` desinstalados no runtime (upgrade, instalação do lock e limpeza num único `RUN`).

## Baseline Lighthouse (Q.5, 2026-11-27)

Lighthouse 13.6.0 contra o container local (clone limpo da `main`), Chromium do Playwright (1255), uma execução por perfil (sem média; o TBT oscila entre execuções).

| Perfil | Desempenho | Acessibilidade | Boas práticas | SEO | FCP | LCP | TBT | CLS | Speed Index |
|---|---|---|---|---|---|---|---|---|---|
| Mobile (padrão, 4× CPU, 4G lento) | **67** | **100** | **96** | **83** | 1,5 s | 1,5 s | 6.470 ms | 0 | 4,4 s |
| Desktop (`--preset=desktop`) | **68** | **100** | **96** | **83** | 0,4 s | 0,4 s | 1.190 ms | 0,003 | 1,8 s |

Reprovações: SEO `meta-description` e `robots-txt` (alvo das tarefas 1.13/1.14); Boas práticas `errors-in-console`. O desempenho é dominado pelo TBT (JS do Dash/Plotly no carregamento).

Comando (o `chrome-launcher` do Lighthouse confunde o WSL com Windows; por isso o Chromium é iniciado à parte e passado por `--port`):

```bash
docker build -q -t dengue-lh . && docker run -d --name dengue-lh -p 17861:7860 dengue-lh   # esperar /health 200
C=~/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome
$C --headless=new --no-sandbox --remote-debugging-port=9333 --user-data-dir=$(mktemp -d) about:blank &
cd /tmp && npx --yes lighthouse@13.6.0 http://localhost:17861/ [--preset=desktop] --port=9333 \
  --only-categories=performance,accessibility,best-practices,seo --output=json --output-path=lh.json
```
