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
    (320, "telefone-minimo"),          # menor viewport suportado (WCAG 1.4.10 reflow)
    (360, "telefone-comum"),
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
    pagina.goto(URL)   # navegar ANTES de tocar em localStorage (about:blank nega acesso)
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


# ---- UI nova (F2–F5): navegação, recência, artigo, citação ----
def test_nav_ancoras(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector("#artigo", timeout=40000)
    pagina.click(".nav-desktop a[href='#artigo']")
    pagina.wait_for_timeout(600)
    top = pagina.evaluate("()=>document.querySelector('#artigo').getBoundingClientRect().top")
    assert top < 120, f"#artigo deveria ir ao topo ao navegar (top={top})"


def test_recencia_se(pagina):
    pagina.goto(URL)
    pagina.wait_for_selector(".recencia", timeout=40000)
    import dados
    se = dados.ORIGINAL.se_origem[1]                          # derivado dos dados: não quebra a cada retreino
    assert f"SE {se}" in pagina.inner_text(".recencia"), "selo de recência deve mostrar a SE da origem"


def test_artigo_lang_pt(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".artigo-titulo", timeout=40000)
    pagina.click("#lang-en")
    pagina.wait_for_function(
        "()=>document.querySelector('header.hero h1').textContent.includes('Weekly dengue')", timeout=15000)
    assert pagina.get_attribute(".artigo-titulo", "lang") == "pt", "título do artigo deve ficar em pt"
    pagina.click("#lang-pt")


def test_citar_e_cff(pagina):
    pagina.goto(URL)
    pagina.wait_for_selector("#como-citar", timeout=40000)
    assert pagina.locator("#cite-abnt").count() == 1 and pagina.locator("#cite-bibtex").count() == 1
    assert pagina.locator("#como-citar a[href='/CITATION.cff']").count() == 1, "falta link de download do CFF"


# ------------------------------------------------------------------ A15: estado na URL
def _estado_url(pg):
    return pg.evaluate("""()=>({
        search: location.search,
        hist: history.length,
        lang: document.documentElement.lang,
        cidade: (document.querySelector('#dd-cidade')||{}).innerText||'',
        cartao: ((document.querySelector('#cartao')||{}).innerText||'').split('\\n')[0]})""")


def _abre(pg, caminho):
    pg.set_viewport_size({"width": 1200, "height": 900})
    pg.goto(URL.rstrip("/") + caminho)
    pg.wait_for_selector("#cartao", timeout=40000)
    pg.wait_for_timeout(2500)      # boot (80 ms) + callbacks de aplicação da URL


def test_url_aplica_idioma_e_cidade(pagina):
    _abre(pagina, "/?lang=es&cidade=1200401")           # Rio Branco
    s = _estado_url(pagina)
    assert s["lang"] == "es" and s["cartao"] == "Rio Branco" and s["cidade"] == "Rio Branco"
    _abre(pagina, "/?lang=pt&cidade=UF-PR")             # escopo estadual
    assert _estado_url(pagina)["cartao"] == "Paraná"


@pytest.mark.parametrize("lixo", ["abc", "%3Cscript%3E", "UF-ZZ", "9999999"])
def test_url_invalida_cai_na_selecao_segura(pagina, lixo):
    _abre(pagina, f"/?lang=pt&cidade={lixo}")
    s = _estado_url(pagina)
    assert s["cartao"] == "São Paulo" and s["cidade"] == "São Paulo"   # GEO0, dropdown nunca vazio
    assert lixo not in s["search"]                                     # valor forjado não é ecoado


def test_url_espelha_selecao_sem_empilhar_historico(pagina):
    _abre(pagina, "/?lang=pt&cidade=1200401")
    h0 = _estado_url(pagina)["hist"]
    pagina.click("#dd-cidade")
    pagina.get_by_role("option", name="Maceió").first.click()
    pagina.wait_for_function("()=>location.search.includes('cidade=2704302')", timeout=15000)
    assert _estado_url(pagina)["hist"] == h0                            # replaceState
    pagina.reload()
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.wait_for_timeout(2500)
    assert _estado_url(pagina)["cartao"] == "Maceió"                    # restaura após reload
    pagina.click("#lang-en")                                            # trocar idioma preserva a cidade
    pagina.wait_for_function("()=>document.documentElement.lang==='en'", timeout=15000)
    pagina.wait_for_timeout(1500)
    assert _estado_url(pagina)["cartao"] == "Maceió"
    pagina.click("#lang-pt")                                            # devolve o estado compartilhado
    pagina.wait_for_function("()=>document.documentElement.lang==='pt'", timeout=15000)


# ------------------------------------------------------------------ A16: movimento + content-visibility
SECOES_ARTIGO = ["resumo", "sec-1", "sec-2", "sec-3", "sec-4", "sec-5", "metodologia",
                 "declaracoes", "referencias", "como-citar"]


def test_entrada_unica_no_hero_e_fora_do_painel(pagina):
    _abre(pagina, "/?lang=pt")
    assert pagina.evaluate("document.querySelectorAll('.enter').length") == 1
    assert pagina.evaluate("document.querySelector('.enter').classList.contains('hero-lead')")
    assert not pagina.evaluate("document.querySelector('#painel').classList.contains('enter')")
    # parte de estado já visível (nunca opacity:0) e anima só opacity+transform
    assert pagina.evaluate("getComputedStyle(document.querySelector('.hero-lead')).animationName") == "rise"


def test_content_visibility_so_nas_secoes_do_artigo(pagina):
    _abre(pagina, "/?lang=pt")
    cv = pagina.evaluate("ids=>ids.map(i=>getComputedStyle(document.getElementById(i)).contentVisibility)",
                         SECOES_ARTIGO)
    assert cv == ["auto"] * len(SECOES_ARTIGO)
    # acima da dobra / gráficos / coluna lateral ficam SEMPRE renderizados
    for sel in ("#painel", "#indicadores", ".hero", "#dados"):
        assert pagina.evaluate("s=>getComputedStyle(document.querySelector(s)).contentVisibility", sel) == "visible"
    # texto das seções puladas continua acessível (Ctrl+F, leitores de tela)
    assert "Referências" in pagina.evaluate("document.body.innerText")


@pytest.mark.parametrize("lang", ["pt", "en", "es"])
@pytest.mark.parametrize("largura", [1280, 390])
def test_ancoras_pousam_no_scroll_margin(pagina, largura, lang):
    """content-visibility + scroll anchoring + estimativa errada já fez #sec-2 pousar 55–85px fora
    (os erros por idioma se somam acima do alvo); a âncora deve ficar ±8px do scroll-margin."""
    pagina.set_viewport_size({"width": largura, "height": 900})
    pagina.goto(URL.rstrip("/") + f"/?lang={lang}")
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.wait_for_timeout(2500)
    for alvo in ("sec-2", "sec-4", "referencias", "como-citar"):
        pagina.evaluate("()=>{location.hash='';window.scrollTo(0,0)}")
        pagina.wait_for_timeout(250)
        pagina.evaluate(f"location.hash='#{alvo}'")
        pagina.wait_for_timeout(1000)
        topo = pagina.evaluate(f"document.getElementById('{alvo}').getBoundingClientRect().top")
        margem = pagina.evaluate(f"parseFloat(getComputedStyle(document.getElementById('{alvo}')).scrollMarginTop)")
        assert abs(topo - margem) <= 8, f"[{lang}/{largura}] #{alvo}: topo {topo:.0f}px, esperado ~{margem:.0f}px"


def test_altura_estimada_proxima_da_real(pagina):
    """Intrinsic sizes medidos: a página não deve 'encolher' >3% ao renderizar tudo (barra de rolagem estável)."""
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.wait_for_timeout(2500)
    est = pagina.evaluate("document.documentElement.scrollHeight")
    pagina.add_style_tag(content=".artigo-coluna > section{content-visibility:visible !important}")
    pagina.wait_for_timeout(400)
    real = pagina.evaluate("document.documentElement.scrollHeight")
    assert abs(est - real) / real < 0.03, f"estimada {est}px vs real {real}px"
    pagina.goto(URL.rstrip("/") + "/?lang=pt")      # devolve a página ao estado padrão dos próximos testes
    pagina.wait_for_selector("#cartao", timeout=40000)


# ------------------------------------------------------------------ barra do topo: altura estável (CLS)
@pytest.mark.parametrize("largura", [320, 360, 390, 768, 1024, 1179, 1180, 1280, 1920])
def test_barra_topo_uma_linha_e_altura_igual_ao_token(pagina, largura):
    """A barra já chegou a 113px (2 linhas) no desktop, 142px a 768px e 116px a 360px: os controles
    quebravam de linha após a hidratação (CLS 1,15). Agora: 1 linha, e --topbar-h = altura real,
    que alimenta scroll-margin-top e o .toc sticky."""
    pagina.set_viewport_size({"width": largura, "height": 800})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.wait_for_timeout(2500)
    r = pagina.evaluate("""()=>({bar: document.querySelector('.topbar').getBoundingClientRect().height,
        token: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--topbar-h')),
        ctrl: document.querySelector('.controls').getBoundingClientRect().bottom,
        barBottom: document.querySelector('.topbar').getBoundingClientRect().bottom})""")
    assert abs(r["bar"] - r["token"]) <= 2, f"barra {r['bar']}px vs --topbar-h {r['token']}px"
    assert r["bar"] <= 70, f"barra com {r['bar']}px: controles quebraram de linha"
    assert r["ctrl"] <= r["barBottom"] + 1                       # controles dentro da barra


def test_barra_topo_nao_muda_de_altura_na_hidratacao(pagina):
    pagina.set_viewport_size({"width": 1280, "height": 800})
    pagina.goto(URL.rstrip("/") + "/?lang=pt", wait_until="commit")
    alturas = set()
    for _ in range(40):
        try:
            h = pagina.evaluate("()=>{const e=document.querySelector('.topbar');return e?Math.round(e.getBoundingClientRect().height):null}")
        except Exception:
            h = None
        if h:
            alturas.add(h)
        pagina.wait_for_timeout(60)
    assert len(alturas) == 1, f"a barra mudou de altura durante o carregamento: {sorted(alturas)}"


@pytest.mark.parametrize("largura", [1180, 1280, 1440])
def test_controles_da_barra_tem_tamanho_equilibrado(pagina, largura):
    """Botões de idioma/tema: alvo AAA (44px) sem passar disso, e grupos que cabem na barra com folga."""
    pagina.set_viewport_size({"width": largura, "height": 800})
    pagina.goto(URL.rstrip("/") + "/?lang=pt", wait_until="commit")
    pagina.wait_for_selector("#lang-pt", state="attached", timeout=40000)
    pagina.wait_for_timeout(800)
    m = pagina.evaluate("""() => ({
      bar: document.querySelector('.topbar').getBoundingClientRect().height,
      segs: [...document.querySelectorAll('.topbar .seg')].filter(e => e.offsetParent)
              .map(e => { const r = e.getBoundingClientRect(); return [r.width, r.height]; }),
      grupos: [...document.querySelectorAll('.topbar .seg')].filter(e => e.offsetParent)
              .map(e => e.parentElement.getBoundingClientRect().height)})""")
    assert m["segs"], "nenhum botão visível"
    for w, h in m["segs"]:
        assert 44 <= h <= 48, f"botão {w}x{h}: fora de 44–48px"
    assert max(m["grupos"]) <= m["bar"] - 12, f"grupo {max(m['grupos'])}px apertado na barra de {m['bar']}px"


@pytest.mark.parametrize("query,presente,ausente", [
    ("?lang=pt", "pt", "en"),
    ("?lang=es", "es", "pt"),
    ("?lang=zz&cidade=abc", "en", "pt"),     # inválido → Accept-Language (en)
])
def test_primeiro_render_ja_nasce_no_idioma_da_url(servidor, query, presente, ausente):
    from i18n import tr
    presente, ausente = tr(presente, "h1"), tr(ausente, "h1")      # h1 do hero muda por idioma
    """Link compartilhado (?lang=) aberto em navegador de OUTRO idioma: o /_dash-layout recebe a URL via
    Referer. Antes nascia em inglês e virava português só no boot (flash + CLS 0,051 no mobile)."""
    import json
    import urllib.request
    req = urllib.request.Request(URL.rstrip("/") + "/_dash-layout",
                                 headers={"Referer": URL.rstrip("/") + "/" + query, "Accept-Language": "en-US"})
    txt = json.dumps(json.loads(urllib.request.urlopen(req, timeout=30).read()), ensure_ascii=False)
    assert presente in txt and ausente not in txt


def test_footer_de_scripts_do_dash_nao_ocupa_espaco(pagina):
    """O <footer> filho do body é do Dash (só scripts); herdava o estilo do rodapé editorial (~61px) e
    sumia ao montar o React (CLS 0,025). O rodapé editorial (dentro de #conteudo) segue visível."""
    pagina.set_viewport_size({"width": 1280, "height": 800})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector("#cartao", timeout=40000)
    assert pagina.evaluate("getComputedStyle(document.querySelector('body > footer')).display") == "none"
    assert pagina.evaluate("document.querySelector('#conteudo footer').getBoundingClientRect().height") > 20


@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_cabecalho_corrido_uma_linha_e_sem_estouro(pagina, lang):
    """Faixa mono acima da barra: quebrava em 2–3 linhas por lado entre 768 e 1179px (altura 49–66px).
    Agora: rótulo curto abaixo de 1180px, texto longo acima; sempre 1 linha, sem overflow horizontal."""
    alturas = set()
    for largura in (768, 820, 900, 1024, 1100, 1179, 1180, 1280, 1440):
        pagina.set_viewport_size({"width": largura, "height": 800})
        pagina.goto(URL.rstrip("/") + f"/?lang={lang}")
        pagina.wait_for_selector(".topbar", state="attached", timeout=40000)
        pagina.wait_for_timeout(500)
        m = pagina.evaluate("""() => { const e = document.querySelector('.running-header');
          const k = [...e.children].filter(c => getComputedStyle(c).display !== 'none');
          return {h: e.getBoundingClientRect().height, sw: e.scrollWidth, cw: e.clientWidth,
                  linhas: k.map(c => Math.round(c.getBoundingClientRect().height))}; }""")
        assert m["sw"] <= m["cw"] + 1, f"{lang}@{largura}: faixa estoura ({m['sw']}>{m['cw']})"
        assert max(m["linhas"]) <= 20, f"{lang}@{largura}: texto quebrou em várias linhas {m['linhas']}"
        alturas.add(round(m["h"]))
    assert len(alturas) == 1, f"{lang}: altura da faixa varia com a largura: {sorted(alturas)}"


def test_trocar_idioma_apos_uf_e_cidade_nao_reverte_a_selecao(pagina):
    """Race: Input('lang') de popular_cidades devolvia value='UF-SP' e revertia a cidade escolhida
    (cartão do estado + URL ?cidade=UF-SP, com o dropdown ainda mostrando a cidade). Repetido porque
    depende da ordem de chegada das respostas."""
    _abre(pagina, "/?lang=pt&cidade=UF-SP")
    pagina.click("#dd-cidade")
    pagina.get_by_role("option", name="Campinas").first.click()
    pagina.wait_for_function("()=>!location.search.includes('UF-SP')", timeout=15000)
    for lang in ("es", "pt", "en", "pt"):
        pagina.click(f"#lang-{lang}")
        pagina.wait_for_function(f"()=>document.documentElement.lang==='{lang}'", timeout=15000)
        pagina.wait_for_timeout(1800)
        e = _estado_url(pagina)
        assert e["cartao"] == "Campinas" and "UF-SP" not in e["search"], f"{lang}: {e}"


def test_mapa_segue_tema_escuro_apos_trocar_idioma(pagina):
    """Race: render_content (sem State de tema) reconstruía o mapa claro e o remapa_idioma competia."""
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.click("#theme-dark")
    pagina.wait_for_function("()=>document.documentElement.dataset.theme==='dark'", timeout=15000)
    for lang in ("en", "es", "pt"):
        pagina.click(f"#lang-{lang}")
        pagina.wait_for_function(f"()=>document.documentElement.lang==='{lang}'", timeout=15000)
        pagina.wait_for_timeout(2200)
        estilo = pagina.evaluate("()=>{const g=document.querySelector('#mapa .js-plotly-plot');"
                                 "return g && g._fullLayout ? g._fullLayout.map.style : null}")
        assert estilo and "dark" in str(estilo), f"{lang}: mapa com estilo {estilo!r} no tema escuro"


def test_menus_details_fecham_com_esc_e_clique_fora(pagina):
    """Menu, preferências e acessibilidade ficavam abertos (e sobrepostos) com Esc/clique fora."""
    pagina.set_viewport_size({"width": 390, "height": 800})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector(".prefs-trigger", timeout=40000)
    pagina.wait_for_timeout(800)
    pagina.click(".prefs-trigger")
    assert pagina.evaluate("document.querySelector('details.prefs').open")
    pagina.keyboard.press("Escape")
    assert not pagina.evaluate("document.querySelector('details.prefs').open")
    assert pagina.evaluate("document.activeElement.classList.contains('prefs-trigger')")   # foco devolvido
    pagina.click(".prefs-trigger")
    pagina.mouse.click(200, 600)                                                         # fora
    assert not pagina.evaluate("document.querySelector('details.prefs').open")


def test_popover_de_preferencias_cabe_a_320px(pagina):
    pagina.set_viewport_size({"width": 320, "height": 700})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector(".prefs-trigger", timeout=40000)
    pagina.wait_for_timeout(800)
    pagina.click(".prefs-trigger")
    r = pagina.evaluate("(()=>{const b=document.querySelector('.prefs-pop').getBoundingClientRect();"
                        "return [b.left,b.right,innerWidth]})()")
    assert r[0] >= 0 and r[1] <= r[2], f"popover fora da viewport: {r}"


def test_barra_da_situacao_segue_a_paleta_cvd(pagina):
    """A barra usava style inline (cor fixa) e ignorava data-cvd=on enquanto glifos/mapa mudavam."""
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector(".barra-seg", timeout=40000)
    cor = "(()=>getComputedStyle(document.querySelector('.barra-seg')).backgroundColor)()"
    antes = pagina.evaluate(cor)
    pagina.evaluate("document.documentElement.setAttribute('data-cvd','on')")
    pagina.wait_for_timeout(200)
    assert pagina.evaluate(cor) != antes


def test_alvos_de_toque_do_dropdown_e_links_de_materiais(pagina):
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector(".dash-dropdown-trigger", timeout=40000)
    alt = pagina.evaluate("[...document.querySelectorAll('.dash-dropdown-trigger')].map(e=>e.getBoundingClientRect().height)")
    assert alt and min(alt) >= 44, f"triggers de dropdown abaixo de 44px: {alt}"
    links = pagina.evaluate("[...document.querySelectorAll('.materiais a')].map(e=>e.getBoundingClientRect().height)")
    assert links and min(links) >= 24, f"links de materiais abaixo de 24px: {links}"


# ------------------------------------------------------------------ Fase 7: lacunas do plano de testes
@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_numeros_do_cartao_seguem_o_formato_do_idioma(pagina, lang):
    """O número previsto no cartão sai de formato.py: milhar/decimal por idioma (pt/es 1.197, en 1,197)."""
    from dados import ORIGINAL
    from formato import fmt_int
    mapa_cid, GEO0 = ORIGINAL.mapa_cid, ORIGINAL.geo0
    v = float(mapa_cid.loc[mapa_cid["geo_id"] == GEO0, "prev"].iloc[0])
    esperado = fmt_int(v, lang)
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + f"/?lang={lang}")
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.wait_for_timeout(800)
    txt = pagina.evaluate("document.querySelector('#cartao').innerText")
    assert esperado in txt, f"{lang}: '{esperado}' não aparece no cartão: {txt[:120]!r}"
    if v >= 1000:                                             # separador de milhar do idioma, nunca o do outro
        sep, outro = ("," if lang == "en" else "."), ("." if lang == "en" else ",")
        assert sep in esperado and not any(f"{d}{outro}{t}" in esperado for d in "0123456789" for t in "0123456789")


def test_meta_theme_color_acompanha_o_tema(pagina):
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector("#cartao", timeout=40000)
    cor = "document.querySelector('meta[name=theme-color]').getAttribute('content')"
    pagina.click("#theme-light")
    pagina.wait_for_function("()=>document.documentElement.dataset.theme==='light'", timeout=15000)
    claro = pagina.evaluate(cor)
    pagina.click("#theme-dark")
    pagina.wait_for_function("()=>document.documentElement.dataset.theme==='dark'", timeout=15000)
    escuro = pagina.evaluate(cor)
    assert claro.upper() == "#1C2620" and escuro.upper() == "#0E1113", (claro, escuro)   # = fundo da barra do tema


@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_html_lang_ja_e_o_do_idioma_antes_do_boot(pagina, lang):
    """O script do <head> define <html lang> a partir de ?lang= antes do React (WCAG 3.1.1 desde o 1º frame)."""
    pagina.goto(URL.rstrip("/") + f"/?lang={lang}", wait_until="commit")
    pagina.wait_for_selector("#boot-shell, .topbar", state="attached", timeout=40000)
    assert pagina.evaluate("document.documentElement.lang") == lang


def test_shell_estatico_e_noscript_sem_javascript(pagina):
    """Sem JS (crawlers, bloqueadores): o shell com título/lede e o link do estudo (DOI) existem no HTML."""
    ctx = pagina.context.browser.new_context(java_script_enabled=False)
    try:
        pg = ctx.new_page()
        pg.goto(URL.rstrip("/") + "/?lang=pt")
        assert pg.locator("#boot-shell .boot-title").count() == 1
        assert "Previsão semanal" in pg.locator("#boot-shell .boot-title").inner_text()
        link = pg.locator(".boot-noscript a")                     # <noscript> é conteúdo real sem JS
        assert link.count() == 1 and "zenodo.13328231" in link.get_attribute("href")
        assert pg.locator(".boot-noscript .boot-l[lang=pt]").count() == 1
    finally:
        ctx.close()


@pytest.mark.parametrize("largura", [390, 1280])
def test_alvos_de_toque_da_cabecalho_e_cta(pagina, largura):
    """Controles do topo e CTAs do hero ≥44px; links de navegação ≥24px (WCAG 2.5.8)."""
    pagina.set_viewport_size({"width": largura, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt")
    pagina.wait_for_selector("#cartao", timeout=40000)
    pagina.wait_for_timeout(900)
    r = pagina.evaluate("""() => { const vis = e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      const alt = sel => [...document.querySelectorAll(sel)].filter(vis).map(e => [e.id || e.className || e.tagName, Math.round(e.getBoundingClientRect().height)]);
      return {ctrl: alt('.topbar button, .topbar summary, .hero .btn'), nav: alt('.nav-a')}; }""")
    assert r["ctrl"], "nenhum controle visível"
    assert all(h >= 44 for _, h in r["ctrl"]), [x for x in r["ctrl"] if x[1] < 44]
    assert all(h >= 24 for _, h in r["nav"]), [x for x in r["nav"] if x[1] < 24]


@pytest.mark.parametrize("largura", [390, 1440])
def test_orcamento_de_fontes_no_carregamento(pagina, largura):
    """Só 3 woff2 (Inter, Source Serif, Mono 400; ≤120 KiB) na carga inicial. Uma regra com peso 600 em mono
    ou itálico fora do uso já puxou o Mono 500 e desfez o ganho do A13."""
    vistos = {}
    ctx = pagina.context.browser.new_context(viewport={"width": largura, "height": 900})   # cache limpo
    try:
        pg = ctx.new_page()
        pg.on("response", lambda r: vistos.__setitem__(r.url.split("/")[-1], len(r.body()))
              if r.url.endswith(".woff2") else None)
        pg.goto(URL.rstrip("/") + "/?lang=pt")
        pg.wait_for_selector("#cartao", timeout=40000)
        pg.wait_for_timeout(2500)
    finally:
        ctx.close()
    assert sorted(vistos) == ["ibm-plex-mono-400.woff2", "inter-var.woff2", "source-serif-4-var.woff2"], vistos
    assert sum(vistos.values()) <= 120 * 1024


def test_rotulo_do_tema_ja_vem_preenchido(pagina):
    pagina.set_viewport_size({"width": 1280, "height": 800})
    pagina.goto(URL.rstrip("/") + "/?lang=pt", wait_until="commit")
    pagina.wait_for_selector("#theme-label", timeout=40000)
    assert pagina.evaluate("document.querySelector('#theme-label').textContent.trim()") != ""


# ------------------------------------------------------------------ A5: fallback do mapa (WebGL)
def test_fallback_do_mapa_so_aparece_sem_webgl(pagina):
    """Regressão: .mapa-fallback { display:flex } anulava o atributo hidden → a mensagem 'WebGL bloqueado'
    aparecia SEMPRE, com o mapa funcionando."""
    _abre(pagina, "/?lang=pt")
    vis = lambda s: pagina.evaluate(f"(()=>{{const e=document.querySelector('{s}');return !!e&&e.offsetParent!==null&&e.getBoundingClientRect().height>0}})()")
    assert pagina.evaluate("document.documentElement.getAttribute('data-webgl')") != "off"
    assert not vis("#mapa-fallback"), "fallback visível com WebGL funcionando"
    assert vis("#mapa")
    # simula falha de WebGL: some o mapa (CSS por atributo, imune ao re-render) e a mensagem aparece
    pagina.evaluate("document.documentElement.setAttribute('data-webgl','off');"
                    "document.querySelector('#mapa-fallback').hidden=false")
    assert vis("#mapa-fallback") and not vis("#mapa")
    pagina.evaluate("document.documentElement.removeAttribute('data-webgl');"
                    "document.querySelector('#mapa-fallback').hidden=true")


# ------------------------------------------------------------------ Fase 5: gráficos
@pytest.mark.parametrize("largura", [360, 390, 768, 979, 980, 1280])
def test_grafico_detalhe_nao_sobrepoe_os_cartoes(pagina, largura):
    """Em coluna única (<980px) o `height:100%` do Plotly virava 0 num pai sem altura: o SVG caía em 450px
    e cobria os cartões t+1…t+4, a linha e os rótulos do eixo (slot de 210px)."""
    pagina.set_viewport_size({"width": largura, "height": 900})
    pagina.goto(URL.rstrip("/") + "/?lang=pt&cidade=4106902")
    pagina.wait_for_selector("#detalhe .main-svg", timeout=40000)
    pagina.wait_for_timeout(2500)
    g = pagina.evaluate("""()=>{const r=s=>document.querySelector(s).getBoundingClientRect();
        return {slot: r('#detalhe'), svg: r('#detalhe .main-svg'), plot: r('#detalhe .js-plotly-plot'), hor: r('#horizontes')}}""")
    assert g["plot"]["height"] >= 200, f"gráfico com {g['plot']['height']:.0f}px (colapsou)"
    assert g["svg"]["height"] <= g["slot"]["height"] + 1, f"SVG {g['svg']['height']:.0f}px > slot {g['slot']['height']:.0f}px"
    assert g["slot"]["bottom"] <= g["hor"]["top"] + 1, "o gráfico invade os cartões t+1…t+4"


@pytest.mark.parametrize("lang,presentes,ausentes", [
    ("pt", {"ago", "set", "out", "dez"}, {"aug", "oct", "dec"}),
    ("es", {"ago", "dic"}, {"aug", "dec"}),
    ("en", {"aug", "oct", "dec"}, {"ago", "out", "dez", "dic"})])
def test_eixo_x_do_detalhe_no_idioma_da_ui(pagina, lang, presentes, ausentes):
    """Os meses saíam em inglês ('Aug 2026') numa página em português: o Plotly do Dash não traz locales."""
    pagina.set_viewport_size({"width": 1280, "height": 900})
    pagina.goto(URL.rstrip("/") + f"/?lang={lang}&cidade=4106902")
    pagina.wait_for_selector("#detalhe .main-svg", timeout=40000)
    pagina.wait_for_timeout(2500)
    # o Plotly adelgaça os rótulos conforme a largura (3 ou 6): força 1 por mês p/ o teste não depender disso
    pagina.evaluate("Plotly.relayout(document.querySelector('#detalhe .js-plotly-plot'), {'xaxis.dtick': 'M1'})")
    pagina.wait_for_timeout(800)
    ticks = pagina.evaluate("[...document.querySelectorAll('#detalhe .xtick text')].map(t=>t.textContent.toLowerCase().split(' ')[0])")
    assert ticks and presentes & set(ticks), f"[{lang}] esperava {presentes} em {ticks}"
    assert not (ausentes & set(ticks)), f"[{lang}] meses de outro idioma: {ausentes & set(ticks)} em {ticks}"
    pagina.goto(URL.rstrip("/") + "/?lang=pt")      # devolve a página ao estado padrão dos próximos testes
    pagina.wait_for_selector("#cartao", timeout=40000)


# ------------------------------------------------------------------ lacunas do Nielsen (refino final)
def _escolhe_opcao(pg, seletor, indice):
    pg.click(seletor)
    pg.wait_for_timeout(250)
    pg.query_selector_all(".dash-dropdown-content [role=option]")[indice].click()
    pg.wait_for_timeout(1200)


def test_comparar_cidades_fluxo_completo(pagina):
    """Comparar: série + legenda + tabela t+1…t+4 + anúncio; persiste ao trocar idioma; limpar volta ao normal;
    estado desabilita o dropdown."""
    _abre(pagina, "/?lang=pt&cidade=4106902")
    traces = lambda: pagina.evaluate("document.querySelectorAll('#detalhe .scatterlayer .trace').length")  # noqa: E731
    base = traces()
    assert pagina.evaluate("document.querySelector('#legenda-cmp').hidden") is True
    assert pagina.locator(".tabela-cmp").count() == 0
    _escolhe_opcao(pagina, "#dd-comparar", 0)
    assert traces() == base + 2
    assert pagina.locator(".tabela-cmp tbody tr").count() == 2
    assert pagina.locator(".tabela-cmp thead th").count() == 4
    assert "Comparação:" in pagina.inner_text("#legenda-cmp")
    assert "Comparando com" in pagina.inner_text("#cartao-status")
    # `atualizar` traduz a legenda, `render_content` a reconstrói e `atualizar` roda de novo: a condição de texto
    # sozinha passava no estado intermediário (flake no CI). Rastreia o último instante SEM o texto e exige
    # ~0,8 s de estabilidade depois dele.
    pagina.evaluate("""() => { window.__ruim = performance.now();
        setInterval(() => { const e = document.querySelector('#legenda-cmp');
          if (!(e && e.innerText.includes('Comparison:'))) window.__ruim = performance.now(); }, 40); }""")
    pagina.click("#lang-en")                                  # idioma reconstrói o conteúdo: comparação fica
    pagina.wait_for_function("()=>performance.now() - window.__ruim > 800", timeout=15000)
    assert "Comparison:" in pagina.inner_text("#legenda-cmp")
    assert pagina.locator(".tabela-cmp").count() == 1
    pagina.click("#dd-comparar .dash-dropdown-clear")
    pagina.wait_for_timeout(1200)
    assert pagina.evaluate("document.querySelector('#legenda-cmp').hidden") is True
    assert pagina.locator(".tabela-cmp").count() == 0 and traces() == base
    _escolhe_opcao(pagina, "#dd-uf", 3)                       # estado: comparar só vale entre municípios
    assert pagina.evaluate("""[...document.querySelectorAll('#dd-comparar, #dd-comparar *')].some(
        e => e.disabled || e.getAttribute('aria-disabled') === 'true' || e.getAttribute('data-disabled') === 'true')""")
    assert not pagina.erros, pagina.erros[:3]


def test_primeira_dobra_mostra_aviso_e_painel(pagina):
    """Heurística 8: o painel (título + controles + topo do mapa) entra na 1ª dobra em 1440×900; o aviso
    'não é alerta oficial' continua acima dele; os resultados-chave vêm depois do painel."""
    pagina.set_viewport_size({"width": 1440, "height": 900})
    pagina.goto(URL + "?lang=pt")
    pagina.wait_for_selector("#mapa", timeout=40000)
    pagina.wait_for_timeout(1500)
    y = pagina.evaluate("""()=>{const t=s=>document.querySelector(s).getBoundingClientRect();
        return {aviso:t('.indicadores .aviso.warn').bottom, h2:t('#painel-titulo').top, ctrl:t('.controles').bottom,
                mapa:t('#mapa').top, painel:t('#painel').top+scrollY, kpi:t('#resultados-chave').top+scrollY}}""")
    assert y["aviso"] < y["h2"] and y["ctrl"] < 900 and y["mapa"] < 900, y
    assert y["kpi"] > y["painel"], y
    pagina.set_viewport_size({"width": 1280, "height": 720})
    pagina.wait_for_timeout(300)
    assert pagina.evaluate("document.querySelector('#painel-titulo').getBoundingClientRect().bottom") < 720


def test_estado_de_carregamento_visivel_e_trilingue(pagina):
    """Heurística 1: enquanto o Dash marca data-dash-is-loading, o cartão esmaece e aparece 'Atualizando…'
    (sem deslocar nada: pseudo-elemento absoluto)."""
    esperado = {"pt": "Atualizando…", "en": "Updating…", "es": "Actualizando…"}
    for lang, texto in esperado.items():
        _abre(pagina, f"/?lang={lang}")
        pagina.evaluate("document.querySelectorAll('#cartao,#detalhe,#horizontes')"
                        ".forEach(e => e.setAttribute('data-dash-is-loading', 'true'))")
        pagina.wait_for_timeout(600)
        assert texto in pagina.evaluate("getComputedStyle(document.querySelector('.panel-detalhe'), '::after').content")
        assert float(pagina.evaluate("getComputedStyle(document.querySelector('#cartao')).opacity")) < 1
        pagina.evaluate("document.querySelectorAll('[data-dash-is-loading]').forEach(e => e.removeAttribute('data-dash-is-loading'))")
        pagina.wait_for_timeout(500)
        assert pagina.evaluate("getComputedStyle(document.querySelector('.panel-detalhe'), '::after').content") in ('""', "none", "normal")


# ---------------------------------------------------------------- regressões do relatório de UI (2026-11)
@pytest.mark.parametrize("largura", [320, 390, 820])
def test_mapa_nao_cobre_a_legenda_em_coluna_unica(pagina, largura):
    """O canvas do mapa (Plotly) caía no padrão de 450px num slot de 340px e cobria legenda e nota."""
    pagina.set_viewport_size({"width": largura, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector("#mapa .js-plotly-plot", timeout=40000)
    pagina.wait_for_timeout(1500)
    r = pagina.evaluate("""()=>{const m=document.querySelector('#mapa'), pl=m.querySelector('.js-plotly-plot'),
        lg=document.querySelector('.map-legend');
        return {slot:m.getBoundingClientRect().bottom, canvas:pl.getBoundingClientRect().bottom,
                legenda:lg.getBoundingClientRect().top}}""")
    assert r["canvas"] <= r["slot"] + 1, f"canvas do mapa transborda o slot em {largura}px: {r}"
    assert r["slot"] <= r["legenda"] + 1, f"mapa cobre a legenda em {largura}px: {r}"


def test_tabela1_completa_cabe_sem_cortar_colunas_no_desktop(pagina):
    for largura in (1200, 1440):
        pagina.set_viewport_size({"width": largura, "height": 900})
        pagina.goto(URL)
        pagina.wait_for_selector(".tab-rank tbody tr", timeout=40000)
        r = pagina.evaluate("""()=>{const w=document.querySelector('.tbl-rank-wrap');
            return {sw:w.scrollWidth, cw:w.clientWidth, h:w.getBoundingClientRect().height,
                    linhas:document.querySelectorAll('.tab-rank tbody tr').length,
                    ult:[...document.querySelectorAll('.tab-rank tbody tr:first-child td')].map(
                        td=>td.getBoundingClientRect().right).pop()}}""")
        import dados
        assert r["linhas"] == len(dados.ORIGINAL.mapa_cid), f"Tabela 1 deveria ter todas as cidades: {r}"
        assert r["sw"] <= r["cw"] + 1, f"coluna(s) da Tabela 1 cortada(s) em {largura}px: {r}"
        assert r["h"] <= 520, f"altura da Tabela 1 deve ser limitada (rolagem interna): {r}"


def test_tabela1_cabecalho_fixo_ao_rolar(pagina):
    pagina.set_viewport_size({"width": 1200, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector(".tab-rank tbody tr", timeout=40000)
    r = pagina.evaluate("""()=>{const w=document.querySelector('.tbl-rank-wrap'), th=w.querySelector('thead th');
        const pg=window.scrollY; w.scrollTop=w.scrollHeight;
        return {pos:getComputedStyle(th).position, wt:w.getBoundingClientRect().top,
                tht:th.getBoundingClientRect().top, rolou:w.scrollTop>0, pg:Math.abs(window.scrollY-pg)}}""")
    assert r["pos"] == "sticky" and r["rolou"], r
    assert abs(r["tht"] - r["wt"]) <= 3, f"cabeçalho saiu do topo da região rolável: {r}"
    assert r["pg"] == 0, "rolar a tabela não pode rolar a página"


@pytest.mark.parametrize("largura", [320, 390, 768, 980, 1200, 1440])
def test_irmaos_do_painel_nao_se_sobrepoem(pagina, largura):
    """Guarda-chuva (A5): filhos diretos dos painéis do mapa e do detalhe empilham sem sobrepor caixas.
    O teste de overflow da página não pegava canvas que transbordava o próprio slot."""
    pagina.set_viewport_size({"width": largura, "height": 900})
    pagina.goto(URL)
    pagina.wait_for_selector("#mapa .js-plotly-plot", timeout=40000)
    pagina.wait_for_selector("#detalhe .js-plotly-plot", timeout=40000)
    pagina.wait_for_timeout(1500)
    bad = pagina.evaluate("""()=>{const out=[];
      for(const p of document.querySelectorAll('.panel-mapa,.panel-detalhe')){
        const k=[...p.children].filter(e=>{const r=e.getBoundingClientRect();
          return r.height>0&&getComputedStyle(e).position!=='absolute'&&!e.classList.contains('sr-only')});
        for(let i=1;i<k.length;i++){
          const a=k[i-1].getBoundingClientRect(), b=k[i].getBoundingClientRect();
          if(a.bottom>b.top+1) out.push(p.className.split(' ')[1]+': '+(k[i-1].id||k[i-1].className)+
            ' ↧'+Math.round(a.bottom)+' > '+(k[i].id||k[i].className)+' ↥'+Math.round(b.top));}}
      return out}""")
    assert not bad, f"filhos do painel se sobrepõem em {largura}px: {bad}"
