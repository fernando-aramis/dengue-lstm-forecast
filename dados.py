# -*- coding: utf-8 -*-
"""
Carga e preparação dos dados que o app LÊ (CSV/GeoJSON) + globais derivados.

O app não treina nem chama a API: só lê os artefatos pré-computados pelo pipeline
(ver webapp/pipeline/). Este módulo centraliza a leitura e os objetos que o layout,
as figuras e os callbacks consomem.
"""
import json
import os

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")

TETO_FATOR = 3.0   # teto defensivo do limite superior: sup <= fator × pico local (ver modelo.py)

hist = pd.read_csv(os.path.join(DATA, "historico.csv"), parse_dates=["data"])
prev = pd.read_csv(os.path.join(DATA, "previsoes.csv"), parse_dates=["data_origem", "data_prev"])
with open(os.path.join(DATA, "br_uf.geojson"), encoding="utf-8") as f:
    GEOJSON_UF = json.load(f)


# ---- contrato de dados: falha-rápido com mensagem clara ----------------------------------------
# Uma falha no refresh semanal (ex.: API do InfoDengue fora do ar) não deve virar um IndexError/NaT
# opaco no boot do gunicorn — derruba explícito, dizendo QUAL arquivo e O QUÊ está faltando.
_COLS_PREV = {"nivel_geo", "geo_id", "uf", "nome", "lat", "lon",
              "data_origem", "h", "data_prev", "prev", "inf", "sup", "nivel_alerta"}
_COLS_HIST = {"nivel_geo", "geo_id", "uf", "nome", "lat", "lon", "data", "casos"}


def _exigir(cond, msg):
    if not cond:
        raise RuntimeError(f"[dados] contrato inválido: {msg}")


_exigir(not prev.empty, "data/previsoes.csv está vazio")
_exigir(not hist.empty, "data/historico.csv está vazio")
_exigir(_COLS_PREV.issubset(prev.columns),
        f"colunas faltando em previsoes.csv: {sorted(_COLS_PREV - set(prev.columns))}")
_exigir(_COLS_HIST.issubset(hist.columns),
        f"colunas faltando em historico.csv: {sorted(_COLS_HIST - set(hist.columns))}")
_exigir(bool(GEOJSON_UF.get("features")), "br_uf.geojson sem 'features'")

for _d in (hist, prev):
    _d["geo_id"] = _d["geo_id"].astype(str)

# guarda de escala: limita sup ao pico histórico local × fator (protege CSVs já gravados e picos
# fora da faixa de treino, em que o expm1 do intervalo pode disparar e quebrar o eixo do gráfico).
_pico = hist.groupby("geo_id")["casos"].max()
_base = np.maximum(prev["geo_id"].map(_pico).fillna(0).to_numpy(), prev["prev"].to_numpy())
prev["sup"] = np.minimum(prev["sup"].to_numpy(), np.maximum(1.0, _base) * TETO_FATOR)
prev["sup"] = prev[["sup", "prev"]].max(axis=1)     # sup >= prev
prev["inf"] = prev[["inf", "prev"]].min(axis=1)     # inf <= prev

DATA_ORIGEM = prev["data_origem"].max().date().isoformat()

# proveniência gravada pelo pipeline (ausência é tolerada — ex.: dados antigos)
try:
    with open(os.path.join(DATA, "_meta.json"), encoding="utf-8") as f:
        META = json.load(f)
except (OSError, ValueError):
    META = {}

mapa_cid = prev[(prev["h"] == 1) & (prev["nivel_geo"] == "municipio")].copy()   # bolhas
mapa_uf = prev[(prev["h"] == 1) & (prev["nivel_geo"] == "estado")].copy()        # choropleth
_exigir(not mapa_cid.empty, "nenhuma linha municipio/h==1 em previsoes.csv (mapa ficaria vazio)")
GEO0 = mapa_cid.sort_values("prev", ascending=False)["geo_id"].iloc[0]           # seleção inicial

nome_uf = {f["properties"]["sigla"]: f["properties"]["name"] for f in GEOJSON_UF["features"]}
UFS = sorted(nome_uf)
COBERTAS = set(mapa_uf["uf"])                   # UFs com pelo menos uma cidade monitorada
NAO_COBERTAS = [u for u in nome_uf if u not in COBERTAS]
# índice do traço choropleth estadual na figura (0, ou 1 se houver a camada "sem cobertura")
IDX_CHOROPLETH = 1 if NAO_COBERTAS else 0
cidades_por_uf = (mapa_cid.sort_values("nome").groupby("uf")[["nome", "geo_id"]]
                  .apply(lambda d: list(zip(d["nome"], d["geo_id"]))).to_dict())
nome_por_geo = dict(zip(prev["geo_id"], prev["nome"]))
