# -*- coding: utf-8 -*-
"""Probe barato (Fase 1.2): decide se vale treinar, comparando a SE mais recente de uma cidade-sentinela
no InfoDengue com a `se_origem` do último `latest.json` publicado na branch `data`.

Uso: python probe.py [caminho/latest.json]   → imprime `treinar=true|false` (e grava em $GITHUB_OUTPUT).
Sem ponteiro anterior, ou se a consulta falhar, devolve `true` (o pipeline tem suas próprias tentativas
e, se falhar, o job vermelho abre a issue de alerta — nunca pular em silêncio).
"""
import json
import os
import sys
from datetime import date

import infodengue

SENTINELA = 4106902   # Curitiba


def precisa_treinar(origem_api, origem_publicada):
    """True se não há run publicado ou se a API já tem uma semana mais nova que a publicada."""
    if not origem_publicada:
        return True
    if not origem_api:
        return True
    return str(origem_api)[:10] > str(origem_publicada)[:10]


def origem_api(geocode=SENTINELA):
    """Data da última semana epidemiológica disponível (mesma regra do pipeline: max das datas)."""
    df = infodengue.buscar_cidade(geocode, ey_start=date.today().year - 1)
    return df["date"].max().date().isoformat()


def ler_publicada(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return str(json.load(f).get("se_origem") or "")[:10] or None
    except (OSError, ValueError, AttributeError):
        return None


def main(argv):
    publicada = ler_publicada(argv[1]) if len(argv) > 1 else None
    try:
        api = origem_api()
    except Exception as e:   # noqa: BLE001 — qualquer falha de consulta ⇒ treinar (ver docstring)
        print(f"probe: consulta falhou ({type(e).__name__}); treinando por segurança", file=sys.stderr)
        api = None
    treinar = precisa_treinar(api, publicada)
    print(f"probe: api={api} publicada={publicada} -> treinar={str(treinar).lower()}")
    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a", encoding="utf-8") as f:
            f.write(f"treinar={str(treinar).lower()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
