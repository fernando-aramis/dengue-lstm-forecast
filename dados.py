# -*- coding: utf-8 -*-
"""
Carga e preparação dos dados que o app LÊ (CSV/GeoJSON) + globais derivados.

O app não treina nem chama a API: só lê os artefatos pré-computados pelo pipeline
(ver webapp/pipeline/). Este módulo centraliza a leitura e os objetos que o layout,
as figuras e os callbacks consomem.
"""
import json
import os
from datetime import date, timedelta

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

# ---- níveis de alerta (aqui, não em figuras.py, para derivar RESUMO sem import circular) --------
CORES_NIVEL = {"Verde": "#2e9e5b", "Amarelo": "#d9a404", "Laranja": "#ef7d2d", "Vermelho": "#d6364c"}
ORDEM_NIVEL = ["Verde", "Amarelo", "Laranja", "Vermelho"]


# ---- derivados de APRESENTAÇÃO (F3): semana epidemiológica + resumo da situação -----------------
def semana_epi(d):
    """Semana epidemiológica (SINAN/MMWR): semanas domingo–sábado; a SE 1 é a 1ª com ≥ 4 dias no ano.
    Retorna (ano_epi, semana)."""
    def inicio(ano):
        j4 = date(ano, 1, 4)
        return j4 - timedelta(days=(j4.weekday() + 1) % 7)   # domingo <= 4/jan
    ano = d.year
    if d < inicio(ano):
        ano -= 1
    elif d >= inicio(ano + 1):
        ano += 1
    return ano, (d - inicio(ano)).days // 7 + 1


SE_ORIGEM = semana_epi(prev["data_origem"].max().date())          # (ano, semana) da origem
DATA_PREV_H1 = mapa_cid["data_prev"].min().date()                 # data da previsão t+1
SE_H1 = semana_epi(DATA_PREV_H1)                                   # SE da próxima semana
RESUMO = {
    "total_h1": int(mapa_cid["prev"].sum()),
    "n_cidades": int(len(mapa_cid)),
    "por_nivel": {nv: int((mapa_cid["nivel_alerta"] == nv).sum()) for nv in ORDEM_NIVEL},
}
