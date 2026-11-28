# -*- coding: utf-8 -*-
"""atual.py (Fase 1.8): máquina de estados com fetcher injetável — sem rede real."""
import hashlib
import json
import os
import threading
from datetime import date, timedelta

import pandas as pd
import pytest

import atual
import dados

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RUN = "202646-abc1234"


def _bruto(nome):
    return open(os.path.join(DATA, nome), "rb").read()


def _site(prev=None, hist=None, meta=None, ptr=None, run=RUN):
    """Dicionário url→bytes de um 'site' com latest.json + run, hashes corretos."""
    arqs = {"previsoes.csv": _bruto("previsoes.csv") if prev is None else prev,
            "historico.csv": _bruto("historico.csv") if hist is None else hist,
            "_meta.json": _bruto("_meta.json") if meta is None else meta}
    base = atual.BASE_PADRAO
    site = {f"{base}runs/{run}/{n}": b for n, b in arqs.items()}
    p = {"run": run, "se_origem": 46, "sha256": {n: hashlib.sha256(b).hexdigest() for n, b in arqs.items()}}
    site[base + "latest.json"] = json.dumps(ptr or p).encode()
    return site


def _fetcher(site, log=None):
    def f(url, etag=None):
        if log is not None:
            log.append((url, etag))
        v = site.get(url)
        if isinstance(v, Exception):
            raise v
        if v is None:
            raise atual.ErroAtual("HTTP 404")
        return 200, v, '"e1"'
    return f


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for k in ("DADOS_ATUAIS", "DADOS_ATUAIS_URL", "DADOS_ATUAIS_TESTE", "ATUAL_MAX_IDADE_SEMANAS"):
        monkeypatch.delenv(k, raising=False)


def _mk(site, hoje=None):
    return atual.Atual(fetcher=_fetcher(site), hoje=hoje or dados.ORIGINAL.data_prev_h1)


def test_import_nao_dispara_rede_nem_thread():
    assert not any(t.name == "atual" for t in threading.enumerate())
    assert atual._GLOBAL is None or atual._GLOBAL._thread is None


def test_estado_inicial_carregando():
    assert _mk({}).estado()["estado"] == atual.CARREGANDO


def test_disponivel_com_run_valido():
    a = _mk(_site())
    assert a.tentar() is True
    e = a.estado()
    assert e["estado"] == atual.DISPONIVEL and e["run"] == RUN and e["motivo"] is None
    assert a.conjunto().data_origem == dados.ORIGINAL.data_origem


def test_defasado_quando_velho():
    a = _mk(_site(), hoje=date.fromisoformat(dados.ORIGINAL.data_origem) + timedelta(weeks=5))
    a.tentar()
    assert a.estado()["estado"] == atual.DEFASADO and a.conjunto() is not None


def test_limite_de_idade_por_env(monkeypatch):
    monkeypatch.setenv("ATUAL_MAX_IDADE_SEMANAS", "10")
    a = _mk(_site(), hoje=date.fromisoformat(dados.ORIGINAL.data_origem) + timedelta(weeks=5))
    a.tentar()
    assert a.estado()["estado"] == atual.DISPONIVEL


@pytest.mark.parametrize("site,trecho", [
    ({}, "404"),
    ({atual.BASE_PADRAO + "latest.json": b"nao e json"}, "latest.json inválido"),
    ({atual.BASE_PADRAO + "latest.json": b"[]"}, "latest.json inválido"),
    ({atual.BASE_PADRAO + "latest.json": json.dumps({"run": "../x", "sha256": {}}).encode()}, "run válido"),
    ({atual.BASE_PADRAO + "latest.json": atual.ErroAtual("rede indisponível")}, "rede"),
])
def test_indisponivel_por_falha_de_busca(site, trecho):
    a = _mk(site)
    assert a.tentar() is False
    e = a.estado()
    assert e["estado"] == atual.INDISPONIVEL and trecho in e["motivo"]
    assert a.conjunto() is None


def test_hash_divergente_rejeita():
    s = _site()
    s[f"{atual.BASE_PADRAO}runs/{RUN}/previsoes.csv"] += b"\n"
    a = _mk(s)
    assert a.tentar() is False and "hash" in a.estado()["motivo"]


def test_csv_invalido_e_contrato_invalido():
    a = _mk(_site(prev=b"a,b\n1,2\n"))
    assert a.tentar() is False and a.estado()["motivo"] == "CSV inválido"
    ruim = _bruto("previsoes.csv").replace(b"Verde", b"Roxo").replace(b"Laranja", b"Roxo")
    a = _mk(_site(prev=ruim))
    assert a.tentar() is False and "nivel_alerta" in a.estado()["motivo"]
    a = _mk(_site(prev=b""))
    assert a.tentar() is False and a.estado()["estado"] == atual.INDISPONIVEL


def test_anterior_ao_original_e_rejeitado():
    import pandas as pd
    p = pd.read_csv(os.path.join(DATA, "previsoes.csv"), parse_dates=["data_origem", "data_prev"])
    p["data_origem"] -= pd.Timedelta(weeks=1)
    meta = json.loads(_bruto("_meta.json"))
    meta.pop("se_origem", None)
    a = _mk(_site(prev=p.to_csv(index=False).encode(), meta=json.dumps(meta).encode()))
    assert a.tentar() is False and "anterior ao original" in a.estado()["motivo"]


def test_se_origem_do_meta_divergente():
    meta = json.loads(_bruto("_meta.json"))
    meta["se_origem"] = "2020-01-05"
    a = _mk(_site(meta=json.dumps(meta).encode()))
    assert a.tentar() is False and "diverge" in a.estado()["motivo"]


def test_mantem_ultimo_bom_apos_falha():
    s = _site()
    a = _mk(s)
    assert a.tentar() is True
    s[atual.BASE_PADRAO + "latest.json"] = b"lixo"
    assert a.tentar() is False
    assert a.estado()["estado"] == atual.DISPONIVEL and a.conjunto() is not None


def test_etag_enviado_e_304_preserva_estado():
    log = []
    s = _site()
    a = atual.Atual(fetcher=_fetcher(s, log), hoje=dados.ORIGINAL.data_prev_h1)
    a.tentar()
    a._fetch = lambda url, etag=None: (304, None, etag)
    assert a.tentar() is True and a.estado()["estado"] == atual.DISPONIVEL
    assert log[0][1] is None


def test_run_rejeitado_nao_envenena_o_etag():
    log = []
    ruim = _site(prev=_bruto("previsoes.csv")[:100])        # hash confere, CSV inválido
    a = atual.Atual(fetcher=_fetcher(ruim, log), hoje=dados.ORIGINAL.data_prev_h1)
    assert a.tentar() is False and a._etag is None
    a._fetch = _fetcher(_site(), log)
    assert a.tentar() is True and a.estado()["estado"] == atual.DISPONIVEL
    assert log[-4][1] is None      # a 2ª tentativa reenviou latest.json sem If-None-Match


def test_excecao_inesperada_vira_falha_e_nao_mata_o_laco(monkeypatch):
    a = _mk(_site())
    monkeypatch.setattr(atual, "montar", lambda *x: (_ for _ in ()).throw(KeyError("x")))
    assert a.tentar() is False
    e = a.estado()
    assert e["estado"] == atual.INDISPONIVEL and e["motivo"] == "erro inesperado"


def test_kill_switch(monkeypatch):
    monkeypatch.setenv("DADOS_ATUAIS", "0")
    chamadas = []
    a = atual.Atual(fetcher=_fetcher(_site(), chamadas))
    assert a.estado()["estado"] == atual.INDISPONIVEL and a.estado()["motivo"] == "desligado"
    assert a.tentar() is True and chamadas == [] and a.iniciar() is False


@pytest.mark.parametrize("url,esperado_padrao", [
    ("https://evil.example.com/x/", True),
    ("http://raw.githubusercontent.com/x/", True),       # http externo
    ("file:///etc/passwd", True),
    ("http://127.0.0.1:9/", True),                        # loopback sem DADOS_ATUAIS_TESTE
    ("https://raw.githubusercontent.com/o/r/data/", True),       # outro repositório do mesmo host
    ("https://raw.githubusercontent.com/fernando-aramis/dengue-lstm-forecast/teste/", False),
])
def test_allowlist_de_url(monkeypatch, url, esperado_padrao):
    monkeypatch.setenv("DADOS_ATUAIS_URL", url)
    assert (atual.url_base() == atual.BASE_PADRAO) is esperado_padrao


def test_loopback_so_com_flag_de_teste(monkeypatch):
    monkeypatch.setenv("DADOS_ATUAIS_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("DADOS_ATUAIS_TESTE", "1")
    assert atual.url_base() == "http://127.0.0.1:9999/"


def test_sem_redirecionamento():
    assert atual._SemRedirect().redirect_request(None, None, 302, "", {}, "http://x") is None


def test_laco_backoff_e_recheck():
    esperas = []

    class _Parar(Exception):
        pass

    def dormir(s):
        esperas.append(s)
        if len(esperas) >= 6:
            raise _Parar

    a = atual.Atual(fetcher=_fetcher({}), dormir=dormir)
    with pytest.raises(_Parar):
        a._laco()
    assert esperas == [15, 60, 300, atual.RECHECAGEM_S, atual.RECHECAGEM_S, atual.RECHECAGEM_S]


def test_iniciar_e_idempotente(monkeypatch):
    monkeypatch.setattr(atual.Atual, "_laco", lambda self: threading.Event().wait(0.3))
    a = atual.Atual(fetcher=_fetcher({}))
    assert a.iniciar() is True and a.iniciar() is False


def _com_limite(corpo, hash_ok=True):
    s = _site()
    base = atual.BASE_PADRAO
    s[f"{base}runs/{RUN}/limite_treino.csv"] = corpo
    p = json.loads(s[base + "latest.json"])
    p["sha256"]["limite_treino.csv"] = hashlib.sha256(corpo if hash_ok else b"x").hexdigest()
    s[base + "latest.json"] = json.dumps(p).encode()
    return s


def test_limite_opcional_e_carregado_quando_o_hash_confere():
    geo = dados.ORIGINAL.geo0
    csv = (f"geo_id,casos_max_treino,log1p_min_treino,log1p_max_treino,n_semanas_treino,pico_serie_completa\n"
           f"{geo},100,0,4.6,300,150\n").encode()
    a = _mk(_com_limite(csv))
    assert a.tentar() is True
    assert a.conjunto().limite[geo]["pico_serie_completa"] == 150.0


def test_limite_com_hash_divergente_desliga_so_o_recurso():
    a = _mk(_com_limite(b"geo_id\n1\n", hash_ok=False))
    assert a.tentar() is True and a.conjunto().limite == {}


def test_limite_listado_mas_ausente_nao_derruba_o_run():
    s = _com_limite(b"x")
    del s[f"{atual.BASE_PADRAO}runs/{RUN}/limite_treino.csv"]       # o fetcher de teste levanta ErroAtual (404)
    a = _mk(s)
    assert a.tentar() is True and a.conjunto().limite == {}


def test_limite_ilegivel_nao_derruba_o_run():
    a = _mk(_com_limite(b"\xff\xfe lixo"))
    assert a.tentar() is True and a.conjunto().limite == {}


def _com_anterior(corpo, hash_ok=True):
    s = _site()
    base = atual.BASE_PADRAO
    s[f"{base}runs/{RUN}/previsoes_anterior.csv"] = corpo
    p = json.loads(s[base + "latest.json"])
    p["sha256"]["previsoes_anterior.csv"] = hashlib.sha256(corpo if hash_ok else b"x").hexdigest()
    s[base + "latest.json"] = json.dumps(p).encode()
    return s


def _csv_anterior():
    a = dados.ORIGINAL.prev.copy()
    for col in ("data_origem", "data_prev"):
        a[col] = (a[col] - pd.Timedelta(days=7)).dt.strftime("%Y-%m-%d")
    return a.to_csv(index=False).encode()


def test_anterior_opcional_e_carregado_quando_o_hash_confere():
    a = _mk(_com_anterior(_csv_anterior()))
    assert a.tentar() is True and a.conjunto().anterior is not None


@pytest.mark.parametrize("corpo,hash_ok", [(b"\xff\xfe lixo", True), (_csv_anterior(), False)])
def test_anterior_invalido_ou_divergente_desliga_so_o_recurso(corpo, hash_ok):
    a = _mk(_com_anterior(corpo, hash_ok))
    assert a.tentar() is True and a.conjunto().anterior is None
