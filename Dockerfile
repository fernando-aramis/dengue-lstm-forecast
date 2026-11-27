# Imagem do app Dash para qualquer host de container (Render, Fly.io, etc.).
# A porta é configurável por $PORT (default 7860): o host injeta PORT e o app se vincula a ele.
# Base pinada por DIGEST (reprodutível + controle de quando a base muda).
# python:3.11-slim (Debian 13/trixie) — digest resolvido em 2026-11-09.
# Para re-pinar no futuro: docker pull python:3.11-slim && \
#   docker inspect --format '{{index .RepoDigests 0}}' python:3.11-slim
FROM python:3.11-slim@sha256:61e01f72680f86a5279ad510818ab7b2ee9f049822589d4e34e33e044360356c

# Security updates do Debian no build (fecha CVEs HIGH/CRITICAL corrigíveis da base).
RUN apt-get update && apt-get -y upgrade \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# usuário não-root (hardening: não rodar o container como root)
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

# Um único RUN (menos camadas, sem duplicar arquivos entre elas):
#  1) pip/setuptools atualizados só para instalar (corrige CVE-2024-6345, CVE-2025-47273, etc.);
#  2) instala do LOCK com verificação de HASH (supply-chain hardening). O lock é gerado de
#     requirements.txt via: uv pip compile requirements.txt --generate-hashes --python-version 3.11 \
#       --no-header -o requirements.lock   (regerar sempre que requirements.txt mudar);
#  3) remove o que o serving não usa: suítes de teste embutidas nos wheels do pandas/numpy,
#     e pip/setuptools/wheel (ferramentas de build) + wheels do ensurepip (só `python -m venv`) —
#     reduz tamanho e superfície de ataque. Mantém os __pycache__ (cold start).
COPY requirements.lock .
RUN pip install --no-cache-dir --upgrade "pip>=26.2" "setuptools>=78.1.1" \
    && pip install --no-cache-dir --require-hashes -r requirements.lock \
    && find /usr/local/lib/python3.11/site-packages/pandas /usr/local/lib/python3.11/site-packages/numpy \
         -type d \( -name tests -o -name test \) -prune -exec rm -rf {} + \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python*/ensurepip/_bundled

# --chown no COPY: evita o `chown -R` numa camada nova (que duplicaria o /app inteiro).
COPY --chown=10001:10001 . .
# UID numérico (hardening: permite runAsNonRoot ser verificado pelo runtime/orquestrador)
USER 10001

EXPOSE 7860

# HEALTHCHECK sem depender de curl (usa a stdlib do próprio Python). Lê $PORT (default 7860).
# Bate na rota leve /health (não re-renderiza a página inteira a cada 30s).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python","-c","import os,urllib.request,sys;p=os.environ.get('PORT','7860');sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+p+'/health',timeout=4).status==200 else 1)"]

# gunicorn serve o objeto `server` do app.py (Flask por baixo do Dash).
# --max-requests recicla workers periodicamente (mitiga vazamento de memória/estado).
# Shell-form com exec p/ expandir $PORT (host injeta) e $WEB_CONCURRENCY (workers; default 1: estado "atual" é por worker).
# exec => gunicorn vira PID 1 e recebe os sinais corretamente.
CMD exec gunicorn --bind "0.0.0.0:${PORT:-7860}" --workers "${WEB_CONCURRENCY:-1}" \
    --timeout 60 --graceful-timeout 30 --max-requests 1000 --max-requests-jitter 100 app:server
