# -*- coding: utf-8 -*-
"""E2E da fonte dos dados (Fase 1.9–1.11): seletor Original × Atual com o dataset atual INJETADO
(sem rede). O servidor roda no mesmo processo, então `atual._GLOBAL` é trocado direto."""
import json
import os
import socket
import threading
import time

import pandas as pd
import pytest
from test_atual import DATA, _bruto, _fetcher, _site

import atual
import dados

PORT = 8078
URL = f"http://127.0.0.1:{PORT}/"
CURITIBA = "4106902"


def _site_novo():
    """Atual = original deslocado +1 semana e SEM Curitiba (testa o fallback da seleção)."""
    p = pd.read_csv(os.path.join(DATA, "previsoes.csv"), parse_dates=["data_origem", "data_prev"])
    p["data_origem"] += pd.Timedelta(weeks=1)
    p["data_prev"] += pd.Timedelta(weeks=1)
    p = p[p["geo_id"].astype(str) != CURITIBA]
    meta = json.loads(_bruto("_meta.json"))
    meta["se_origem"] = p["data_origem"].max().date().isoformat()
    return _site(prev=p.to_csv(index=False).encode(), meta=json.dumps(meta).encode()), meta["se_origem"]


@pytest.fixture(scope="module")
def servidor():
    from werkzeug.serving import make_server
    os.environ["DADOS_ATUAIS"] = "1"
    import app as A
    srv = make_server("127.0.0.1", PORT, A.server, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", PORT), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield URL
    srv.shutdown()
    os.environ["DADOS_ATUAIS"] = "0"
    atual._GLOBAL = None


def _instala(site):
    a = atual.Atual(fetcher=_fetcher(site), hoje=dados.ORIGINAL.data_prev_h1)
    a._thread, a._pid = threading.current_thread(), os.getpid()      # impede a thread de fundo
    atual._GLOBAL = a
    return a


@pytest.fixture()
def pagina(servidor):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_context(locale="pt-BR", viewport={"width": 1200, "height": 900}).new_page()
        erros = []
        pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
        pg.erros = erros
        yield pg
        nav.close()


def test_atual_indisponivel_mantem_original(pagina):
    a = _instala({})
    a.tentar()
    pagina.goto(URL)
    pagina.wait_for_selector("#fonte-status", timeout=40000)
    assert pagina.get_attribute("#fonte-atual", "aria-disabled") == "true"
    assert pagina.get_attribute("#fonte-original", "aria-checked") == "true"
    assert "indisponíveis" in pagina.inner_text("#fonte-status")
    pagina.click("#fonte-atual", force=True)                       # aria-disabled: não troca
    pagina.wait_for_timeout(600)
    assert pagina.get_attribute("#fonte-original", "aria-checked") == "true"
    assert not [e for e in pagina.erros if "favicon" not in e]


def test_atual_disponivel_troca_e_revalida_selecao(pagina):
    site, nova_origem = _site_novo()
    a = _instala(site)
    assert a.tentar() is True
    se_nova = dados.semana_epi(pd.Timestamp(nova_origem).date())[1]
    pagina.goto(URL + f"?cidade={CURITIBA}")
    pagina.wait_for_selector(".recencia", timeout=40000)
    assert "Curitiba" in pagina.inner_text("#cartao")
    assert pagina.get_attribute("#fonte-atual", "aria-disabled") == "false"
    pagina.click("#fonte-atual")
    pagina.wait_for_function(f"()=>document.querySelector('.recencia').textContent.includes('SE {se_nova}')",
                             timeout=20000)
    assert pagina.get_attribute("#fonte-atual", "aria-checked") == "true"
    assert "dados atuais" in pagina.inner_text(".recencia")
    assert "Curitiba" not in pagina.inner_text("#cartao")           # Curitiba não existe no atual → geo0
    pagina.click("#fonte-original")
    pagina.wait_for_function(
        f"()=>document.querySelector('.recencia').textContent.includes('SE {dados.ORIGINAL.se_origem[1]}')",
        timeout=20000)
    assert not [e for e in pagina.erros if "favicon" not in e]


def test_fonte_na_url_pedida_com_atual_carregado(pagina):
    site, _ = _site_novo()
    _instala(site).tentar()
    pagina.goto(URL + "?fonte=atual")
    pagina.wait_for_selector(".recencia", timeout=40000)
    assert pagina.get_attribute("#fonte-atual", "aria-checked") == "true"


def test_fonte_invalida_na_url_cai_no_original(pagina):
    site, _ = _site_novo()
    _instala(site).tentar()
    pagina.goto(URL + "?fonte=%3Cscript%3E")
    pagina.wait_for_selector(".recencia", timeout=40000)
    assert pagina.get_attribute("#fonte-original", "aria-checked") == "true"


def test_radiogroup_teclado(pagina):
    site, _ = _site_novo()
    _instala(site).tentar()
    pagina.goto(URL)
    pagina.wait_for_selector("#fonte-original", timeout=40000)
    pagina.focus("#fonte-original")
    pagina.keyboard.press("ArrowRight")
    pagina.wait_for_function("()=>document.querySelector('#fonte-atual').getAttribute('aria-checked')==='true'",
                             timeout=20000)
