# -*- coding: utf-8 -*-
"""E2E do aviso "fora do limite de treino" (Fase 2.3) com dataset atual INJETADO (limite forçado = 0:
todo município fica acima). Cobre cartão, Tabela 1, anúncio e axe AAA nos 2 temas, 390 e 1280 px."""
import os
import socket
import threading
import time

import pytest
from test_a11y_axe import _axe
from test_atual import DATA, RUN, _fetcher, _site

import atual
import dados

PORT = 8079
URL = f"http://127.0.0.1:{PORT}/"


def _site_com_limite():
    import hashlib
    import json

    import pandas as pd
    prev = pd.read_csv(os.path.join(DATA, "previsoes.csv"))
    geos = prev.loc[prev["nivel_geo"] == "municipio", "geo_id"].astype(str).unique()
    lim = pd.DataFrame({"geo_id": geos, "casos_max_treino": 0.0, "log1p_min_treino": 0.0,
                        "log1p_max_treino": 0.0, "n_semanas_treino": 300, "pico_serie_completa": 1000})
    corpo = lim.to_csv(index=False).encode()
    s = _site()
    s[f"{atual.BASE_PADRAO}runs/{RUN}/limite_treino.csv"] = corpo
    ptr = json.loads(s[atual.BASE_PADRAO + "latest.json"])
    ptr["sha256"]["limite_treino.csv"] = hashlib.sha256(corpo).hexdigest()
    s[atual.BASE_PADRAO + "latest.json"] = json.dumps(ptr).encode()
    return s


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
    a = atual.Atual(fetcher=_fetcher(_site_com_limite()), hoje=dados.ORIGINAL.data_prev_h1)
    a._thread, a._pid = threading.current_thread(), os.getpid()
    atual._GLOBAL = a
    assert a.tentar() is True and a.conjunto().limite
    yield URL
    srv.shutdown()
    os.environ["DADOS_ATUAIS"] = "0"
    atual._GLOBAL = None


@pytest.fixture()
def pagina(servidor):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_context(locale="pt-BR", viewport={"width": 1280, "height": 900}).new_page()
        yield pg
        nav.close()


def _abre(pg, largura, tema):
    pg.set_viewport_size({"width": largura, "height": 900})
    pg.goto(URL + "?fonte=atual&lang=pt")
    pg.wait_for_selector("#cartao .aviso-limite", timeout=40000)
    pg.wait_for_timeout(1200)
    if tema == "dark":
        if largura < 1180:
            pg.click(".prefs-trigger")
        pg.click("#theme-dark")
        pg.wait_for_function("()=>document.documentElement.dataset.theme==='dark'", timeout=15000)
        if largura < 1180:
            pg.keyboard.press("Escape")
        pg.wait_for_timeout(1000)


def test_aviso_no_cartao_tabela_e_anuncio(pagina):
    _abre(pagina, 1280, "light")
    assert "menos confiável" in pagina.inner_text("#cartao .aviso-limite")
    assert pagina.locator("#cartao .aviso-limite .glifo").get_attribute("aria-hidden") == "true"
    assert pagina.locator(".tab-rank .glifo.atencao").count() > 0
    assert pagina.locator(".tab-rank .sr-only", has_text="acima do limite de treino").count() > 0
    assert "menos confiável" in pagina.inner_text("#cartao-status")


@pytest.mark.parametrize("largura", [390, 1280])
@pytest.mark.parametrize("tema", ["light", "dark"])
def test_axe_aaa_com_aviso_visivel(pagina, largura, tema):
    _abre(pagina, largura, tema)
    assert _axe(pagina) == []
