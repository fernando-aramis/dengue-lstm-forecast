# -*- coding: utf-8 -*-
"""P.3 'o que mudou desde a última previsão': carregamento, alvos em comum, publicação e UI."""
import hashlib
import json
import os
import shutil

import pandas as pd
import pytest

import dados
import figuras
import publicar_run

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(AQUI), "data")


def _anterior(dias=7, delta=10):
    """Previsão 'da semana anterior': origem e alvos deslocados -7 dias; prev = atual + delta."""
    cur = dados.ORIGINAL.prev
    a = cur.copy()
    a["data_origem"] = a["data_origem"] - pd.Timedelta(days=dias)
    a["data_prev"] = a["data_prev"] - pd.Timedelta(days=dias)
    # nos alvos em comum, o valor "antes" = valor atual − delta (assim o delta esperado é conhecido)
    ref = cur.set_index(["geo_id", "data_prev"])["prev"]
    chave = pd.MultiIndex.from_arrays([a["geo_id"].astype(str), a["data_prev"]])
    a["prev"] = ref.reindex(chave).fillna(pd.Series(a["prev"].to_numpy(), index=chave)).to_numpy() - delta
    a["inf"] = a["prev"] - 5
    a["sup"] = a["prev"] + 5
    return a


def _txt(x):
    return json.dumps(x, default=lambda o: o.to_plotly_json(), ensure_ascii=False)


def _conj(ant):
    o = dados.ORIGINAL
    return dados.carregar((o.prev.copy(), o.hist.copy(), dict(o.meta), None, ant))


def test_sem_anterior_recurso_oculto():
    assert dados.ORIGINAL.anterior is None
    assert dados.mudancas(dados.ORIGINAL, dados.ORIGINAL.geo0) is None
    assert figuras.bloco_mudancas(dados.ORIGINAL.geo0) == []


def test_alvos_em_comum_sao_tres_para_origens_consecutivas():
    c = _conj(_anterior())
    m = dados.mudancas(c, c.geo0)
    assert len(m["linhas"]) == 3                                    # 4 alvos, deslocados 1 semana → 3 em comum
    assert all(l["delta"] == 10 for l in m["linhas"])
    assert [l["h"] for l in m["linhas"]] == [1, 2, 3]               # h da previsão ATUAL


def test_intervalo_sem_alvo_em_comum_oculta():
    c = _conj(_anterior(dias=28))
    assert dados.mudancas(c, c.geo0) is None


@pytest.mark.parametrize("mut", [
    lambda a: a.assign(data_origem=a["data_origem"] + pd.Timedelta(days=14)),   # origem NÃO anterior
    lambda a: a.drop(columns=["sup"]),                                         # schema incompleto
    lambda a: a.iloc[0:0],
    lambda a: a.assign(prev=float("nan")),
])
def test_anterior_invalido_desliga_o_recurso(mut):
    assert _conj(mut(_anterior())).anterior is None


def test_ui_texto_neutro_com_sentido_por_extenso():
    c = _conj(_anterior())
    html = _txt(figuras.horizontes(c.geo0, "pt", None, c))
    assert "O que mudou desde a previsão anterior" in html and "subiu 10" in html and "nowcast" in html
    en = _txt(figuras.horizontes(c.geo0, "en", None, c))
    assert "rose by 10" in en
    c2 = _conj(_anterior(delta=-5))
    assert "caiu 5" in _txt(figuras.horizontes(c2.geo0, "pt", None, c2))
    c3 = _conj(_anterior(delta=0))
    assert "sem mudança" in _txt(figuras.horizontes(c3.geo0, "pt", None, c3))


def test_carregar_le_previsoes_anterior_do_diretorio(tmp_path):
    for n in ("previsoes.csv", "historico.csv", "_meta.json"):
        shutil.copy(os.path.join(DATA, n), tmp_path / n)
    _anterior().to_csv(tmp_path / "previsoes_anterior.csv", index=False)
    assert dados.carregar(str(tmp_path)).anterior is not None
    (tmp_path / "previsoes_anterior.csv").write_text("lixo\n1\n")
    assert dados.carregar(str(tmp_path)).anterior is None


def _saida(tmp_path, nome, origem):
    d = tmp_path / nome
    d.mkdir()
    for n in ("previsoes.csv", "historico.csv", "_meta.json"):
        shutil.copy(os.path.join(DATA, n), d / n)
    meta = json.load(open(d / "_meta.json", encoding="utf-8"))
    meta["se_origem"] = origem
    json.dump(meta, open(d / "_meta.json", "w", encoding="utf-8"))
    return str(d)


def test_publicar_inclui_previsoes_anterior_com_hash(tmp_path):
    destino = tmp_path / "data"
    destino.mkdir()
    run1 = publicar_run.publicar(_saida(tmp_path, "s1", "2026-11-08"), str(destino), commit="aaaaaaa")
    ptr1 = json.load(open(destino / "latest.json", encoding="utf-8"))
    assert "previsoes_anterior.csv" not in ptr1["sha256"]           # primeira execução: nada anterior
    publicar_run.publicar(_saida(tmp_path, "s2", "2026-11-15"), str(destino), commit="bbbbbbb")
    ptr2 = json.load(open(destino / "latest.json", encoding="utf-8"))
    corpo = (destino / "runs" / ptr2["run"] / "previsoes_anterior.csv").read_bytes()
    assert corpo == (destino / "runs" / run1 / "previsoes.csv").read_bytes()
    assert hashlib.sha256(corpo).hexdigest() == ptr2["sha256"]["previsoes_anterior.csv"]


def test_publicar_mesma_origem_nao_cria_anterior(tmp_path):
    destino = tmp_path / "data"
    destino.mkdir()
    publicar_run.publicar(_saida(tmp_path, "s1", "2026-11-15"), str(destino), commit="aaaaaaa")
    publicar_run.publicar(_saida(tmp_path, "s2", "2026-11-15"), str(destino), commit="bbbbbbb")
    assert "previsoes_anterior.csv" not in json.load(open(destino / "latest.json", encoding="utf-8"))["sha256"]
