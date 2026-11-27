# -*- coding: utf-8 -*-
"""Conjunto/validar/carregar (Fase 1.5–1.6): contrato puro, sem navegador e sem rede."""
import dataclasses

import pandas as pd
import pytest

import dados


def _dfs():
    o = dados.ORIGINAL
    return o.prev.copy(), o.hist.copy()


def test_carregar_por_dfs_equivale_ao_original():
    prev, hist = _dfs()
    c = dados.carregar((prev, hist, dict(dados.ORIGINAL.meta)))
    o = dados.ORIGINAL
    for campo in ("geo0", "data_origem", "se_origem", "se_h1", "data_prev_h1", "resumo",
                  "cidades_por_uf", "nome_por_geo", "cobertas", "nao_cobertas", "idx_choropleth"):
        assert getattr(c, campo) == getattr(o, campo), campo
    pd.testing.assert_frame_equal(c.prev.reset_index(drop=True), o.prev.reset_index(drop=True))
    pd.testing.assert_frame_equal(c.mapa_cid, o.mapa_cid)


def test_aliases_do_modulo_apontam_para_o_original():
    o = dados.ORIGINAL
    assert dados.prev is o.prev and dados.GEO0 == o.geo0 and dados.SE_ORIGEM == o.se_origem
    assert dados.RESUMO is o.resumo and dados.IDX_CHOROPLETH == o.idx_choropleth


def test_conjunto_e_imutavel():
    with pytest.raises(dataclasses.FrozenInstanceError):
        dados.ORIGINAL.geo0 = "x"


def test_carregar_nao_altera_os_dfs_de_entrada():
    prev, hist = _dfs()
    antes = prev["sup"].copy()
    dados.carregar((prev, hist))
    pd.testing.assert_series_equal(prev["sup"], antes)


@pytest.mark.parametrize("mutar,trecho", [
    (lambda p, h: (p.iloc[0:0], h), "vazio"),
    (lambda p, h: (p, h.iloc[0:0]), "vazio"),
    (lambda p, h: (p.drop(columns=["sup"]), h), "colunas faltando"),
    (lambda p, h: (p, h.drop(columns=["casos"])), "colunas faltando"),
    (lambda p, h: (p.assign(nivel_alerta="Roxo"), h), "nivel_alerta"),
    (lambda p, h: (p.assign(prev=float("nan")), h), "ausentes"),
    (lambda p, h: (p[p["nivel_geo"] != "municipio"], h), "municipio"),
])
def test_validar_rejeita(mutar, trecho):
    p, h = mutar(*_dfs())
    with pytest.raises(RuntimeError, match=trecho):
        dados.validar(p, h)
