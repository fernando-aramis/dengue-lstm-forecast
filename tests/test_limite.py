# -*- coding: utf-8 -*-
"""Limite de treino (Fase 2.2/2.2b): contrato do arquivo opcional e teto pelo pico da série completa."""
import pandas as pd
import pytest

import dados

COLS = ["geo_id", "casos_max_treino", "log1p_min_treino", "log1p_max_treino", "n_semanas_treino"]


def _lim(geo, maximo=100.0, pico=None):
    d = {"geo_id": [geo], "casos_max_treino": [maximo], "log1p_min_treino": [0.0],
         "log1p_max_treino": [4.6], "n_semanas_treino": [300]}
    if pico is not None:
        d["pico_serie_completa"] = [pico]
    return pd.DataFrame(d)


def _base():
    o = dados.ORIGINAL
    return o.prev.copy(), o.hist.copy()


def test_sem_arquivo_recurso_desligado():
    assert dados.ORIGINAL.limite in ({}, dados.ORIGINAL.limite)     # original pode ou não ter o arquivo
    prev, hist = _base()
    assert dados.carregar((prev, hist)).limite == {}


@pytest.mark.parametrize("quebra", [
    lambda d: d.drop(columns=["casos_max_treino"]),
    lambda d: d.assign(casos_max_treino=-1),
    lambda d: d.assign(casos_max_treino=float("nan")),
    lambda d: pd.concat([d, d]),
    lambda d: d.iloc[0:0],
])
def test_validar_limite_rejeita(quebra):
    with pytest.raises(RuntimeError):
        dados.validar_limite(quebra(_lim("4106902")))


def test_limite_invalido_e_ignorado_no_carregar():
    prev, hist = _base()
    c = dados.carregar((prev, hist, {}, _lim("4106902").drop(columns=["casos_max_treino"])))
    assert c.limite == {}


def test_limite_valido_entra_no_conjunto():
    prev, hist = _base()
    geo = dados.ORIGINAL.geo0
    c = dados.carregar((prev, hist, {}, _lim(geo, 123.0, pico=999)))
    assert c.limite[geo] == {"casos_max_treino": 123.0, "pico_serie_completa": 999.0}


def test_teto_usa_pico_da_serie_completa():
    prev, hist = _base()
    geo = dados.ORIGINAL.geo0
    sem = dados.carregar((prev, hist))
    prev2 = prev.copy()
    linha = (prev2["geo_id"].astype(str) == geo) & (prev2["h"] == 1)
    prev2.loc[linha, "sup"] = 10_000_000          # absurdo: sem pico completo é cortado pela janela curta
    com_pico = dados.carregar((prev2, hist, {}, _lim(geo, 10, pico=5_000_000)))
    sem_pico = dados.carregar((prev2, hist, {}, None))
    s_com = com_pico.prev.loc[com_pico.prev["geo_id"].eq(geo) & com_pico.prev["h"].eq(1), "sup"].iloc[0]
    s_sem = sem_pico.prev.loc[sem_pico.prev["geo_id"].eq(geo) & sem_pico.prev["h"].eq(1), "sup"].iloc[0]
    assert s_com > s_sem and s_com <= 5_000_000 * dados.TETO_FATOR
    assert sem.prev["sup"].le(sem.prev["sup"].max()).all()


def test_carregar_le_limite_do_diretorio(tmp_path):
    o = dados.ORIGINAL
    o.prev.to_csv(tmp_path / "previsoes.csv", index=False)
    o.hist.to_csv(tmp_path / "historico.csv", index=False)
    _lim(o.geo0, 50.0, pico=80).to_csv(tmp_path / "limite_treino.csv", index=False)
    assert dados.carregar(str(tmp_path)).limite[o.geo0]["casos_max_treino"] == 50.0
    (tmp_path / "limite_treino.csv").write_text("lixo\n1,2\n")
    assert dados.carregar(str(tmp_path)).limite == {}
