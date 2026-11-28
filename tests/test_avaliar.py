# -*- coding: utf-8 -*-
"""Fase 3.1/3.5 — avaliar.py: sintético com acertos/erros conhecidos, sem vazamento, atraso, Wilson."""
import json
import math

import avaliar
import pandas as pd
import pytest


def _hist(n_sem=12, geos=("1", "2"), base=100):
    datas = pd.date_range("2026-01-04", periods=n_sem, freq="7D")
    return pd.DataFrame([{"nivel_geo": "municipio", "geo_id": g, "data": d, "casos": base}
                         for g in geos for d in datas])


def _snap(origem, geos=("1", "2"), prev=100, inf=90, sup=110):
    o = pd.Timestamp(origem)
    return pd.DataFrame([{"nivel_geo": "municipio", "geo_id": g, "data_origem": o, "h": h,
                          "data_prev": o + pd.Timedelta(weeks=h), "prev": prev, "inf": inf, "sup": sup}
                         for g in geos for h in (1, 2, 3, 4)])


def test_wilson_valores_de_referencia():
    lo, hi = avaliar.wilson(90, 100)          # referência: 0,8256 – 0,9448
    assert lo == pytest.approx(0.8256, abs=1e-3) and hi == pytest.approx(0.9448, abs=1e-3)
    assert avaliar.wilson(0, 0) == (None, None)
    lo, hi = avaliar.wilson(10, 10)
    assert hi == pytest.approx(1.0) and lo == pytest.approx(0.7225, abs=1e-3)


def test_acertos_erros_e_skill_conhecidos():
    h = _hist()                                # observado = 100 sempre; última semana 2026-03-22
    s = _snap("2026-01-11", prev=100, inf=90, sup=110)
    s.loc[s["geo_id"] == "2", ["inf", "sup"]] = [200, 300]       # cidade 2 sempre erra o intervalo
    r = avaliar.avaliar([s], h, n_min=1)
    h1 = r["por_h"]["1"]
    assert h1["n"] == 2 and h1["acertos"] == 1 and h1["cobertura"] == 0.5
    assert h1["mae_lstm"] == 0 and h1["mae_ingenuo"] == 0 and h1["skill"] is None   # ingênuo perfeito: skill indefinida
    assert h1["largura_media"] == pytest.approx((20 + 100) / 2)


def test_skill_positiva_quando_modelo_supera_ingenuo():
    h = _hist()
    h.loc[(h["data"] == pd.Timestamp("2026-01-11")), "casos"] = 50     # valor em O = 50; observado nos alvos = 100
    r = avaliar.avaliar([_snap("2026-01-11", prev=95)], h)
    h1 = r["por_h"]["1"]
    assert h1["mae_lstm"] == 5 and h1["mae_ingenuo"] == 50
    assert h1["skill"] == pytest.approx(0.9) and h1["skill_mediano_cidade"] == pytest.approx(0.9)
    assert h1["skill_log"] is not None and h1["skill_log"] > 0


def test_atraso_de_4_semanas_respeitado():
    h = _hist(n_sem=12)                        # última = 2026-03-22 → corte 2026-02-22
    r = avaliar.avaliar([_snap("2026-02-15")], h)      # alvos 02-22 (ok), 03-01, 03-08, 03-15 (imaturos)
    assert r["por_h"]["1"]["n"] == 2
    for k in ("2", "3", "4"):
        assert r["por_h"][k] == {"n": 0}
    assert r["ultima_semana_observada"] == "2026-03-22"


def test_sem_vazamento_alvo_nao_posterior_a_origem_e_descartado():
    h = _hist()
    s = _snap("2026-01-25")
    s["data_prev"] = s["data_origem"] - pd.Timedelta(weeks=1)      # alvo ANTERIOR à origem: inválido
    r = avaliar.avaliar([s], h)
    assert all(v == {"n": 0} for v in r["por_h"].values())


def test_snapshot_duplicado_conta_uma_vez_e_estados_sao_ignorados():
    h = _hist()
    s = _snap("2026-01-11")
    est = s.copy()
    est["nivel_geo"] = "estado"
    r = avaliar.avaliar([s, s, est], h)
    assert r["por_h"]["1"]["n"] == 2


def test_sem_dados_observados_nao_gera_par():
    h = _hist(geos=("9",))                     # nenhum geo em comum
    r = avaliar.avaliar([_snap("2026-01-11")], h)
    assert all(v == {"n": 0} for v in r["por_h"].values()) and r["periodo"] is None


def test_main_grava_json_valido(tmp_path):
    (tmp_path / "snaps").mkdir()
    _snap("2026-01-11").to_csv(tmp_path / "snaps" / "previsoes_202603.csv", index=False)
    (tmp_path / "snaps" / "previsoes_lixo.csv").write_text("")      # vazio: ignorado com aviso
    _hist().to_csv(tmp_path / "h.csv", index=False)
    avaliar.main(str(tmp_path / "snaps"), str(tmp_path / "h.csv"), str(tmp_path / "d.json"))
    d = json.load(open(tmp_path / "d.json", encoding="utf-8"))
    assert d["criterio"] == {"atraso_semanas": 4, "n_min": 100} and d["snapshots_usados"] == ["previsoes_202603.csv"]
    assert not any(isinstance(v, float) and math.isnan(v) for g in d["por_h"].values() for v in g.values())
