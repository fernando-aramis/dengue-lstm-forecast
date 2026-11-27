# -*- coding: utf-8 -*-
"""Config do gunicorn (carregada automaticamente do diretório de trabalho, /app na imagem).

Inicia a thread do dataset "atual" em CADA worker depois do fork (threads não sobrevivem ao fork,
por isso NÃO usar --preload). O estado vive em memória por processo: no Render free tier o
`render.yaml` fixa WEB_CONCURRENCY=1 (o default da imagem é 2: cada worker busca por conta própria,
mitigado por ETag). Nunca bloqueia o boot nem o /health.
"""


def post_worker_init(worker):
    import atual
    atual.global_atual().iniciar()
