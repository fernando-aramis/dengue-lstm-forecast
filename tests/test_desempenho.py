# -*- coding: utf-8 -*-
"""Fase 3.3/3.5 — desempenho realizado: validação (entrada não confiável), exibição, 'em acumulação', ocultação."""
import copy
import hashlib
import json

import pytest

import atual
import dados
import figuras
import layout


def _h(n, acertos=None, **kw):
    acertos = n * 9 // 10 if acertos is None else acertos
    d = {"n": n, "acertos": acertos, "cobertura": acertos / n if n else 0, "wilson_inf": 0.8, "wilson_sup": 0.95,
         "largura_media": 30.0, "mae_lstm": 10.0, "mae_ingenuo": 12.0, "skill": 0.1667, "mae_log_lstm": 0.2,
         "mae_log_ingenuo": 0.25, "skill_log": 0.2, "mae_mediano_cidade_lstm": 3.0,
         "mae_mediano_cidade_ingenuo": 4.0, "skill_mediano_cidade": 0.25, "n_cidades": 33}
    d.update(kw)
    return d


def _bruto(n1=120, n2=40):
    return {"gerado_em": "2026-12-14T09:00:00+00:00", "criterio": {"atraso_semanas": 4, "n_min": 100},
            "por_h": {"1": _h(n1), "2": _h(n2), "3": {"n": 0}, "4": {"n": 0}},
            "snapshots_usados": ["previsoes_202643.csv"], "periodo": {"inicio": "2026-11-01", "fim": "2026-12-06"},
            "ultima_semana_observada": "2026-12-06"}


def _txt(x):
    return json.dumps(x, default=lambda o: o.to_plotly_json(), ensure_ascii=False)


def test_validar_aceita_e_saneia():
    v = dados.validar_desempenho(_bruto())
    assert v["n_min"] == 100 and v["por_h"]["1"]["n"] == 120 and v["por_h"]["3"] == {"n": 0}
    assert v["gerado_em"] == "2026-12-14" and v["periodo"]["fim"] == "2026-12-06"


@pytest.mark.parametrize("mut", [
    lambda d: d.pop("criterio"),
    lambda d: d["criterio"].update(n_min="100"),
    lambda d: d["por_h"].pop("2"),
    lambda d: d["por_h"]["1"].update(cobertura=1.5),
    lambda d: d["por_h"]["1"].update(acertos=999),
    lambda d: d["por_h"]["1"].update(mae_lstm="<script>"),
    lambda d: d["por_h"]["1"].update(mae_lstm=float("inf")),
    lambda d: d["por_h"]["1"].update(n=True),
    lambda d: d.update(gerado_em="ontem"),
])
def test_validar_rejeita_entrada_invalida(mut):
    d = copy.deepcopy(_bruto())
    mut(d)
    assert dados.validar_desempenho(d) is None


@pytest.mark.parametrize("x", [None, [], "x", 3])
def test_validar_tipos_inesperados_viram_none(x):
    assert dados.validar_desempenho(x) is None


def test_tabela_oculta_sem_dados_ou_sem_pares():
    assert layout.tabela_desempenho("pt", None) == []
    vazio = _bruto()
    for h in vazio["por_h"].values():
        h.clear()
        h["n"] = 0
    assert layout.tabela_desempenho("pt", dados.validar_desempenho(vazio)) == []
    assert figuras.nota_cobertura("pt", None) == []


def test_tabela_mostra_medido_e_em_acumulacao_por_horizonte():
    v = dados.validar_desempenho(_bruto())
    t = _txt(layout.tabela_desempenho("pt", v))
    assert "Tabela 3. " in t and "Desempenho em produção" in t and "14/12/2026" in t
    assert "90%" in t and "em acumulação (n=40; mínimo 100)" in t and "+17%" in t   # ganho com sinal explícito
    assert "correlacionadas" in t                                                   # 3.4: ressalva estatística


def test_tabela_en_es_formatam_numeros_por_idioma():
    v = dados.validar_desempenho(_bruto())
    assert "10.0" in _txt(layout.tabela_desempenho("en", v)) and "10,0" in _txt(layout.tabela_desempenho("es", v))


def test_nota_cobertura_medida_e_acumulacao():
    v = dados.validar_desempenho(_bruto())
    assert "medida no t+1: 90% (n=120, IC 80–95%)" in _txt(figuras.nota_cobertura("pt", v))
    v2 = dados.validar_desempenho(_bruto(n1=50))
    assert "em acumulação (n=50)" in _txt(figuras.nota_cobertura("pt", v2))
    assert "accumulating" in _txt(figuras.nota_cobertura("en", v2))


def test_carregar_le_desempenho_do_diretorio_e_tolera_lixo(tmp_path):
    import shutil
    for n in ("previsoes.csv", "historico.csv", "_meta.json"):
        shutil.copy(f"{dados.DATA}/{n}", tmp_path / n)
    assert dados.carregar(str(tmp_path)).desempenho is None
    (tmp_path / "desempenho.json").write_text(json.dumps(_bruto()))
    assert dados.carregar(str(tmp_path)).desempenho["por_h"]["1"]["n"] == 120
    (tmp_path / "desempenho.json").write_text("{lixo")
    assert dados.carregar(str(tmp_path)).desempenho is None


def test_original_sem_arquivo_nao_exibe_nada():
    assert dados.ORIGINAL.desempenho is None


def test_desempenho_vigente_prefere_atual_e_cai_no_original(monkeypatch):
    class _C:
        desempenho = {"x": 1}

    class _A:
        def __init__(self, c): self._c = c
        def conjunto(self): return self._c
    monkeypatch.setattr(atual, "global_atual", lambda: _A(_C()))
    assert atual.desempenho_vigente() == {"x": 1}
    monkeypatch.setattr(atual, "global_atual", lambda: _A(None))
    assert atual.desempenho_vigente() == dados.ORIGINAL.desempenho


def test_atual_carrega_desempenho_com_hash_e_ignora_divergente(monkeypatch):
    for k in ("DADOS_ATUAIS", "DADOS_ATUAIS_URL", "DADOS_ATUAIS_TESTE", "ATUAL_MAX_IDADE_SEMANAS"):
        monkeypatch.delenv(k, raising=False)
    import test_atual as ta
    corpo = json.dumps(_bruto()).encode()

    def site(hash_ok):
        s = ta._site()
        base = atual.BASE_PADRAO
        s[f"{base}runs/{ta.RUN}/desempenho.json"] = corpo
        p = json.loads(s[base + "latest.json"])
        p["sha256"]["desempenho.json"] = hashlib.sha256(corpo if hash_ok else b"x").hexdigest()
        s[base + "latest.json"] = json.dumps(p).encode()
        return s
    a = ta._mk(site(True))
    assert a.tentar() is True and a.conjunto().desempenho["por_h"]["1"]["n"] == 120
    b = ta._mk(site(False))
    assert b.tentar() is True and b.conjunto().desempenho is None


@pytest.mark.parametrize("campo", ["wilson_inf", "wilson_sup", "mae_lstm", "mae_ingenuo", "n_cidades", "acertos"])
def test_validar_rejeita_campo_obrigatorio_nulo_com_n_positivo(campo):
    d = copy.deepcopy(_bruto())
    d["por_h"]["1"][campo] = None
    assert dados.validar_desempenho(d) is None      # evitaria TypeError na renderização da página inteira
