# -*- coding: utf-8 -*-
"""
Painel de previsão de dengue — mapa nacional (capitais + principais cidades) com fallback estadual.

Arquitetura (Opção 1): o app NÃO treina e NÃO re-prevê. Lê previsões já calculadas
(webapp/data/*.csv) e as desenha. Troque os CSVs pelo pipeline sem mudar este arquivo.

Módulos: dados.py (carga) · figuras.py (Plotly/cartão) · layout.py (página) · i18n.py (PT/EN/ES).
Recursos de UI: tema claro/sistema/escuro, idioma PT/EN/ES (Accept-Language, fallback EN),
contraste WCAG AAA, layout mobile-first.

Rodar local:   python app.py                 (DASH_DEBUG=1 liga o modo debug)
Deploy:        gunicorn app:server
"""
import json
import logging
import os

from dash import Dash, dcc, html, Input, Output, State, ctx, no_update, Patch
from flask import request, send_file
from flask_compress import Compress

import conteudo
from i18n import tr, resolver
from dados import (prev, hist, mapa_cid, mapa_uf, nome_uf, UFS, COBERTAS, NAO_COBERTAS,
                   cidades_por_uf, nome_por_geo, GEO0, DATA_ORIGEM, META, TETO_FATOR,
                   GEOJSON_UF, IDX_CHOROPLETH)
from figuras import (figura_mapa, figura_detalhe, cartao_info, resumo_cartao, horizontes,
                     tema as _tema, PLOT, CORES_NIVEL, ORDEM_NIVEL, centro_zoom, sem_serie)
from layout import construir_conteudo, serve_layout, opcoes_uf, cabecalho_corrido, nav_links

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dengue.app")

app = Dash(__name__, title="Previsão de dengue no Brasil — LSTM",
           update_title=None, suppress_callback_exceptions=True,
           meta_tags=[{"name": "viewport",
                       "content": "width=device-width, initial-scale=1, viewport-fit=cover"},
                      # metadados acadêmicos (Google Scholar / OJS). SEM citation_pdf_url (não há PDF).
                      {"name": "citation_title", "content": conteudo.T_ARTIGO["artigo_titulo"]["pt"]},
                      {"name": "citation_author", "content": "Colque, Fernando Aramis"},
                      {"name": "citation_publication_date", "content": "2026/10/21"},
                      {"name": "citation_language", "content": "pt"},
                      {"name": "citation_keywords",
                       "content": "dengue; time-series forecasting; LSTM; conformal prediction; "
                                  "epidemiological surveillance"},
                      {"name": "citation_dissertation_institution",
                       "content": "Universidade Tecnológica Federal do Paraná"},
                      {"name": "DC.title", "content": conteudo.T_ARTIGO["artigo_titulo"]["pt"]},
                      {"name": "DC.creator", "content": "Colque, Fernando Aramis"},
                      {"name": "DC.date", "content": "2026-10-21"},
                      {"name": "DC.language", "content": "pt"},
                      {"property": "og:type", "content": "article"},
                      {"property": "og:title", "content": conteudo.T_ARTIGO["artigo_titulo"]["pt"]}])
# Fontes auto-hospedadas em assets/fonts/ (self-host, WS2/F1): o Dash carrega assets/fonts.css
# automaticamente; sem dependência do Google Fonts (ver CSP: font-src 'self', style-src sem o Google).
server = app.server
Compress(server)   # gzip/brotli nas respostas (corta o payload do geojson/JS)

# script no <head>: aplica o tema antes da pintura (evita flash) e acompanha o sistema
app.index_string = """<!DOCTYPE html>
<html lang="pt">
<head>
  {%metas%}<meta name="theme-color" content="#1C2620"><title>{%title%}</title>{%favicon%}
  <link rel="preload" href="/assets/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/source-serif-4-var.woff2" as="font" type="font/woff2" crossorigin>
  {%css%}
  <script>
  (function(){try{
    var L=['pt','en','es'], q=(new URLSearchParams(location.search).get('lang')||'').toLowerCase();
    var l=L.indexOf(q)>=0?q:(localStorage.getItem('lang')||(navigator.language||'').slice(0,2).toLowerCase());
    if(L.indexOf(l)>=0) document.documentElement.lang=l;   // WCAG 3.1.1 antes do boot (callback reafirma)
    var c = localStorage.getItem('tema') || 'system';
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var dark = c==='dark' || (c==='system' && mq.matches);
    var tc = function(d){var m=document.querySelector('meta[name="theme-color"]'); if(m) m.setAttribute('content', d?'#0E1113':'#1C2620');};
    document.documentElement.setAttribute('data-theme', dark?'dark':'light'); tc(dark);
    if(localStorage.getItem('cvd')==='on') document.documentElement.setAttribute('data-cvd','on');
    if(localStorage.getItem('motion')==='off') document.documentElement.setAttribute('data-motion','off');
    mq.addEventListener('change', function(e){
      if((localStorage.getItem('tema')||'system')==='system'){
        var d=e.matches; document.documentElement.setAttribute('data-theme', d?'dark':'light'); tc(d);}
    });
  }catch(e){}})();
  </script>
</head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>"""

# JSON-LD ScholarlyArticle (estático, gerado em Python — não usa dado do usuário). Injetado após o CSS.
_JSONLD = json.dumps({
    "@context": "https://schema.org", "@type": "ScholarlyArticle",
    "headline": conteudo.T_ARTIGO["artigo_titulo"]["pt"],
    "author": {"@type": "Person", "name": "Fernando Aramis Colque",
               **({"identifier": conteudo.ORCID_URL} if conteudo.ORCID else {})},
    "inLanguage": "pt", "datePublished": "2026-10-21", "url": conteudo.PUBLIC_URL + "/",
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "publisher": {"@type": "Organization", "name": "Universidade Tecnológica Federal do Paraná"},
}, ensure_ascii=False)
app.index_string = app.index_string.replace(
    "{%css%}", '{%css%}\n  <script type="application/ld+json">' + _JSONLD + "</script>")

# Shell estático de cold-start (A4): o Render free pode levar ~1 min para acordar; sem isto o
# visitante (e crawlers) veem só "Loading...". Overlay FIXED (não entra no fluxo → não gera CLS);
# removido por JS quando o layout real (.topbar) monta. <noscript> dá caminho ao estudo.
_TITULO_BOOT = conteudo.T_ARTIGO["artigo_titulo"]["pt"]
def _boot_bloco(l):
    return ('<div class="boot-l" lang="' + l + '"><p class="boot-lede">' + tr(l, "boot_lede") + '</p>'
            '<p class="boot-msg">' + tr(l, "boot_msg") + '</p></div>')


_BOOT_SHELL = (
    '<div id="boot-shell"><div class="boot-inner">'
    '<div class="boot-brand"><span class="boot-dot"></span><span translate="no">' + tr("en", "brand") + '</span></div>'
    '<h1 class="boot-title" lang="pt">' + _TITULO_BOOT + '</h1>'
    '<div class="boot-skeleton" aria-hidden="true"><span></span><span></span><span></span></div>'
    + "".join(_boot_bloco(l) for l in ("pt", "en", "es")) +
    '</div><noscript><p class="boot-noscript">'
    + "".join('<span class="boot-l" lang="' + l + '">' + tr(l, "boot_noscript") + '</span>' for l in ("pt", "en", "es"))
    + '<a href="' + conteudo.LINKS["zenodo"] + '" translate="no">DOI 10.5281/zenodo.13328231</a>.</p></noscript></div>'
)
_BOOT_HIDE = (
    '<script>(function(){var s=document.getElementById("boot-shell");if(!s)return;'
    'function done(){s.classList.add("boot-hidden");setTimeout(function(){'
    'if(s&&s.parentNode)s.parentNode.removeChild(s);},450);}'
    'var t=setInterval(function(){if(document.querySelector(".topbar")){clearInterval(t);done();}},120);'
    'setTimeout(function(){clearInterval(t);done();},60000);})();</script>'
)
app.index_string = app.index_string.replace("{%app_entry%}", _BOOT_SHELL + "{%app_entry%}" + _BOOT_HIDE)


@server.after_request
def _cabecalhos_seguranca(resp):
    """Hardening de exposição (OWASP A05). Cabeçalhos de segurança + CSP.

    A CSP fica em **Report-Only de propósito** — e assim permanece (decisão documentada, NÃO um
    TODO de "promover a enforce depois"). Enforçá-la quebraria o app por dois motivos estruturais
    e irredutíveis:
      1. O renderer do Dash injeta config inline e avalia bundles em runtime → exige
         `script-src 'unsafe-inline' 'unsafe-eval'`, o que já esvazia a proteção anti-XSS que uma
         CSP enforçada traria.
      2. As camadas de mapa (MapLibre GL, via Scattermap/Choroplethmap) criam Web Workers a partir
         de `blob:` → exigem `worker-src blob:`.
    Com esses relaxamentos obrigatórios, uma CSP *enforçada* agregaria pouco sobre os demais
    cabeçalhos. E o app é público, read-only, SEM auth / cookie de sessão / entrada de usuário /
    caminho de escrita — o impacto prático de um XSS aqui é mínimo. Mantemos a política completa e
    correta no cabeçalho como documentação executável e para gerar telemetria útil caso um coletor
    (`report-to` / `report-uri`) seja adicionado. (Opção B do diagnóstico de segurança.)
    """
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    # HSTS (o proxy do host, ex.: Render, termina o TLS) + Permissions-Policy (desliga APIs sensíveis)
    resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    resp.headers.setdefault(
        "Content-Security-Policy-Report-Only",
        "default-src 'self'; "
        "img-src 'self' data: blob: https://*.basemaps.cartocdn.com; "
        # fontes auto-hospedadas (WS2/F1): sem Google em style-src/font-src
        "style-src 'self' 'unsafe-inline'; "
        "font-src 'self'; "
        # script-src: 'unsafe-inline'/'unsafe-eval' são EXIGIDOS pelo renderer do Dash (ver docstring)
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        # worker-src blob: é EXIGIDO pelos Web Workers do MapLibre GL (camadas do mapa)
        "worker-src 'self' blob:; "
        "connect-src 'self' https://*.basemaps.cartocdn.com https://*.tiles.mapbox.com; "
        # endurecimentos sem custo p/ o app (não usa iframe aninhado, <base>, form externo nem plugin)
        "frame-ancestors 'self'; base-uri 'self'; form-action 'self'; object-src 'none'")
    # Cache (WS1): estáticos versionados (Dash usa ?m=/hash) → imutável 1 ano; HTML e callbacks →
    # no-cache (senão o navegador "congela" tema/idioma de um render antigo).
    _p = request.path
    if _p.startswith("/_dash-component-suites/") or _p.startswith("/assets/"):
        # imutável SÓ para 200 (um 404/500 transitório não pode ficar 1 ano no cache) e só para o que é
        # versionado (?m=/hash). Fontes/ícones chegam sem ?m= (url() do CSS) → 1 dia, revalidável.
        if resp.status_code not in (200, 206):
            resp.headers["Cache-Control"] = "no-store"
        elif _p.startswith("/_dash-component-suites/") or request.args.get("m"):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            resp.headers["Cache-Control"] = "public, max-age=86400"
    elif _p == "/" or _p.startswith("/_dash-update-component") or _p == "/_dash-dependencies":
        resp.headers["Cache-Control"] = "no-cache"
    elif _p == "/_dash-layout":
        # o layout varia por Referer (?lang=&cidade=) e Accept-Language: nunca compartilhável por cache
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["Vary"] = "Accept-Encoding, Accept-Language, Referer"
    return resp


@server.route("/health")
def _health():
    """Liveness barato p/ o HEALTHCHECK do container — testa o processo, não re-renderiza a página."""
    return "ok", 200


@server.route("/CITATION.cff")
def _citation_cff():
    """Serve o CITATION.cff da raiz (para 'Como citar'). Herda os cabeçalhos de segurança."""
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "CITATION.cff"),
                     mimetype="text/plain")


app.layout = serve_layout
log.info("app pronto · %d cidades · origem %s%s", len(mapa_cid), DATA_ORIGEM,
         f" · coletado {META.get('coletado_em')}" if META.get("coletado_em") else "")


# ---------------------------------------------------------------- idioma
@app.callback(Output("lang", "data"),
              Input("lang-pt", "n_clicks"), Input("lang-en", "n_clicks"), Input("lang-es", "n_clicks"),
              prevent_initial_call=True)
def set_lang(a, b, c):
    return {"lang-pt": "pt", "lang-en": "en", "lang-es": "es"}[ctx.triggered_id]


@app.callback(Output("app-content", "children"),
              Output("running-header", "children"), Output("topnav", "children"),
              Input("lang", "data"), State("sel", "data"), State("url-cidade", "data"),
              State("theme-eff", "data"), State("cvd", "data"),
              prevent_initial_call=True)   # conteúdo já vem do serve_layout; re-render só ao TROCAR idioma
def render_content(lang, sel, url_cidade, tema, cvd):
    lang = resolver(lang)
    # preserva a seleção atual ao trocar de idioma (store sel). No boot, `lang` e `url-cidade` saem
    # na MESMA resposta do callback clientside, mas `sel` só é gravado depois (aplica_url_cidade):
    # sem este fallback o rebuild correria na frente e perderia a cidade da URL.
    alvo = sel if _geo_valido(sel) else (url_cidade if _geo_valido(url_cidade) else None)
    return (construir_conteudo(lang, alvo, tema or "light", bool(cvd)),
            cabecalho_corrido(lang), nav_links(lang))


app.clientside_callback(
    # além de pintar a pílula ativa, sincroniza o atributo <html lang> com o idioma da UI
    # (a11y: leitor de tela pronuncia no idioma certo — WCAG 3.1.1 "idioma da página").
    "function(l){l=(l||'en');try{document.documentElement.lang=l;}catch(e){}"
    "var on='seg on',off='seg';"
    "return [l=='pt'?on:off, l=='en'?on:off, l=='es'?on:off];}",
    Output("lang-pt", "className"), Output("lang-en", "className"), Output("lang-es", "className"),
    Input("lang", "data"))

# persiste o idioma ESCOLHIDO em localStorage — só em mudança real (prevent_initial_call), para não
# sobrescrever a preferência do usuário com o idioma do servidor no 1º render (A15).
app.clientside_callback(
    "function(l){try{if(l){localStorage.setItem('lang', l);}}catch(e){} return window.dash_clientside.no_update;}",
    Output("url-sync", "data", allow_duplicate=True),
    Input("lang", "data"), prevent_initial_call=True)


# ---------------------------------------------------------------- tema
@app.callback(Output("theme", "data"),
              Input("theme-light", "n_clicks"), Input("theme-system", "n_clicks"),
              Input("theme-dark", "n_clicks"), prevent_initial_call=True)
def set_theme(a, b, c):
    return {"theme-light": "light", "theme-system": "system", "theme-dark": "dark"}[ctx.triggered_id]


# aplica o tema (atributo + localStorage) e devolve o tema EFETIVO (claro/escuro) p/ os gráficos
app.clientside_callback(
    "function(choice, boot){try{"
    "var c = choice || localStorage.getItem('tema') || 'system';"
    "var dark = c==='dark' || (c==='system' && window.matchMedia('(prefers-color-scheme: dark)').matches);"
    "document.documentElement.setAttribute('data-theme', dark?'dark':'light');"
    "var _m=document.querySelector('meta[name=\\'theme-color\\']'); if(_m)_m.setAttribute('content', dark?'#0E1113':'#1C2620');"
    "localStorage.setItem('tema', c);"
    "return dark?'dark':'light';}catch(e){return 'light';}}",
    Output("theme-eff", "data"),
    Input("theme", "data"), Input("boot", "n_intervals"))

# A5 — fallback do mapa: se o WebGL não estiver disponível (navegador travado, headless sem GPU),
# o MapLibre não renderiza. Esconde o <Graph> do mapa e mostra a mensagem #mapa-fallback (que aponta
# para os seletores e a Tabela 1, ambos independentes de WebGL). hidden=ok: visível só quando falha.
app.clientside_callback(
    "function(n){try{"
    "var c=document.createElement('canvas');"
    "var gl=c.getContext('webgl2')||c.getContext('webgl')||c.getContext('experimental-webgl');"
    "var ok=!!gl; var de=document.documentElement;"
    "if(ok){de.removeAttribute('data-webgl');} else {de.setAttribute('data-webgl','off');}"
    "return ok;"
    "}catch(e){document.documentElement.setAttribute('data-webgl','off'); return false;}}",
    Output("mapa-fallback", "hidden"),
    Input("boot", "n_intervals"))

# ---------------------------------------------------------------- menu de acessibilidade (F-A11y)
# Aplica as opções: data-cvd (paleta p/ daltonismo) e data-motion=off (reduzir movimento) no <html>,
# persiste em localStorage e devolve o flag `cvd` (para o rebuild do mapa). data-motion=off é lido
# também pelo script pré-paint (sem flash).
app.clientside_callback(
    "function(vals){try{"
    "vals = vals || []; var de=document.documentElement;"
    "var cvd = vals.indexOf('cvd')>=0, motion = vals.indexOf('motion')>=0;"
    "if(cvd){de.setAttribute('data-cvd','on'); localStorage.setItem('cvd','on');}"
    "else {de.removeAttribute('data-cvd'); localStorage.setItem('cvd','off');}"
    "if(motion){de.setAttribute('data-motion','off'); localStorage.setItem('motion','off');}"
    "else {de.removeAttribute('data-motion'); localStorage.setItem('motion','on');}"
    "return cvd;}catch(e){return false;}}",
    Output("cvd", "data"),
    Input("a11y-opts", "value"),
    prevent_initial_call=True)

# restaura as opções do localStorage no boot (dispara o callback acima)
app.clientside_callback(
    "function(n){try{var v=[];"
    "if(localStorage.getItem('cvd')==='on') v.push('cvd');"
    "if(localStorage.getItem('motion')==='off') v.push('motion');"
    "return v;}catch(e){return [];}}",
    Output("a11y-opts", "value"),
    Input("boot", "n_intervals"))


# relocaliza rótulos do menu a11y quando o idioma muda (a barra_controles não é re-renderizada)
@app.callback(Output("a11y-opts", "options"), Output("a11y-pop-title", "children"),
              Input("lang", "data"))
def localiza_a11y(lang):
    lg = resolver(lang)
    return ([{"label": tr(lg, "a11y_cvd"), "value": "cvd"},
             {"label": tr(lg, "a11y_motion"), "value": "motion"}], tr(lg, "a11y_titulo"))

app.clientside_callback(
    "function(choice){var c=choice||(localStorage.getItem('tema')||'system');var on='seg on',off='seg';"
    "return [c=='light'?on:off, c=='system'?on:off, c=='dark'?on:off];}",
    Output("theme-light", "className"), Output("theme-system", "className"),
    Output("theme-dark", "className"), Input("theme", "data"))

# no boot, sincroniza o store com a escolha persistida (para a pílula/rótulo já virem certos)
app.clientside_callback(
    "function(n){try{return localStorage.getItem('tema')||'system';}catch(e){return 'system';}}",
    Output("theme", "data", allow_duplicate=True), Input("boot", "n_intervals"),
    prevent_initial_call=True)


@app.callback(Output("theme-label", "children"), Input("theme", "data"), Input("lang", "data"))
def rotulo_tema(choice, lang):
    choice = choice or "system"
    return tr(resolver(lang), f"tema_{choice}")


# recolore o MAPA no tema via Patch — atualiza só estilo/cores, SEM reenviar o geojson (~128 KB)
@app.callback(Output("mapa", "figure", allow_duplicate=True), Input("theme-eff", "data"),
              prevent_initial_call=True)
def tema_mapa(tnome):
    p = _tema(tnome or "light")
    patch = Patch()
    patch["layout"]["map"]["style"] = p["mapstyle"]
    patch["layout"]["font"]["color"] = p["ink"]
    patch["layout"]["legend"]["font"]["color"] = p["ink"]
    patch["layout"]["legend"]["title"]["font"]["color"] = p["ink"]
    patch["layout"]["legend"]["bgcolor"] = p["legbg"]
    patch["layout"]["legend"]["bordercolor"] = p["legbd"]
    patch["layout"]["hoverlabel"]["bgcolor"] = p["hover_bg"]       # tooltip segue o tema (contraste)
    patch["layout"]["hoverlabel"]["bordercolor"] = p["hover_bd"]
    patch["layout"]["hoverlabel"]["font"]["color"] = p["ink"]
    patch["data"][IDX_CHOROPLETH]["colorscale"] = p["escala"]
    patch["data"][IDX_CHOROPLETH]["marker"]["line"]["color"] = p["mapline"]
    patch["data"][IDX_CHOROPLETH]["marker"]["line"]["width"] = p["maplinew"]
    if NAO_COBERTAS:
        patch["data"][0]["marker"]["line"]["color"] = p["mapline"]
        patch["data"][0]["marker"]["line"]["width"] = p["maplinew"]                      # camada "sem cobertura" (índice 0) acompanha o tema
        patch["data"][0]["colorscale"] = [[0, p["naocob"]], [1, p["naocob"]]]
    return patch


# ---------------------------------------------------------------- UF -> cidades (fallback estadual)
_UFS_SET = set(UFS)


@app.callback(Output("dd-cidade", "options"), Output("dd-cidade", "value"),
              Input("dd-uf", "value"), Input("lang", "data"))
def popular_cidades(uf, lang):
    lang = resolver(lang)
    uf = uf if isinstance(uf, str) and (uf == "BR" or uf in _UFS_SET) else "BR"
    if uf == "BR" or not uf:
        todas = sorted(((n, g) for lst in cidades_por_uf.values() for n, g in lst))
        return [{"label": n, "value": g} for n, g in todas], no_update
    cidades = cidades_por_uf.get(uf, [])
    rotulo = f"◼ {nome_uf.get(uf, uf)} ({tr(lang, 'escopo_estado').lower()})"
    opts = [{"label": rotulo, "value": f"UF-{uf}"}] + [{"label": n, "value": g} for n, g in cidades]
    # Input("lang") só traduz os rótulos: gravar o value aqui reverteria a cidade escolhida ao estado
    return opts, (no_update if ctx.triggered_id == "lang" else f"UF-{uf}")


def _geo_valido(g):
    """WS6: valida geo vindo do cliente (POST forjável) → permite fallback seguro, nunca exceção."""
    if not g or not isinstance(g, str):        # int/lista forjados → inválido (antes: AttributeError/500)
        return False
    if g.startswith("UF-"):
        return g[3:] in _UFS_SET
    return g in nome_por_geo


# WS5: um ÚNICO handler de clique no mapa — bolha de cidade → dd-cidade; estado → dd-uf (ambos validados).
@app.callback(Output("dd-uf", "value"), Output("dd-cidade", "value", allow_duplicate=True),
              Input("mapa", "clickData"), prevent_initial_call=True)
def clique_mapa(click):
    if not click:
        return no_update, no_update
    try:
        pt = click["points"][0]
        cd = pt.get("customdata")
        if isinstance(cd, str) and cd in nome_por_geo:       # bolha de cidade
            return no_update, cd
        loc = pt.get("location")
        if isinstance(loc, str) and loc in _UFS_SET:         # estado (choropleth)
            return loc, no_update
    except (KeyError, IndexError, TypeError, AttributeError):   # payload forjado → ignora
        pass
    return no_update, no_update


# reconstrói a figura do mapa só quando muda o IDIOMA (traduz hover/legenda/traços) — carrega o
# tema efetivo; tema puro é tratado por tema_mapa via Patch.
@app.callback(Output("mapa", "figure"),
              Input("lang", "data"), Input("cvd", "data"),
              State("dd-uf", "value"), State("theme-eff", "data"),
              prevent_initial_call=True)
def remapa_idioma(lang, cvd, uf, tema):
    uf = uf if isinstance(uf, str) and (uf == "BR" or uf in _UFS_SET) else "BR"
    return figura_mapa(uf, resolver(lang), tema or "light", cvd=bool(cvd))


# mudança de UF: só recentra/dá zoom via Patch — NÃO reenvia o geojson (~128 KB) a cada clique.
@app.callback(Output("mapa", "figure", allow_duplicate=True),
              Input("dd-uf", "value"), prevent_initial_call=True)
def zoom_uf(uf):
    uf = uf if isinstance(uf, str) and (uf == "BR" or uf in _UFS_SET) else "BR"
    centro, zoom = centro_zoom(uf)
    patch = Patch()
    patch["layout"]["map"]["center"] = centro
    patch["layout"]["map"]["zoom"] = zoom
    return patch


# a seleção vem SEMPRE do dd-cidade (o clique no mapa já atualiza o dd-cidade acima → fluxo único)
@app.callback(Output("sel", "data"), Input("dd-cidade", "value"), prevent_initial_call=True)
def selecionar(cidade):
    return cidade if _geo_valido(cidade) else no_update


@app.callback(Output("cartao", "children"), Output("detalhe", "figure"),
              Output("horizontes", "children"), Output("cartao-status", "children"),
              Output("legenda-serie", "hidden"),
              Input("sel", "data"), Input("lang", "data"), Input("theme-eff", "data"))
def atualizar(geo_id, lang, tema):
    lang, tema = resolver(lang), (tema or "light")
    if not _geo_valido(geo_id):                 # WS6: geo ausente/forjado → seleção inicial segura
        geo_id = GEO0
    return (cartao_info(geo_id, lang), figura_detalhe(geo_id, lang, tema),
            horizontes(geo_id, lang), resumo_cartao(geo_id, lang),
            bool(sem_serie(geo_id)))            # legenda da série só faz sentido com série (estado sem cobertura: oculta)


# anúncio "Copiado" para leitor de tela ao usar os botões de copiar (NEW/A14)
@app.callback(Output("copia-status", "children"),
              Input("clip-abnt", "n_clicks"), Input("clip-bibtex", "n_clicks"),
              State("lang", "data"), prevent_initial_call=True)
def anuncia_copia(_a, _b, lang):
    return tr(resolver(lang), "copiado")


# A15 — espelha idioma + seleção na URL (replaceState: não empilha histórico; link compartilhável).
# Usa o store `sel` (fonte canônica da seleção, imune ao rebuild de render_content), não o dd-cidade.
# Tema/cvd/motion ficam no localStorage, não na URL.
app.clientside_callback(
    "function(lang, sel){try{"
    "var p=new URLSearchParams(window.location.search);"
    "if(lang){p.set('lang', lang);}"
    "if(sel!=null && sel!==''){p.set('cidade', String(sel));}"
    "var qs=p.toString();"
    "var u=window.location.pathname + (qs?('?'+qs):'') + window.location.hash;"
    "window.history.replaceState(null, '', u);"
    "}catch(e){} return window.dash_clientside.no_update;}",
    Output("url-sync", "data"),
    Input("lang", "data"), Input("sel", "data"),
    prevent_initial_call=True)

# A15 — LEITURA da URL no boot (clientside; a query não chega ao serve_layout, que é servido via
# /_dash-layout). Define sel (→ atualizar renderiza a cidade) + dd-uf/dd-cidade (dropdowns) + idioma.
# Como render_content respeita o State("sel"), o rebuild ao aplicar o idioma NÃO reseta a seleção.
app.clientside_callback(
    "function(n, search, srv){var nu=window.dash_clientside.no_update; var o=[nu,nu];"
    "try{var ok=['pt','en','es'];"
    "var p=new URLSearchParams(search||window.location.search||'');"
    "var urlLang=(p.get('lang')||'').toLowerCase();"
    "var lsLang=null; try{lsLang=localStorage.getItem('lang');}catch(e){}"
    "var target=(urlLang&&ok.indexOf(urlLang)>=0)?urlLang:((lsLang&&ok.indexOf(lsLang)>=0)?lsLang:null);"
    "if(target && target!==srv){o[0]=target;}"
    "var cid=p.get('cidade');"
    "if(cid){o[1]=(cid.length<=16 && /^(UF-[A-Za-z]{2}|[0-9]{1,10})$/.test(cid))?cid:'invalida';}"   # forma/tamanho inválidos nem sobem ao servidor; 'invalida' faz o servidor normalizar a URL para GEO0          # texto CRU: quem valida é o servidor (aplica_url_cidade)
    "}catch(e){} return o;}",
    Output("lang", "data", allow_duplicate=True),
    Output("url-cidade", "data"),
    Input("boot", "n_intervals"), State("url", "search"), State("lang", "data"),
    prevent_initial_call=True)


@app.callback(Output("sel", "data", allow_duplicate=True),
              Output("dd-uf", "value", allow_duplicate=True),
              Output("dd-cidade", "value", allow_duplicate=True),
              Input("url-cidade", "data"), prevent_initial_call=True)
def aplica_url_cidade(raw):
    """A15 — aplica ?cidade= vindo da URL. Valor forjado/inexistente → seleção inicial segura (GEO0),
    nunca um dropdown vazio nem a string da URL ecoada de volta."""
    if not raw:
        return no_update, no_update, no_update
    if not _geo_valido(raw):
        return GEO0, no_update, no_update          # dropdowns já estão em GEO0; só normaliza sel/URL
    if raw.startswith("UF-"):
        return raw, raw[3:], raw
    return raw, no_update, raw


if __name__ == "__main__":
    app.run(debug=os.environ.get("DASH_DEBUG") == "1",
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8050")))
