# -*- coding: utf-8 -*-
"""Logging padrão do pipeline (stdlib, sem dependência externa). Nível via LOG_LEVEL."""
import logging
import os

_CONFIG = False


def configurar(nome="dengue.pipeline"):
    global _CONFIG
    if not _CONFIG:
        logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                            format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        _CONFIG = True
    return logging.getLogger(nome)
