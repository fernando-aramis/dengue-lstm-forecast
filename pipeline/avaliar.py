# -*- coding: utf-8 -*-
"""Fase 3.1 — desempenho REALIZADO das previsões já publicadas (sem TensorFlow; só pandas/numpy).

Uso (no CI, ANTES de publicar o run, para o arquivo entrar no `latest.json` com hash):
    python avaliar.py <snapshots_dir> <historico.csv do run novo> <saida desempenho.json> [snapshot_novo.csv ...]

Para cada (origem O, horizonte h, alvo T = data_prev, município) avalia SOMENTE se T já está consolidado:
T <= última_semana_observada − ATRASO_SEMANAS (4). O observado é `casos` do historico.csv (casos estimados/
nowcast, a mesma série que alimenta o modelo). Baseline ingênuo: o valor observado em O repetido.
Métricas por horizonte: n, acertos, cobertura + IC de Wilson 95%, largura média, MAE (LSTM e ingênuo) em casos
e em log1p, MAE mediano por cidade (o MAE absoluto agregado é dominado por cidades grandes) e skill = 1 − MAE/MAE_ingênuo.
Limitação declarada: o IC de Wilson supõe independência, mas as cidades são correlacionadas (intervalo otimista).
Os snapshots guardam o `sup` bruto do pipeline (o app pode limitá-lo na exibição).
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ATRASO_SEMANAS = 4
N_MIN = 100
Z95 = 1.959963984540054


def wilson(k, n, z=Z95):
    """IC de Wilson para uma proporção k/n → (inferior, superior); n=0 → (None, None)."""
    if n <= 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    meia = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(max(0.0, centro - meia)), float(min(1.0, centro + meia))


def _num(x):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else float(x)


def _skill(mae, mae_ing):
    return None if not mae_ing else float(1 - mae / mae_ing)


def pares(snapshots, hist, atraso=ATRASO_SEMANAS):
    """DataFrame de pares avaliáveis (um por origem×município×h). `snapshots`: iterável de DataFrames de
    previsoes.csv (municípios); `hist`: historico.csv. Sem vazamento: exige data_prev > data_origem."""
    h = hist[hist["nivel_geo"] == "municipio"].copy()
    h["geo_id"] = h["geo_id"].astype(str)
    h["data"] = pd.to_datetime(h["data"])
    ultima = h["data"].max()
    corte = ultima - pd.Timedelta(weeks=atraso)
    obs = h.set_index(["geo_id", "data"])["casos"]
    partes = []
    for s in snapshots:
        s = s[s["nivel_geo"] == "municipio"].copy()
        s["geo_id"] = s["geo_id"].astype(str)
        s["data_origem"] = pd.to_datetime(s["data_origem"])
        s["data_prev"] = pd.to_datetime(s["data_prev"])
        partes.append(s)
    if not partes:
        return pd.DataFrame(), ultima
    p = pd.concat(partes, ignore_index=True).drop_duplicates(["geo_id", "data_origem", "h"], keep="last")
    p = p[(p["data_prev"] > p["data_origem"]) & (p["data_prev"] <= corte)]
    idx_t = pd.MultiIndex.from_arrays([p["geo_id"], p["data_prev"]])
    idx_o = pd.MultiIndex.from_arrays([p["geo_id"], p["data_origem"]])
    p = p.assign(obs=obs.reindex(idx_t).to_numpy(), ing=obs.reindex(idx_o).to_numpy())
    return p.dropna(subset=["obs", "ing"]).reset_index(drop=True), ultima


def avaliar(snapshots, hist, atraso=ATRASO_SEMANAS, n_min=N_MIN, usados=None, agora=None):
    p, ultima = pares(snapshots, hist, atraso)
    por_h = {}
    for hh in (1, 2, 3, 4):
        q = p[p["h"] == hh] if len(p) else p
        n = int(len(q))
        if n == 0:
            por_h[str(hh)] = {"n": 0}
            continue
        acertos = int(((q["inf"] <= q["obs"]) & (q["obs"] <= q["sup"])).sum())
        lo, hi = wilson(acertos, n)
        e = (q["prev"] - q["obs"]).abs()
        ei = (q["ing"] - q["obs"]).abs()
        el = (np.log1p(q["prev"].clip(lower=0)) - np.log1p(q["obs"].clip(lower=0))).abs()
        eli = (np.log1p(q["ing"].clip(lower=0)) - np.log1p(q["obs"].clip(lower=0))).abs()
        por_cid = pd.DataFrame({"g": q["geo_id"], "e": e, "ei": ei}).groupby("g").mean()
        mm, mmi = float(por_cid["e"].median()), float(por_cid["ei"].median())
        por_h[str(hh)] = {
            "n": n, "acertos": acertos, "cobertura": acertos / n, "wilson_inf": lo, "wilson_sup": hi,
            "largura_media": _num((q["sup"] - q["inf"]).mean()),
            "mae_lstm": _num(e.mean()), "mae_ingenuo": _num(ei.mean()),
            "skill": _skill(e.mean(), ei.mean()),
            "mae_log_lstm": _num(el.mean()), "mae_log_ingenuo": _num(eli.mean()),
            "skill_log": _skill(el.mean(), eli.mean()),
            "mae_mediano_cidade_lstm": _num(mm), "mae_mediano_cidade_ingenuo": _num(mmi),
            "skill_mediano_cidade": _skill(mm, mmi), "n_cidades": int(len(por_cid))}
    periodo = None
    if len(p):
        periodo = {"inicio": p["data_prev"].min().date().isoformat(), "fim": p["data_prev"].max().date().isoformat()}
    return {"gerado_em": (agora or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
            "criterio": {"atraso_semanas": atraso, "n_min": n_min},
            "por_h": por_h, "snapshots_usados": sorted(usados or []), "periodo": periodo,
            "ultima_semana_observada": ultima.date().isoformat()}


def main(snaps_dir, hist_csv, saida, extras=()):
    arquivos = sorted(glob.glob(os.path.join(snaps_dir, "previsoes_*.csv"))) + list(extras)
    dfs, usados = [], []
    for a in arquivos:
        try:
            dfs.append(pd.read_csv(a, dtype={"geo_id": str}))
            usados.append(os.path.basename(a))
        except (OSError, ValueError, pd.errors.ParserError) as e:   # um snapshot ruim não derruba a avaliação
            print(f"aviso: snapshot ignorado {a}: {e}", file=sys.stderr)
    res = avaliar(dfs, pd.read_csv(hist_csv, dtype={"geo_id": str}), usados=usados)
    tmp = saida + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    os.replace(tmp, saida)          # nunca publica um JSON meio escrito
    print(f"desempenho: {sum(v.get('n', 0) for v in res['por_h'].values())} pares avaliados → {saida}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
