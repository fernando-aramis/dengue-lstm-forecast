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
import re

from dash import Dash, Input, Output, Patch, State, ctx, dcc, html, no_update
from flask import Response, request, send_file
from flask_compress import Compress

import atual
import conteudo
from dados import (
    GEOJSON_UF,
    ORIGINAL,
    TETO_FATOR,
    UFS,
    csv_cidade,
    nome_uf,
)
from figuras import (
    CORES_NIVEL,
    ORDEM_NIVEL,
    PLOT,
    cartao_info,
    centro_zoom,
    comparacao_valida,
    figura_detalhe,
    figura_mapa,
    horizontes,
    indices_anel,
    resumo_cartao,
    sem_serie,
)
from figuras import tema as _tema
from i18n import resolver, tr
from layout import (
    atributos_fonte,
    cabecalho_corrido,
    construir_conteudo,
    nav_links,
    opcoes_uf,
    serve_layout,
    status_fonte,
)

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dengue.app")

app = Dash(__name__, title="Previsão de dengue no Brasil com LSTM",
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
                      # SEO (1.13): description, Open Graph completo e Twitter card. O HTML inicial é igual nos
                      # 3 idiomas (idioma resolvido no cliente): metatags em PT e SEM hreflang.
                      {"name": "description", "content": tr("pt", "meta_desc")},
                      {"property": "og:type", "content": "article"},
                      {"property": "og:title", "content": conteudo.T_ARTIGO["artigo_titulo"]["pt"]},
                      {"property": "og:description", "content": tr("pt", "meta_desc")},
                      {"property": "og:url", "content": conteudo.PUBLIC_URL + "/"},
                      {"property": "og:image", "content": conteudo.PUBLIC_URL + "/assets/og.png"},
                      {"property": "og:image:width", "content": "1200"},
                      {"property": "og:image:height", "content": "630"},
                      {"property": "og:image:alt", "content": tr("pt", "og_alt")},
                      {"property": "og:locale", "content": "pt_BR"},
                      {"property": "og:site_name", "content": "Previsão de dengue no Brasil"},
                      {"name": "twitter:card", "content": "summary_large_image"},
                      {"name": "twitter:title", "content": conteudo.T_ARTIGO["artigo_titulo"]["pt"]},
                      {"name": "twitter:description", "content": tr("pt", "meta_desc")},
                      {"name": "twitter:image", "content": conteudo.PUBLIC_URL + "/assets/og.png"}])
# Fontes auto-hospedadas em assets/fonts/ (self-host, WS2/F1): o Dash carrega assets/fonts.css
# automaticamente; sem dependência do Google Fonts (ver CSP: font-src 'self', style-src sem o Google).
server = app.server
Compress(server)   # gzip/brotli nas respostas (corta o payload do geojson/JS)

# script no <head>: aplica o tema antes da pintura (evita flash) e acompanha o sistema
app.index_string = """<!DOCTYPE html>
<html lang="pt">
<head>
  {%metas%}<link rel="canonical" href="__CANONICAL__"><meta name="theme-color" content="#1C2620"><title>{%title%}</title>{%favicon%}
  <link rel="preload" href="/assets/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/source-serif-4-var.woff2" as="font" type="font/woff2" crossorigin>
  {%css%}
  <script>
  (function(){try{
    var L=['pt','en','es'], q=(new URLSearchParams(location.search).get('lang')||'').toLowerCase();
    var l=L.indexOf(q)>=0?q:(localStorage.getItem('lang')||(navigator.language||'').slice(0,2).toLowerCase());
    if(L.indexOf(l)>=0){document.documentElement.lang=l; var TT=__TITULOS__; if(TT[l]) document.title=TT[l];}   // WCAG 3.1.1/2.4.2 antes do boot (callback reafirma)
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
    **({"dateModified": ORIGINAL.meta["coletado_em"][:10]} if str(ORIGINAL.meta.get("coletado_em", ""))[:4].isdigit() else {}),
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "publisher": {"@type": "Organization", "name": "Universidade Tecnológica Federal do Paraná"},
}, ensure_ascii=False)
app.index_string = app.index_string.replace("__CANONICAL__", conteudo.PUBLIC_URL + "/")
app.index_string = app.index_string.replace(
    "__TITULOS__", json.dumps({_l: tr(_l, "doc_title") for _l in ("pt", "en", "es")}, ensure_ascii=False))
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


def obter(fonte):
    """Conjunto da fonte pedida pelo cliente: 'atual' só se já estiver carregado; senão ORIGINAL."""
    if fonte == "atual":
        c = atual.global_atual().conjunto()
        if c is not None:
            return c
    return ORIGINAL


@server.route("/health")
def _health():
    """Liveness barato p/ o HEALTHCHECK do container — testa o processo, não re-renderiza a página."""
    return "ok", 200


@server.route("/dados/<geo_id>.csv")
def _dados_csv(geo_id):
    """P.2: download das previsões de uma cidade/estado. `geo_id` só vale se está no conjunto carregado
    (allowlist em memória; nada vira caminho de arquivo) e `fonte` só aceita original|atual."""
    fonte = request.args.get("fonte", "original")
    if fonte not in ("original", "atual"):
        return Response("fonte inválida (use original ou atual)\n", 400, mimetype="text/plain")
    c = ORIGINAL if fonte == "original" else atual.global_atual().conjunto()
    if c is None:
        return Response("dados atuais indisponíveis no momento; use fonte=original\n", 404, mimetype="text/plain")
    corpo = csv_cidade(c, geo_id, fonte)
    if corpo is None:
        return Response("geo_id desconhecido\n", 404, mimetype="text/plain")
    nome = re.sub(r"[^A-Za-z0-9_-]", "", str(geo_id))
    return Response(corpo, mimetype="text/csv", headers={
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="previsao_{nome}_{fonte}.csv"',
        "Cache-Control": "public, max-age=300", "X-Content-Type-Options": "nosniff"})


@server.route("/robots.txt")
def _robots():
    """Permite tudo e aponta o sitemap (1.14). Cache público de 1 h; herda os cabeçalhos de segurança."""
    corpo = f"User-agent: *\nAllow: /\n\nSitemap: {conteudo.PUBLIC_URL}/sitemap.xml\n"
    return Response(corpo, mimetype="text/plain", headers={"Cache-Control": "public, max-age=3600"})


@server.route("/sitemap.xml")
def _sitemap():
    """Apenas '/', coerente com o canonical único (1.14)."""
    corpo = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             f"  <url><loc>{conteudo.PUBLIC_URL}/</loc></url>\n</urlset>\n")
    return Response(corpo, mimetype="application/xml", headers={"Cache-Control": "public, max-age=3600"})


@server.route("/CITATION.cff")
def _citation_cff():
    """Serve o CITATION.cff da raiz (para 'Como citar'). Herda os cabeçalhos de segurança."""
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "CITATION.cff"),
                     mimetype="text/plain")


app.layout = serve_layout
log.info("app pronto · %d cidades · origem %s%s", len(ORIGINAL.mapa_cid), ORIGINAL.data_origem,
         f" · coletado {ORIGINAL.meta.get('coletado_em')}" if ORIGINAL.meta.get("coletado_em") else "")


# ---------------------------------------------------------------- idioma
@app.callback(Output("lang", "data"),
              Input("lang-pt", "n_clicks"), Input("lang-en", "n_clicks"), Input("lang-es", "n_clicks"),
              prevent_initial_call=True)
def set_lang(a, b, c):
    return {"lang-pt": "pt", "lang-en": "en", "lang-es": "es"}[ctx.triggered_id]


@app.callback(Output("app-content", "children"),
              Output("running-header", "children"), Output("topnav", "children"),
              Input("lang", "data"), Input("fonte", "data"),
              State("sel", "data"), State("url-cidade", "data"),
              State("theme-eff", "data"), State("cvd", "data"), State("cmp", "data"),
              prevent_initial_call=True)   # conteúdo já vem do serve_layout; re-render ao TROCAR idioma ou fonte
def render_content(lang, fonte, sel, url_cidade, tema, cvd, cmp):
    lang = resolver(lang)
    c = obter(fonte)
    fonte = "atual" if c is not ORIGINAL else "original"
    # preserva a seleção atual ao trocar de idioma (store sel). No boot, `lang` e `url-cidade` saem
    # na MESMA resposta do callback clientside, mas `sel` só é gravado depois (aplica_url_cidade):
    # sem este fallback o rebuild correria na frente e perderia a cidade da URL.
    alvo = sel if _geo_valido(sel, c) else (url_cidade if _geo_valido(url_cidade, c) else None)
    return (construir_conteudo(lang, alvo, tema or "light", bool(cvd), cmp, c=c, fonte=fonte),
            cabecalho_corrido(lang), nav_links(lang))


app.clientside_callback(
    # além de pintar a pílula ativa, sincroniza o atributo <html lang> com o idioma da UI
    # (a11y: leitor de tela pronuncia no idioma certo — WCAG 3.1.1 "idioma da página").
    "function(l){l=(l||'en');try{document.documentElement.lang=l;document.title=("
    + json.dumps({_l: tr(_l, "doc_title") for _l in ("pt", "en", "es")}, ensure_ascii=False) + ")[l]||document.title;}catch(e){}"
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


# ---------------------------------------------------------------- fonte dos dados (1.9)
@app.callback(Output("fonte", "data"),
              Input("fonte-original", "n_clicks"), Input("fonte-atual", "n_clicks"),
              prevent_initial_call=True)
def escolher_fonte(_o, _a):
    """Cliente pede a fonte; 'atual' só é aceita se já estiver carregada (senão mantém a atual).
    O Dash dispara este callback quando o seletor é RECRIADO (n_clicks None, p.ex. ao trocar o idioma);
    sem clique real não escreve `fonte` — senão cada troca de idioma refaria atualizar/revalidar e
    zeraria a comparação momentaneamente."""
    if not (ctx.triggered and ctx.triggered[0].get("value")):
        return no_update
    if ctx.triggered_id == "fonte-atual":
        return "atual" if atual.global_atual().conjunto() is not None else no_update
    return "original"


@app.callback(Output("fonte-status", "children"),
              Output("fonte-original", "aria-checked"), Output("fonte-original", "tabIndex"),
              Output("fonte-atual", "aria-checked"), Output("fonte-atual", "tabIndex"),
              Output("fonte-atual", "aria-disabled"),
              Output("poll-atual", "disabled"), Output("poll-atual", "interval"),
              Output("fonte", "data", allow_duplicate=True), Output("fonte-pedida", "data"),
              Input("poll-atual", "n_intervals"), Input("lang", "data"), Input("fonte", "data"),
              State("fonte-pedida", "data"), prevent_initial_call=True)
def poll_atual(_n, lang, fonte, pedida):
    """Atualiza status/estado dos botões a partir do atual.py; troca para 'atual' se foi pedido por
    ?fonte= e acabou de chegar; para o poll quando o estado fica estável."""
    est = atual.global_atual().estado()
    pronto = est["estado"] in (atual.DISPONIVEL, atual.DEFASADO)
    nova, limpa = no_update, no_update
    if pedida == "atual" and pronto:
        nova, limpa, fonte = "atual", None, "atual"
    a = atributos_fonte(est, fonte)
    parar = pronto or est["motivo"] == "desligado"
    intervalo = 4000 if est["estado"] == atual.CARREGANDO else 30000
    return (status_fonte(resolver(lang), est), a["original"]["aria-checked"], a["original"]["tabIndex"],
            a["atual"]["aria-checked"], a["atual"]["tabIndex"], a["atual"]["aria-disabled"],
            parar, intervalo, nova, limpa)


# ao trocar de fonte, a seleção/comparação são revalidadas contra o Conjunto ativo (fallback geo0)
@app.callback(Output("sel", "data", allow_duplicate=True), Output("cmp", "data", allow_duplicate=True),
              Input("fonte", "data"), State("sel", "data"), State("cmp", "data"), prevent_initial_call=True)
def revalidar_selecao(fonte, sel, cmp):
    c = obter(fonte)
    novo_sel = sel if _geo_valido(sel, c) else c.geo0
    novo_cmp = cmp if (isinstance(cmp, str) and cmp in c.nome_por_geo) else None
    return (no_update if novo_sel == sel else novo_sel), (no_update if novo_cmp == cmp else novo_cmp)


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
              State("fonte", "data"), prevent_initial_call=True)
def tema_mapa(tnome, fonte="original"):
    c = obter(fonte)
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
    patch["data"][c.idx_choropleth]["colorscale"] = p["escala"]
    patch["data"][c.idx_choropleth]["marker"]["line"]["color"] = p["mapline"]
    patch["data"][c.idx_choropleth]["marker"]["line"]["width"] = p["maplinew"]
    for i in indices_anel(c):                  # anéis das bolhas (cor do tema)
        patch["data"][i]["marker"]["color"] = p["ring"]
    if c.nao_cobertas:
        patch["data"][0]["marker"]["line"]["color"] = p["mapline"]
        patch["data"][0]["marker"]["line"]["width"] = p["maplinew"]                      # camada "sem cobertura" (índice 0) acompanha o tema
        patch["data"][0]["colorscale"] = [[0, p["naocob"]], [1, p["naocob"]]]
    return patch


# ---------------------------------------------------------------- UF -> cidades (fallback estadual)
_UFS_SET = set(UFS)


@app.callback(Output("dd-cidade", "options"), Output("dd-cidade", "value"),
              Input("dd-uf", "value"), Input("lang", "data"), State("fonte", "data"))
def popular_cidades(uf, lang, fonte="original"):
    lang = resolver(lang)
    por_uf = obter(fonte).cidades_por_uf
    uf = uf if isinstance(uf, str) and (uf == "BR" or uf in _UFS_SET) else "BR"
    if uf == "BR" or not uf:
        todas = sorted(((n, g) for lst in por_uf.values() for n, g in lst))
        return [{"label": n, "value": g} for n, g in todas], no_update
    cidades = por_uf.get(uf, [])
    rotulo = f"◼ {nome_uf.get(uf, uf)} ({tr(lang, 'escopo_estado').lower()})"
    opts = [{"label": rotulo, "value": f"UF-{uf}"}] + [{"label": n, "value": g} for n, g in cidades]
    # Input("lang") só traduz os rótulos: gravar o value aqui reverteria a cidade escolhida ao estado
    return opts, (no_update if ctx.triggered_id == "lang" else f"UF-{uf}")


def _geo_valido(g, c=ORIGINAL):
    """WS6: valida geo vindo do cliente (POST forjável) → permite fallback seguro, nunca exceção."""
    if not g or not isinstance(g, str):        # int/lista forjados → inválido (antes: AttributeError/500)
        return False
    if g.startswith("UF-"):
        return g[3:] in _UFS_SET
    return g in c.nome_por_geo


# WS5: um ÚNICO handler de clique no mapa — bolha de cidade → dd-cidade; estado → dd-uf (ambos validados).
@app.callback(Output("dd-uf", "value"), Output("dd-cidade", "value", allow_duplicate=True),
              Input("mapa", "clickData"), State("fonte", "data"), prevent_initial_call=True)
def clique_mapa(click, fonte="original"):
    nomes = obter(fonte).nome_por_geo
    if not click:
        return no_update, no_update
    try:
        pt = click["points"][0]
        cd = pt.get("customdata")
        if isinstance(cd, str) and cd in nomes:       # bolha de cidade
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
              State("dd-uf", "value"), State("theme-eff", "data"), State("fonte", "data"),
              prevent_initial_call=True)
def remapa_idioma(lang, cvd, uf, tema, fonte="original"):
    uf = uf if isinstance(uf, str) and (uf == "BR" or uf in _UFS_SET) else "BR"
    return figura_mapa(uf, resolver(lang), tema or "light", cvd=bool(cvd), c=obter(fonte))


# mudança de UF: só recentra/dá zoom via Patch — NÃO reenvia o geojson (~128 KB) a cada clique.
@app.callback(Output("mapa", "figure", allow_duplicate=True),
              Input("dd-uf", "value"), State("fonte", "data"), prevent_initial_call=True)
def zoom_uf(uf, fonte="original"):
    uf = uf if isinstance(uf, str) and (uf == "BR" or uf in _UFS_SET) else "BR"
    centro, zoom = centro_zoom(uf, obter(fonte))
    patch = Patch()
    patch["layout"]["map"]["center"] = centro
    patch["layout"]["map"]["zoom"] = zoom
    return patch


# a seleção vem SEMPRE do dd-cidade (o clique no mapa já atualiza o dd-cidade acima → fluxo único)
@app.callback(Output("sel", "data"), Input("dd-cidade", "value"), State("fonte", "data"),
              prevent_initial_call=True)
def selecionar(cidade, fonte="original"):
    return cidade if _geo_valido(cidade, obter(fonte)) else no_update


@app.callback(Output("cartao", "children"), Output("detalhe", "figure"),
              Output("horizontes", "children"), Output("cartao-status", "children"),
              Output("legenda-serie", "hidden"),
              Output("dd-comparar", "disabled"), Output("legenda-cmp", "hidden"),
              Output("legenda-cmp-nome", "children"),
              Input("sel", "data"), Input("lang", "data"), Input("theme-eff", "data"),
              Input("cmp", "data"), State("fonte", "data"))
def atualizar(geo_id, lang, tema, cmp, fonte="original"):
    lang, tema = resolver(lang), (tema or "light")
    c = obter(fonte)
    if not _geo_valido(geo_id, c):              # WS6: geo ausente/forjado → seleção inicial segura
        geo_id = c.geo0
    comp = comparacao_valida(geo_id, cmp, c)    # só município vs. outro município existente (valor forjado → None)
    nome_cmp = tr(lang, "serie_cmp", nome=c.nome_por_geo[comp]) if comp else ""
    return (cartao_info(geo_id, lang, c=c), figura_detalhe(geo_id, lang, tema, comp, c=c),
            horizontes(geo_id, lang, comp, c, atual.desempenho_vigente()), resumo_cartao(geo_id, lang, comp, c),
            bool(sem_serie(geo_id, c)),            # legenda da série só faz sentido com série (estado sem cobertura: oculta)
            geo_id.startswith("UF-"),           # comparar só vale entre municípios
            not comp, nome_cmp)
@app.callback(Output("cmp", "data"), Input("dd-comparar", "value"), State("fonte", "data"),
              prevent_initial_call=True)
def selecionar_cmp(valor, fonte="original"):
    """Comparação: valor do cliente validado (forjado/inexistente → sem comparação)."""
    return valor if (isinstance(valor, str) and valor in obter(fonte).nome_por_geo
                     and not valor.startswith("UF-")) else None


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
    "function(lang, sel, fonte){try{"
    "var p=new URLSearchParams(window.location.search);"
    "if(lang){p.set('lang', lang);}"
    "if(fonte==='atual'){p.set('fonte','atual');}else{p.delete('fonte');}"
    "if(sel!=null && sel!==''){p.set('cidade', String(sel));}"
    "var qs=p.toString();"
    "var u=window.location.pathname + (qs?('?'+qs):'') + window.location.hash;"
    "window.history.replaceState(null, '', u);"
    "}catch(e){} return window.dash_clientside.no_update;}",
    Output("url-sync", "data"),
    Input("lang", "data"), Input("sel", "data"), Input("fonte", "data"),
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
              Input("url-cidade", "data"), State("fonte", "data"), prevent_initial_call=True)
def aplica_url_cidade(raw, fonte="original"):
    """A15 — aplica ?cidade= vindo da URL. Valor forjado/inexistente → seleção inicial segura (GEO0),
    nunca um dropdown vazio nem a string da URL ecoada de volta."""
    if not raw:
        return no_update, no_update, no_update
    c = obter(fonte)
    if not _geo_valido(raw, c):
        return c.geo0, no_update, no_update          # dropdowns já estão em GEO0; só normaliza sel/URL
    if raw.startswith("UF-"):
        return raw, raw[3:], raw
    return raw, no_update, raw


if __name__ == "__main__":
    app.run(debug=os.environ.get("DASH_DEBUG") == "1",
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8050")))
