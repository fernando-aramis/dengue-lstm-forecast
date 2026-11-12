# -*- coding: utf-8 -*-
"""
PIPELINE REAL (offline). Para cada cidade coberta:
  InfoDengue (casos)  ->  EDA + preparação (replicando a planilha)  ->  LSTM A + conformal
  ->  previsão das próximas 4 semanas com intervalo de 90%.
Agrega o fallback estadual e grava data/historico.csv, data/previsoes.csv e data/eda.json,
no MESMO schema do gerador de exemplo — o app Dash não muda.

Requer TensorFlow:  pip install tensorflow-cpu   (ou rode no Colab, como o estudo original).
Rode:  python gerar_previsoes_reais.py            (knobs via variáveis de ambiente abaixo)

Env opcionais:
  CIDADES_GEO="4106902,3550308"  -> só esses geocodes (teste rápido)
  MAX_CIDADES=5                  -> limita a quantidade
  MODO_RAPIDO=1                  -> menos épocas/paciência (demonstração)
  EY_START=2014                  -> ano inicial da coleta
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from cidades import CIDADES, UF_NOME
import infodengue
import preparacao
import modelo
import _log

log = _log.configurar("dengue.pipeline")

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "..", "data")
os.makedirs(DATA, exist_ok=True)

HIST_SEMANAS = 20
EY_START = int(os.environ.get("EY_START", 2014))
RAPIDO = os.environ.get("MODO_RAPIDO") == "1"
EPOCAS, PACIENCIA = (120, 12) if RAPIDO else (500, 30)
PREFETCH_WORKERS = int(os.environ.get("PIPELINE_PREFETCH_WORKERS", "6"))   # paralelismo só da COLETA


def nivel_alerta(casos_semana, pop):
    inc = casos_semana / max(pop, 1) * 100_000
    if inc < 2.5:
        return "Verde"
    if inc < 10:
        return "Amarelo"
    if inc < 30:
        return "Laranja"
    return "Vermelho"


def _lista_cidades():
    geo_env = os.environ.get("CIDADES_GEO")
    cids = CIDADES
    if geo_env:
        alvo = {int(g) for g in geo_env.split(",")}
        cids = [c for c in cids if c[2] in alvo]
    if os.environ.get("MAX_CIDADES"):
        cids = cids[:int(os.environ["MAX_CIDADES"])]
    return cids


def processar_cidade(nome, uf, geocode, lat, lon, pop_aprox):
    df = infodengue.buscar_cidade(geocode, ey_start=EY_START)
    resumo = preparacao.eda(df)
    s, params = preparacao.preparar(df)                 # usa nowcast (casos_est)
    previsao, meta = modelo.treinar_prever(s, params, epocas=EPOCAS, paciencia=PACIENCIA)
    pop = int(df["pop"].dropna().iloc[-1]) if "pop" in df and df["pop"].notna().any() else pop_aprox

    hist_rows = []
    sub = s.tail(HIST_SEMANAS)
    for _, r in sub.iterrows():
        hist_rows.append(["municipio", str(geocode), uf, nome, lat, lon,
                          r["date"].date().isoformat(), int(r["casos"])])

    origem = meta["data_origem"].date().isoformat()
    prev_rows = []
    for p in previsao:
        prev_rows.append(["municipio", str(geocode), uf, nome, lat, lon, origem,
                          p["h"], pd.Timestamp(p["data_prev"]).date().isoformat(),
                          round(p["prev"]), round(p["inf"]), round(p["sup"]),
                          nivel_alerta(p["prev"], pop)])
    return hist_rows, prev_rows, pop, resumo


def agregar_estados(por_uf, hist_rows, prev_rows):
    """Fallback estadual: soma as cidades cobertas de cada UF (passo do gerador de exemplo)."""
    for uf, cidades in por_uf.items():
        pop_uf = sum(c["pop"] for c in cidades)
        lat_uf = float(np.mean([c["lat"] for c in cidades]))
        lon_uf = float(np.mean([c["lon"] for c in cidades]))
        geo_uf, nome_u = f"UF-{uf}", UF_NOME[uf]

        soma_h = {}
        for c in cidades:
            for row in c["hist"]:
                soma_h[row[6]] = soma_h.get(row[6], 0) + row[7]
        for d, v in sorted(soma_h.items()):
            hist_rows.append(["estado", geo_uf, uf, nome_u, lat_uf, lon_uf, d, v])

        soma_p = {}
        for c in cidades:
            for row in c["prev"]:
                h = row[7]
                a = soma_p.setdefault(h, {"data": row[8], "prev": 0, "inf": 0, "sup": 0})
                a["prev"] += row[9]; a["inf"] += row[10]; a["sup"] += row[11]
        origem_uf = cidades[0]["prev"][0][6]        # origem é a mesma p/ todas as cidades da UF
        for h in sorted(soma_p):
            a = soma_p[h]
            prev_rows.append(["estado", geo_uf, uf, nome_u, lat_uf, lon_uf,
                              origem_uf, h, a["data"], a["prev"], a["inf"], a["sup"],
                              nivel_alerta(a["prev"], pop_uf)])


def main():
    cidades = _lista_cidades()
    print(f"Processando {len(cidades)} cidade(s) · EY_START={EY_START} · "
          f"{'rápido' if RAPIDO else 'completo'}")
    hist_rows, prev_rows, por_uf, edas, falhas = [], [], {}, {}, []

    # WS9: coleta (I/O) em PARALELO → popula o cache do infodengue; o treino (TF) segue SEQUENCIAL.
    # Com o cache, as chamadas de buscar_cidade dentro do loop viram cache-hit (não rebatem na API).
    if infodengue.CACHE_ON and len(cidades) > 1:
        geocodes = [c[2] for c in cidades]
        print(f"  Pré-buscando {len(geocodes)} cidade(s) em paralelo ({PREFETCH_WORKERS} workers, cache)…")

        def _prefetch(g):
            try:
                infodengue.buscar_cidade(g, ey_start=EY_START)
            except Exception as e:                       # noqa: BLE001  (não-fatal: o loop re-tenta)
                log.warning("prefetch falhou p/ %s: %s", g, e)

        with ThreadPoolExecutor(max_workers=PREFETCH_WORKERS) as ex:
            list(ex.map(_prefetch, geocodes))

    for i, (nome, uf, geocode, lat, lon, pop_aprox) in enumerate(cidades, 1):
        try:
            hr, pr, pop, resumo = processar_cidade(nome, uf, geocode, lat, lon, pop_aprox)
            hist_rows += hr
            prev_rows += pr
            por_uf.setdefault(uf, []).append({"lat": lat, "lon": lon, "pop": pop, "hist": hr, "prev": pr})
            edas[str(geocode)] = {"cidade": nome, "uf": uf, **resumo}
            print(f"  [{i}/{len(cidades)}] {nome}/{uf}: ok "
                  f"(próx. semana ~{pr[0][9]} casos, {pr[0][12]})")
        except Exception as e:                           # noqa: BLE001
            falhas.append((nome, uf, str(e)))
            print(f"  [{i}/{len(cidades)}] {nome}/{uf}: FALHOU — {e}")

    if not prev_rows:
        raise SystemExit("Nenhuma cidade processada. Verifique a rede/TensorFlow.")

    agregar_estados(por_uf, hist_rows, prev_rows)

    df_prev = pd.DataFrame(prev_rows, columns=["nivel_geo", "geo_id", "uf", "nome", "lat", "lon",
                                               "data_origem", "h", "data_prev", "prev", "inf", "sup",
                                               "nivel_alerta"])
    pd.DataFrame(hist_rows, columns=["nivel_geo", "geo_id", "uf", "nome", "lat", "lon",
                                     "data", "casos"]).to_csv(
        os.path.join(DATA, "historico.csv"), index=False)
    df_prev.to_csv(os.path.join(DATA, "previsoes.csv"), index=False)
    with open(os.path.join(DATA, "eda.json"), "w", encoding="utf-8") as f:
        json.dump(edas, f, ensure_ascii=False, indent=2)

    # proveniência + snapshot datado (habilita auditoria e backtesting; não sobrescreve o histórico)
    origem = str(df_prev["data_origem"].iloc[0])
    ano, semana, _ = pd.Timestamp(origem).isocalendar()
    snaps = os.path.join(DATA, "snapshots")
    os.makedirs(snaps, exist_ok=True)
    df_prev.to_csv(os.path.join(snaps, f"previsoes_{ano}{int(semana):02d}.csv"), index=False)
    meta = {"coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "se_origem": origem, "modelo": "LSTM A univariada (conformal 90%)",
            "modo": "rápido" if RAPIDO else "completo",
            "n_cidades": len(edas), "n_falhas": len(falhas), "versao": 1}
    with open(os.path.join(DATA, "_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    log.info("OK: %d cidades, %d falhas. CSVs + snapshot %s%02d + _meta.json gravados em data/.",
             len(edas), len(falhas), ano, int(semana))
    if falhas:
        log.warning("Falhas: %s", falhas)


if __name__ == "__main__":
    main()
