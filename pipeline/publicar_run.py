# -*- coding: utf-8 -*-
"""Publicação consistente na branch `data` (Fase 1.2): run imutável + ponteiro `latest.json` POR ÚLTIMO.

Uso (no CI, com a branch `data` em um worktree):
    python publicar_run.py <DATA_DIR da saída do pipeline> <worktree da branch data> [commit_sha]

Layout gerado em <worktree>:
    runs/AAAASS-<sha7>/{previsoes.csv,historico.csv,_meta.json,eda.json}
    snapshots/previsoes_AAAASS.csv
    latest.json   {run, se_origem, sha256{arquivo: hash}}   <- escrito por último (ponteiro atômico)

O app lê o ponteiro e depois os arquivos do run apontado, conferindo os hashes: nunca combina arquivos
de execuções diferentes, mesmo com cache de CDN.
"""
import hashlib
import json
import os
import shutil
import sys

import pandas as pd

OBRIGATORIOS = ("previsoes.csv", "historico.csv", "_meta.json")
OPCIONAIS = ("eda.json",)


def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def nome_run(se_origem, commit):
    """AAAASS-<sha7> a partir da data de origem (semana ISO, igual aos snapshots) e do commit."""
    ano, semana, _ = pd.Timestamp(se_origem).isocalendar()
    sha7 = (commit or "0000000")[:7].lower()
    if len(sha7) < 7 or any(ch not in "0123456789abcdef" for ch in sha7):
        sha7 = "0000000"
    return f"{ano}{int(semana):02d}-{sha7}", f"{ano}{int(semana):02d}"


def publicar(data_dir, destino, commit=None):
    for n in OBRIGATORIOS:
        if not os.path.isfile(os.path.join(data_dir, n)):
            raise SystemExit(f"arquivo obrigatório ausente em {data_dir}: {n}")
    with open(os.path.join(data_dir, "_meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    se_origem = str(meta["se_origem"])[:10]
    run, aaaass = nome_run(se_origem, commit or meta.get("commit") or os.environ.get("GITHUB_SHA"))
    pasta = os.path.join(destino, "runs", run)
    os.makedirs(pasta, exist_ok=True)
    hashes = {}
    for n in OBRIGATORIOS + OPCIONAIS:
        src = os.path.join(data_dir, n)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(pasta, n))
            hashes[n] = _sha256(src)
    snap = os.path.join(data_dir, "snapshots", f"previsoes_{aaaass}.csv")
    if os.path.isfile(snap):
        os.makedirs(os.path.join(destino, "snapshots"), exist_ok=True)
        shutil.copyfile(snap, os.path.join(destino, "snapshots", f"previsoes_{aaaass}.csv"))
    # ponteiro por ÚLTIMO, via arquivo temporário + rename (nunca meio escrito)
    ptr = {"run": run, "se_origem": se_origem, "sha256": hashes}
    tmp = os.path.join(destino, "latest.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ptr, f, ensure_ascii=False, indent=2)
    os.replace(tmp, os.path.join(destino, "latest.json"))
    return run


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    print(publicar(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
