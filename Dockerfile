# Dash no Hugging Face Spaces (SDK: Docker). Porta 7860 é a esperada pelo Spaces.
# Base pinada por DIGEST (reprodutível + controle de quando a base muda).
# python:3.11-slim (Debian 13/trixie) — digest resolvido em 2026-11-09.
# Para re-pinar no futuro: docker pull python:3.11-slim && \
#   docker inspect --format '{{index .RepoDigests 0}}' python:3.11-slim
FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

# Security updates do Debian no build (fecha CVEs HIGH/CRITICAL corrigíveis da base).
RUN apt-get update && apt-get -y upgrade \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# usuário não-root (hardening: não rodar o container como root)
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

# tooling de build atualizado (corrige CVEs de pip/setuptools: CVE-2024-6345, CVE-2025-47273, etc.)
# e remoção dos wheels empacotados do ensurepip (pip/setuptools antigos, só usados por `python -m venv`,
# que o container de serving nunca faz) — fecha os CVEs residuais e reduz superfície de ataque.
RUN pip install --no-cache-dir --upgrade "pip>=26.2" "setuptools>=78.1.1" \
    && rm -rf /usr/local/lib/python*/ensurepip/_bundled

# Instala do LOCK com verificação de HASH (supply-chain hardening). O lock é gerado de
# requirements.txt via: uv pip compile requirements.txt --generate-hashes --python-version 3.11 \
#   --no-header -o requirements.lock   (regerar sempre que requirements.txt mudar).
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

COPY . .
RUN chown -R appuser:appuser /app
# UID numérico (hardening: permite runAsNonRoot ser verificado pelo runtime/orquestrador)
USER 10001

EXPOSE 7860

# HEALTHCHECK sem depender de curl (usa a stdlib do próprio Python). JSON/exec-form.
# Bate na rota leve /health (não re-renderiza a página inteira a cada 30s).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python","-c","import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/health',timeout=4).status==200 else 1)"]

# gunicorn serve o objeto `server` do app.py (Flask por baixo do Dash).
# --max-requests recicla workers periodicamente (mitiga vazamento de memória/estado).
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", \
     "--timeout", "60", "--graceful-timeout", "30", \
     "--max-requests", "1000", "--max-requests-jitter", "100", "app:server"]
