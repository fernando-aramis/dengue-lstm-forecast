# -*- coding: utf-8 -*-
"""Caminho de import comum: qualquer arquivo de teste roda isolado (`pytest tests/test_formato.py`)."""
import os
import sys

_WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_WEBAPP, os.path.join(_WEBAPP, "pipeline")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Fase 1: testes nunca buscam o dataset "atual" na rede (o app só liga isso com DADOS_ATUAIS=1).
os.environ.setdefault("DADOS_ATUAIS", "0")
