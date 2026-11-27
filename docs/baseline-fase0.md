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
