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
    assert dados.ORIGINAL.limite == {}      # o original ainda não traz limite_treino.csv (1.4c pendente)
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
    assert (s_sem < 10_000_000) and sem.prev["sup"].ge(sem.prev["prev"]).all()      # sem pico completo, o guard corta


def test_carregar_le_limite_do_diretorio(tmp_path):
    o = dados.ORIGINAL
    o.prev.to_csv(tmp_path / "previsoes.csv", index=False)
    o.hist.to_csv(tmp_path / "historico.csv", index=False)
    _lim(o.geo0, 50.0, pico=80).to_csv(tmp_path / "limite_treino.csv", index=False)
    assert dados.carregar(str(tmp_path)).limite[o.geo0]["casos_max_treino"] == 50.0
    (tmp_path / "limite_treino.csv").write_text("lixo\n1,2\n")
    assert dados.carregar(str(tmp_path)).limite == {}


# ---- 2.1 ingênuo -------------------------------------------------------------------------------
def test_ingenuo_e_o_ultimo_observado_repetido():
    import figuras
    c = dados.ORIGINAL
    for geo in (c.geo0, "UF-" + c.mapa_uf["uf"].iloc[0]):
        fig = figuras.figura_detalhe(geo, c=c)
        tr_ = [t for t in fig.data if t.name and t.name.endswith("(última semana repetida)")]
        assert len(tr_) == 1, geo
        h = c.hist[c.hist["geo_id"] == geo].sort_values("data")
        pv = c.prev[c.prev["geo_id"] == geo].sort_values("h")
        assert list(tr_[0].y) == [h["casos"].iloc[-1]] * (len(pv) + 1)
        assert list(tr_[0].x)[1:] == list(pv["data_prev"])
        assert tr_[0].line.dash == "dashdot"          # canal além da cor


def test_ingenuo_contraste_grafico_3_para_1():
    from test_unit import contraste

    import figuras
    for tema in ("light", "dark"):
        p = figuras.PLOT[tema]
        assert contraste(p["naive"], p["paper"]) >= 3.0, tema


# ---- 2.3 aviso "fora do limite de treino" -------------------------------------------------------
def _com_limite_em(geo, maximo):
    o = dados.ORIGINAL
    return dados.carregar((o.prev.copy(), o.hist.copy(), {}, _lim(geo, maximo)))


def _vals(geo):
    o = dados.ORIGINAL
    obs = o.hist[o.hist["geo_id"] == geo].sort_values("data")["casos"].iloc[-1]
    prev = o.mapa_cid[o.mapa_cid["geo_id"] == geo]["prev"].iloc[0]
    return float(obs), float(prev)


def test_fora_limite_regra_dos_dois_gatilhos_e_igualdade():
    geo = dados.ORIGINAL.geo0
    obs, prev = _vals(geo)
    assert dados.fora_limite(dados.ORIGINAL, geo) is None                              # sem arquivo: sem aviso
    c = _com_limite_em(geo, max(obs, prev) + 1)
    assert dados.fora_limite(c, geo) is None                                # abaixo: sem aviso
    assert dados.fora_limite(_com_limite_em(geo, max(obs, prev)), geo) is None   # igual ao limite NÃO sinaliza
    if obs != prev:
        alto, baixo = max(obs, prev), min(obs, prev)
        r = dados.fora_limite(_com_limite_em(geo, (alto + baixo) / 2 if alto - baixo > 1 else baixo - 0.5), geo)
        assert r == ("obs" if obs > prev else "prev")
    assert dados.fora_limite(_com_limite_em(geo, min(obs, prev) - 1), geo) == "ambos"


def test_fora_limite_ignora_uf_e_geo_sem_limite():
    c = _com_limite_em(dados.ORIGINAL.geo0, 0.0)
    uf = "UF-" + dados.ORIGINAL.mapa_uf["uf"].iloc[0]
    assert dados.fora_limite(c, uf) is None
    outro = next(g for g in dados.ORIGINAL.mapa_cid["geo_id"] if g != dados.ORIGINAL.geo0)
    assert dados.fora_limite(c, outro) is None


@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_aviso_aparece_no_cartao_tabela_e_anuncio(lang):
    import figuras
    import layout
    from i18n import tr
    geo = dados.ORIGINAL.geo0
    c = _com_limite_em(geo, 0.0)                       # força: tudo acima do limite
    assert "aviso-limite" in str(figuras.cartao_info(geo, lang, c=c))
    assert tr(lang, "aviso_limite") in figuras.resumo_cartao(geo, lang, c=c)
    tab = str(layout.tabela_ranking(lang, c=c))
    assert "atencao" in tab and tr(lang, "aviso_limite_tab") in tab and tr(lang, "aviso_limite_nota") in tab
    # sem arquivo/aviso: nada disso aparece
    sem = dados.carregar((dados.ORIGINAL.prev.copy(), dados.ORIGINAL.hist.copy()))
    assert "aviso-limite" not in str(figuras.cartao_info(geo, lang, c=sem))
    assert "atencao" not in str(layout.tabela_ranking(lang, c=sem))


def test_pico_invalido_nao_desliga_o_aviso():
    geo = dados.ORIGINAL.geo0
    lim = _lim(geo, 5.0, pico=float("nan"))
    c = dados.carregar((dados.ORIGINAL.prev.copy(), dados.ORIGINAL.hist.copy(), {}, lim))
    assert c.limite[geo] == {"casos_max_treino": 5.0, "pico_serie_completa": None}


def test_aviso_nao_gera_lista_aninhada():
    from test_unit import _coleta_listas_aninhadas

    import figuras
    import layout
    geo = dados.ORIGINAL.geo0
    c = _com_limite_em(geo, 0.0)
    hits = _coleta_listas_aninhadas(figuras.cartao_info(geo, "pt", c=c))
    hits += _coleta_listas_aninhadas(layout.tabela_ranking("pt", c=c))
    hits += _coleta_listas_aninhadas(figuras.horizontes(geo, "pt", c=c))
    assert hits == []
