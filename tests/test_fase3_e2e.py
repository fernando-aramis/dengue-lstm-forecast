# -*- coding: utf-8 -*-
"""E2E das Fases 2B/3 (P.1 metodologia, P.2 download, P.3 o que mudou, 3.3 desempenho) com dataset atual
INJETADO (previsão anterior + desempenho.json). axe AAA nos 2 temas, 390 e 1280 px."""
import os
import socket
import threading
import time

import pytest
from test_a11y_axe import _axe
from test_atual import DATA, RUN, _fetcher, _site

import atual
import dados

PORT = 8080
URL = f"http://127.0.0.1:{PORT}/"


def _site_completo():
    import hashlib
    import json

    import pandas as pd
    prev = pd.read_csv(os.path.join(DATA, "previsoes.csv"))
    ant = prev.copy()
    for col in ("data_origem", "data_prev"):
        ant[col] = (pd.to_datetime(ant[col]) - pd.Timedelta(days=7)).dt.strftime("%Y-%m-%d")
    h = lambda n: {"n": n, "acertos": n * 9 // 10, "cobertura": 0.9, "wilson_inf": 0.84, "wilson_sup": 0.94,  # noqa: E731
                   "largura_media": 30.0, "mae_lstm": 10.0, "mae_ingenuo": 12.0, "skill": 0.17, "mae_log_lstm": 0.2,
                   "mae_log_ingenuo": 0.25, "skill_log": 0.2, "mae_mediano_cidade_lstm": 3.0,
                   "mae_mediano_cidade_ingenuo": 4.0, "skill_mediano_cidade": 0.25, "n_cidades": 33}
    desemp = {"gerado_em": "2026-12-14T09:00:00+00:00", "criterio": {"atraso_semanas": 4, "n_min": 100},
              "por_h": {"1": h(150), "2": h(60), "3": {"n": 0}, "4": {"n": 0}}, "periodo": None}
    s = _site()
    ptr = json.loads(s[atual.BASE_PADRAO + "latest.json"])
    for nome, corpo in (("previsoes_anterior.csv", ant.to_csv(index=False).encode()),
                        ("desempenho.json", json.dumps(desemp).encode())):
        s[f"{atual.BASE_PADRAO}runs/{RUN}/{nome}"] = corpo
        ptr["sha256"][nome] = hashlib.sha256(corpo).hexdigest()
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
    a = atual.Atual(fetcher=_fetcher(_site_completo()), hoje=dados.ORIGINAL.data_prev_h1)
    a._thread, a._pid = threading.current_thread(), os.getpid()
    atual._GLOBAL = a
    assert a.tentar() is True and a.conjunto().anterior is not None and a.conjunto().desempenho
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
    pg.wait_for_selector("#horizontes .mudancas", timeout=40000)
    pg.wait_for_timeout(1200)
    if tema == "dark":
        if largura < 1180:
            pg.click(".prefs-trigger")
        pg.click("#theme-dark")
        pg.wait_for_function("()=>document.documentElement.dataset.theme==='dark'", timeout=15000)
        if largura < 1180:
            pg.keyboard.press("Escape")
        pg.wait_for_timeout(1000)


def test_recursos_visiveis_e_texto_neutro(pagina):
    _abre(pagina, 1280, "light")
    m = pagina.inner_text("#horizontes .mudancas")
    assert "O que mudou desde a previsão anterior" in m and "nowcast" in m and "t+1" in m
    assert pagina.locator("#horizontes .mudancas-lista li").count() == 3
    assert "medida no t+1" in pagina.inner_text("#horizontes")
    t = pagina.inner_text(".tab-desemp")
    assert "em acumulação (n=60; mínimo 100)" in t and "+17%" in t
    assert pagina.locator("#metodologia h3").count() == 7


def test_link_de_download_serve_csv(pagina):
    _abre(pagina, 1280, "light")
    a = pagina.locator("[data-testid=baixar-csv]")
    assert a.count() == 1 and a.bounding_box()["height"] >= 44
    href = a.get_attribute("href")
    assert href.endswith("?fonte=atual")
    r = pagina.request.get(URL.rstrip("/") + href)
    assert r.status == 200 and r.headers["content-type"].startswith("text/csv")
    assert r.text().splitlines()[0].endswith("fonte,se_origem")


@pytest.mark.parametrize("largura", [390, 1280])
@pytest.mark.parametrize("tema", ["light", "dark"])
def test_axe_aaa_com_recursos_novos(pagina, largura, tema):
    _abre(pagina, largura, tema)
    assert _axe(pagina) == []
