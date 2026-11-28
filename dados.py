# -*- coding: utf-8 -*-
"""
Carga e preparação dos dados que o app LÊ (CSV/GeoJSON) + globais derivados.

O app não treina nem chama a API: só lê os artefatos pré-computados pelo pipeline
(ver webapp/pipeline/). Este módulo centraliza a leitura e os objetos que o layout,
as figuras e os callbacks consomem.
"""
import json
import os
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")

TETO_FATOR = 3.0   # teto defensivo do limite superior: sup <= fator × pico local (ver modelo.py)

with open(os.path.join(DATA, "br_uf.geojson"), encoding="utf-8") as f:
    GEOJSON_UF = json.load(f)

# ---- constantes que NÃO dependem do dataset (ficam globais) --------------------------------------
# níveis de alerta (aqui, não em figuras.py, para derivar RESUMO sem import circular)
CORES_NIVEL = {"Verde": "#2e9e5b", "Amarelo": "#d9a404", "Laranja": "#ef7d2d", "Vermelho": "#d6364c"}
# Paleta alternativa para daltonismo (opt-in via menu de acessibilidade). Medida por simulação de Machado
# et al. (2009, severidade 1,0) e distância ΔE76 em CIELAB, pior par entre os 4 níveis (tests/test_unit.py):
#   protanopia   — padrão 17,4 (Amarelo/Laranja) → CVD 26,9 (Verde/Laranja)
#   deuteranopia — padrão 10,1 (Verde/Vermelho)  → CVD 11,6 (Verde/Vermelho)
# Ou seja: melhora clara em protanopia e ganho pequeno em deuteranopia, onde Verde/Vermelho continuam
# próximos — por isso a COR NUNCA é o único canal (glifo + rótulo + anel de espessura + Tabela 1).
CORES_NIVEL_CVD = {"Verde": "#2E8B57", "Amarelo": "#F5D800", "Laranja": "#D9641E", "Vermelho": "#B3203F"}
ORDEM_NIVEL = ["Verde", "Amarelo", "Laranja", "Vermelho"]

if not GEOJSON_UF.get("features"):
    raise RuntimeError("[dados] contrato inválido: br_uf.geojson sem 'features'")
nome_uf = {f["properties"]["sigla"]: f["properties"]["name"] for f in GEOJSON_UF["features"]}
UFS = sorted(nome_uf)


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


# ---- contrato de dados: falha-rápido com mensagem clara ----------------------------------------
# Uma falha no refresh semanal (ex.: API do InfoDengue fora do ar) não deve virar um IndexError/NaT
# opaco no boot do gunicorn — derruba explícito, dizendo QUAL arquivo e O QUÊ está faltando.
_COLS_PREV = {"nivel_geo", "geo_id", "uf", "nome", "lat", "lon",
              "data_origem", "h", "data_prev", "prev", "inf", "sup", "nivel_alerta"}
_COLS_HIST = {"nivel_geo", "geo_id", "uf", "nome", "lat", "lon", "data", "casos"}


_COLS_LIMITE = {"geo_id", "casos_max_treino", "log1p_min_treino", "log1p_max_treino", "n_semanas_treino"}


def _exigir(cond, msg):
    if not cond:
        raise RuntimeError(f"[dados] contrato inválido: {msg}")


def validar(prev, hist):
    """Valida o contrato de previsoes/historico (função pura; levanta RuntimeError com a causa).
    Reutilizada para o dataset original (disco) e o atual (rede)."""
    _exigir(not prev.empty, "previsoes.csv está vazio")
    _exigir(not hist.empty, "historico.csv está vazio")
    _exigir(_COLS_PREV.issubset(prev.columns),
            f"colunas faltando em previsoes.csv: {sorted(_COLS_PREV - set(prev.columns))}")
    _exigir(_COLS_HIST.issubset(hist.columns),
            f"colunas faltando em historico.csv: {sorted(_COLS_HIST - set(hist.columns))}")
    _exigir(prev["nivel_alerta"].isin(ORDEM_NIVEL).all(),
            "previsoes.csv: nivel_alerta fora de " + str(ORDEM_NIVEL))   # nível inesperado sumiria do mapa
    _exigir(prev[["prev", "inf", "sup"]].notna().all().all(),
            "previsoes.csv: prev/inf/sup com valores ausentes")
    _exigir(((prev["nivel_geo"] == "municipio") & (prev["h"] == 1)).any(),
            "nenhuma linha municipio/h==1 em previsoes.csv (mapa ficaria vazio)")


def validar_limite(lim):
    """Valida `limite_treino.csv` (opcional; função pura; levanta RuntimeError com a causa)."""
    _exigir(not lim.empty, "limite_treino.csv está vazio")
    _exigir(_COLS_LIMITE.issubset(lim.columns),
            f"colunas faltando em limite_treino.csv: {sorted(_COLS_LIMITE - set(lim.columns))}")
    num = [c for c in _COLS_LIMITE | {"pico_serie_completa"} if c != "geo_id" and c in lim.columns]
    _exigir(lim[num].notna().all().all() and (lim[num].select_dtypes("number").shape[1] == len(num)),
            "limite_treino.csv: valores ausentes ou não numéricos")
    _exigir((lim["casos_max_treino"] >= 0).all(), "limite_treino.csv: casos_max_treino negativo")
    _exigir(not lim["geo_id"].astype(str).duplicated().any(), "limite_treino.csv: geo_id duplicado")


def _dict_limite(lim):
    """geo_id → {casos_max_treino, pico_serie_completa|None}; DataFrame inválido/None vira {} (recurso desligado)."""
    if lim is None:
        return {}
    try:
        validar_limite(lim)
    except RuntimeError:
        return {}
    tem_pico = "pico_serie_completa" in lim.columns
    return {str(g): {"casos_max_treino": float(c), "pico_serie_completa": float(p) if tem_pico else None}
            for g, c, p in zip(lim["geo_id"], lim["casos_max_treino"],
                               lim["pico_serie_completa"] if tem_pico else [None] * len(lim))}


@dataclass(frozen=True, eq=False)
class Conjunto:
    """Tudo que depende dos CSVs, imutável. O app escolhe um (original ou atual) por requisição."""
    prev: pd.DataFrame
    hist: pd.DataFrame
    mapa_cid: pd.DataFrame
    mapa_uf: pd.DataFrame
    cidades_por_uf: dict
    nome_por_geo: dict
    cobertas: set
    nao_cobertas: list
    idx_choropleth: int          # índice do traço choropleth estadual na figura (0, ou 1 se há "sem cobertura")
    geo0: str                    # seleção inicial
    data_origem: str
    se_origem: tuple
    data_prev_h1: date
    se_h1: tuple
    resumo: dict
    meta: dict
    limite: dict = None          # geo_id → limite de treino (opcional; {} = recurso desligado)


def carregar(origem):
    """Constrói um Conjunto a partir de um diretório (com previsoes.csv, historico.csv e _meta.json
    opcional, limite_treino.csv opcional) ou de uma tupla (prev_df, hist_df[, meta_dict[, limite_df]]).
    Valida o contrato; um limite_treino inválido é ignorado (recurso opcional desligado)."""
    if isinstance(origem, (str, os.PathLike)):
        hist = pd.read_csv(os.path.join(origem, "historico.csv"), parse_dates=["data"])
        prev = pd.read_csv(os.path.join(origem, "previsoes.csv"), parse_dates=["data_origem", "data_prev"])
        meta = {}
        try:   # proveniência gravada pelo pipeline (ausência é tolerada — ex.: dados antigos)
            with open(os.path.join(origem, "_meta.json"), encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            pass
        try:
            lim = pd.read_csv(os.path.join(origem, "limite_treino.csv"), dtype={"geo_id": str})
        except (OSError, ValueError, pd.errors.ParserError):
            lim = None
    else:
        prev, hist, *resto = origem
        meta = resto[0] if resto else {}
        lim = resto[1] if len(resto) > 1 else None
        prev, hist = prev.copy(), hist.copy()
    if not isinstance(meta, dict):           # JSON válido porém não-objeto (ex.: []) → tolera como ausente
        meta = {}
    validar(prev, hist)
    for d in (hist, prev):
        d["geo_id"] = d["geo_id"].astype(str)

    # guarda de escala: limita sup ao pico histórico local × fator (protege CSVs já gravados e picos
    # fora da faixa de treino, em que o expm1 do intervalo pode disparar e quebrar o eixo do gráfico).
    limite = _dict_limite(lim)
    pico = hist.groupby("geo_id")["casos"].max()
    # 2.2b: o pico da SÉRIE COMPLETA (exportado pelo pipeline) substitui o da janela curta quando existe
    completo = {g: v["pico_serie_completa"] for g, v in limite.items() if v["pico_serie_completa"] is not None}
    if completo:
        pico = pico.combine(pd.Series(completo, dtype=float), lambda a, b: max(a, b), fill_value=0)
    base = np.maximum(prev["geo_id"].map(pico).fillna(0).to_numpy(), prev["prev"].to_numpy())
    prev["sup"] = np.minimum(prev["sup"].to_numpy(), np.maximum(1.0, base) * TETO_FATOR)
    prev["sup"] = prev[["sup", "prev"]].max(axis=1)     # sup >= prev
    prev["inf"] = prev[["inf", "prev"]].min(axis=1)     # inf <= prev

    mapa_cid = prev[(prev["h"] == 1) & (prev["nivel_geo"] == "municipio")].copy()   # bolhas
    mapa_uf = prev[(prev["h"] == 1) & (prev["nivel_geo"] == "estado")].copy()        # choropleth
    cobertas = set(mapa_uf["uf"])                    # UFs com pelo menos uma cidade monitorada
    nao_cobertas = [u for u in nome_uf if u not in cobertas]
    return Conjunto(
        prev=prev, hist=hist, mapa_cid=mapa_cid, mapa_uf=mapa_uf,
        cidades_por_uf=(mapa_cid.sort_values("nome").groupby("uf")[["nome", "geo_id"]]
                        .apply(lambda d: list(zip(d["nome"], d["geo_id"]))).to_dict()),
        nome_por_geo=dict(zip(prev["geo_id"], prev["nome"])),
        cobertas=cobertas, nao_cobertas=nao_cobertas,
        idx_choropleth=1 if nao_cobertas else 0,
        geo0=mapa_cid.sort_values("prev", ascending=False)["geo_id"].iloc[0],
        data_origem=prev["data_origem"].max().date().isoformat(),
        se_origem=semana_epi(prev["data_origem"].max().date()),     # (ano, semana) da origem
        data_prev_h1=mapa_cid["data_prev"].min().date(),            # data da previsão t+1
        se_h1=semana_epi(mapa_cid["data_prev"].min().date()),       # SE da próxima semana
        resumo={
            "total_h1": int(mapa_cid["prev"].sum()),
            "n_cidades": int(len(mapa_cid)),
            "por_nivel": {nv: int((mapa_cid["nivel_alerta"] == nv).sum()) for nv in ORDEM_NIVEL},
        },
        meta=meta, limite=limite,
    )


ORIGINAL = carregar(DATA)      # fail-fast no import, como antes
