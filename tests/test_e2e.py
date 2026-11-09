# -*- coding: utf-8 -*-
"""
Testes E2E (Playwright): sobe o app de verdade e valida preview, responsividade e
ausência de erro de console (guarda a regressão do 'Objects are not valid as a React child').

Gera as prévias em tests/screenshots/ para os 5 breakpoints pedidos:
  ≤480 (telefone retrato) · 767 (telefone paisagem) · 768 (tablet retrato) ·
  980 (tablet paisagem) · 1200 (desktop).

Rodar:  cd webapp && source .venv/bin/activate
        python -m playwright install chromium   # 1ª vez
        pytest tests/test_e2e.py -q
"""
import os
import socket
import sys
import threading
import time

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
WEBAPP = os.path.dirname(AQUI)
for p in (WEBAPP, os.path.join(WEBAPP, "pipeline")):
    if p not in sys.path:
        sys.path.insert(0, p)

SHOTS = os.path.join(AQUI, "screenshots")
os.makedirs(SHOTS, exist_ok=True)

PORT = 8077
URL = f"http://127.0.0.1:{PORT}/"
BREAKPOINTS = [
    (480, "telefone-retrato"),
    (767, "telefone-paisagem"),
    (768, "tablet-retrato"),
    (980, "tablet-paisagem"),
    (1200, "desktop"),
]


@pytest.fixture(scope="module")
def servidor():
    from werkzeug.serving import make_server
    import app as A
    srv = make_server("127.0.0.1", PORT, A.server, threaded=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    for _ in range(60):                       # espera a porta abrir
        try:
            socket.create_connection(("127.0.0.1", PORT), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield URL
    srv.shutdown()


@pytest.fixture(scope="module")
def pagina(servidor):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        ctx = navegador.new_context(device_scale_factor=1, locale="pt-BR")
        pg = ctx.new_page()
        erros = []
        pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.erros = erros
        yield pg
        navegador.close()


def _tracks(pg, sel):
    v = pg.evaluate("s=>{const e=document.querySelector(s);"
                    "return e?getComputedStyle(e).gridTemplateColumns:''}", sel)
    return len([t for t in v.split() if t]) if v and v != "none" else 0


def test_carrega_sem_erro_de_console(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector("#mapa .js-plotly-plot", timeout=40000)
    pagina.wait_for_selector(".cartao .valor", timeout=40000)
    react = [e for e in pagina.erros if "not valid as a React child" in e]
    assert not react, f"o erro do React regressou: {react}"


def test_elementos_principais(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".cartao .valor", timeout=40000)
    pagina.wait_for_function(
        "()=>{const v=document.querySelector('.cartao .valor');return v && /\\d/.test(v.textContent);}",
        timeout=40000)
    assert pagina.title().startswith("Previsão de dengue")
    assert pagina.locator("header.hero h1").is_visible()
    assert pagina.locator(".stats .stat").count() == 4
    assert pagina.locator(".cartao .pill").count() >= 1           # cartão renderizou
    assert any(c.isdigit() for c in pagina.locator(".cartao .valor").inner_text())
    assert pagina.locator(".aviso.info").is_visible()


@pytest.mark.parametrize("largura,nome", BREAKPOINTS)
def test_responsivo_sem_overflow_e_preview(pagina, largura, nome):
    pagina.set_viewport_size({"width": largura, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".stats .stat", timeout=40000)
    pagina.wait_for_function(                        # card preenchido (sem flash vazio)
        "()=>{const v=document.querySelector('.cartao .valor');return v && /\\d/.test(v.textContent);}",
        timeout=40000)
    pagina.wait_for_timeout(500)                     # layout/plotly assentarem

    # 1) não pode haver rolagem horizontal na página
    overflow = pagina.evaluate("()=>document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"rolagem horizontal em {largura}px ({nome}): sobra {overflow}px"

    # 2) nenhum container estrutural pode ultrapassar a viewport (tabela é rolável à parte)
    spill = pagina.evaluate(
        "()=>{const vw=window.innerWidth,bad=[];"
        "for(const el of document.querySelectorAll("
        "'header,section,.wrap,.panel,.stat,.card,.finding,.aviso,.chip,.controls,.seg-group')){"
        "const r=el.getBoundingClientRect();"
        "if(r.width>0&&(r.right>vw+1||r.left<-1))bad.push((el.className||el.tagName)+'@'+Math.round(r.right));}"
        "return bad.slice(0,6);}")
    assert not spill, f"elementos ultrapassam a viewport em {largura}px ({nome}): {spill}"

    # 3) prévia
    pagina.screenshot(path=os.path.join(SHOTS, f"bp-{largura:04d}-{nome}.png"), full_page=True)


def test_grade_muda_por_breakpoint(pagina):
    pagina.goto(URL)
    pagina.wait_for_selector(".stats", timeout=40000)

    pagina.set_viewport_size({"width": 480, "height": 900})
    pagina.wait_for_timeout(250)
    assert _tracks(pagina, ".stats") == 1, "stats deveria ter 1 coluna ≤480"
    assert _tracks(pagina, ".grid") == 1, "mapa/detalhe deveriam empilhar ≤480"

    pagina.set_viewport_size({"width": 600, "height": 900})
    pagina.wait_for_timeout(250)
    assert _tracks(pagina, ".stats") == 2, "stats deveria ter 2 colunas em 600px"

    pagina.set_viewport_size({"width": 1000, "height": 900})
    pagina.wait_for_timeout(250)
    assert _tracks(pagina, ".stats") == 4, "stats deveria ter 4 colunas ≥980"
    assert _tracks(pagina, ".grid") == 2, "mapa/detalhe deveriam ficar lado a lado ≥980"


def test_paineis_mesma_altura_desktop(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".cartao .valor", timeout=40000)
    pagina.wait_for_timeout(500)
    hm = pagina.locator(".panel-mapa").bounding_box()["height"]
    hd = pagina.locator(".panel-detalhe").bounding_box()["height"]
    assert abs(hm - hd) <= 4, f"mapa ({hm}) e card ({hd}) deveriam ter a mesma altura"


def test_troca_idioma(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.evaluate("()=>localStorage.removeItem('tema')")
    pagina.goto(URL)
    pagina.wait_for_selector("header.hero h1", timeout=40000)
    pagina.click("#lang-en")
    pagina.wait_for_function(
        "()=>document.querySelector('header.hero h1') && "
        "document.querySelector('header.hero h1').textContent.includes('Weekly dengue')",
        timeout=15000)
    pagina.click("#lang-es")
    pagina.wait_for_function(
        "()=>document.querySelector('header.hero h1').textContent.includes('Pronóstico semanal')",
        timeout=15000)
    pagina.click("#lang-pt")  # volta ao PT


def test_troca_tema_e_preview_dark(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".cartao .valor", timeout=40000)
    # claro
    pagina.click("#theme-light")
    pagina.wait_for_function("()=>document.documentElement.getAttribute('data-theme')==='light'",
                             timeout=10000)
    # escuro
    pagina.click("#theme-dark")
    pagina.wait_for_function("()=>document.documentElement.getAttribute('data-theme')==='dark'",
                             timeout=10000)
    pagina.wait_for_timeout(600)
    pagina.screenshot(path=os.path.join(SHOTS, "dark-1200-desktop.png"), full_page=True)
    # prévia dark no telefone
    pagina.set_viewport_size({"width": 480, "height": 900})
    pagina.wait_for_timeout(500)
    pagina.screenshot(path=os.path.join(SHOTS, "dark-0480-telefone.png"), full_page=True)
    # volta ao sistema
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.click("#theme-system")


def test_cabecalhos_seguranca(pagina):
    resp = pagina.request.get(URL)
    h = {k.lower(): v for k, v in resp.headers.items()}
    assert h.get("x-content-type-options") == "nosniff"
    assert "referrer-policy" in h
    assert h.get("x-frame-options") == "SAMEORIGIN"
    assert "content-security-policy-report-only" in h


def test_troca_tema_nao_recarrega_a_pagina(pagina):
    # marca um global JS; se o tema fizesse reload completo, o marcador sumiria
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".cartao .valor", timeout=40000)
    pagina.evaluate("()=>{window.__marca = 'vivo';}")
    pagina.click("#theme-dark")
    pagina.wait_for_function("()=>document.documentElement.getAttribute('data-theme')==='dark'",
                             timeout=10000)
    assert pagina.evaluate("()=>window.__marca") == "vivo", "troca de tema recarregou a página"
    pagina.click("#theme-system")
