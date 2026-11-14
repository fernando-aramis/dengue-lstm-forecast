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
    assert "SE 43" in pagina.inner_text(".recencia"), "selo de recência deve mostrar a SE da origem"


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
SECOES_ARTIGO = ["resumo", "sec-1", "sec-2", "sec-3", "sec-4", "sec-5",
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
@pytest.mark.parametrize("largura", [360, 390, 768, 1024, 1179, 1180, 1280, 1920])
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
