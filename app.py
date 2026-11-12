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
from figuras import (figura_mapa, figura_detalhe, cartao_info, horizontes, tema as _tema, PLOT,
                     CORES_NIVEL, ORDEM_NIVEL, centro_zoom)
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
  {%metas%}<title>{%title%}</title>{%favicon%}{%css%}
  <script>
  (function(){try{
    var c = localStorage.getItem('tema') || 'system';
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var dark = c==='dark' || (c==='system' && mq.matches);
    document.documentElement.setAttribute('data-theme', dark?'dark':'light');
    mq.addEventListener('change', function(e){
      if((localStorage.getItem('tema')||'system')==='system')
        document.documentElement.setAttribute('data-theme', e.matches?'dark':'light');
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
        # força: o Dash seta um Cache-Control próprio; estes caminhos são versionados (?m=/hash)
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif _p == "/" or _p.startswith("/_dash-update-component"):
        resp.headers["Cache-Control"] = "no-cache"
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
              Input("lang", "data"))
def render_content(lang):
    lang = resolver(lang)
    return construir_conteudo(lang), cabecalho_corrido(lang), nav_links(lang)


app.clientside_callback(
    # além de pintar a pílula ativa, sincroniza o atributo <html lang> com o idioma da UI
    # (a11y: leitor de tela pronuncia no idioma certo — WCAG 3.1.1 "idioma da página").
    "function(l){l=(l||'en');try{document.documentElement.lang=l;}catch(e){}"
    "var on='seg on',off='seg';"
    "return [l=='pt'?on:off, l=='en'?on:off, l=='es'?on:off];}",
    Output("lang-pt", "className"), Output("lang-en", "className"), Output("lang-es", "className"),
    Input("lang", "data"))


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
    "localStorage.setItem('tema', c);"
    "return dark?'dark':'light';}catch(e){return 'light';}}",
    Output("theme-eff", "data"),
    Input("theme", "data"), Input("boot", "n_intervals"))

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
    if NAO_COBERTAS:                      # camada "sem cobertura" (índice 0) acompanha o tema
        patch["data"][0]["colorscale"] = [[0, p["naocob"]], [1, p["naocob"]]]
    return patch


# ---------------------------------------------------------------- UF -> cidades (fallback estadual)
@app.callback(Output("dd-cidade", "options"), Output("dd-cidade", "value"),
              Input("dd-uf", "value"), Input("lang", "data"))
def popular_cidades(uf, lang):
    lang = resolver(lang)
    if uf == "BR" or not uf:
        todas = sorted(((n, g) for lst in cidades_por_uf.values() for n, g in lst))
        return [{"label": n, "value": g} for n, g in todas], no_update
    cidades = cidades_por_uf.get(uf, [])
    rotulo = f"◼ {nome_uf.get(uf, uf)} ({tr(lang, 'escopo_estado').lower()})"
    opts = [{"label": rotulo, "value": f"UF-{uf}"}] + [{"label": n, "value": g} for n, g in cidades]
    return opts, f"UF-{uf}"


_UFS_SET = set(UFS)


def _geo_valido(g):
    """WS6: valida geo vindo do cliente (POST forjável) → permite fallback seguro, nunca exceção."""
    if not g:
        return False
    if isinstance(g, str) and g.startswith("UF-"):
        return g[3:] in _UFS_SET
    return str(g) in nome_por_geo


# WS5: um ÚNICO handler de clique no mapa — bolha de cidade → dd-cidade; estado → dd-uf (ambos validados).
@app.callback(Output("dd-uf", "value"), Output("dd-cidade", "value", allow_duplicate=True),
              Input("mapa", "clickData"), prevent_initial_call=True)
def clique_mapa(click):
    if not click:
        return no_update, no_update
    pt = click["points"][0]
    cd = pt.get("customdata")
    if cd is not None and str(cd) in nome_por_geo:     # bolha de cidade
        return no_update, str(cd)
    loc = pt.get("location")
    if loc in _UFS_SET:                                 # estado (choropleth)
        return loc, no_update
    return no_update, no_update


# reconstrói a figura do mapa só quando muda o IDIOMA (traduz hover/legenda/traços) — carrega o
# tema efetivo; tema puro é tratado por tema_mapa via Patch.
@app.callback(Output("mapa", "figure"),
              Input("lang", "data"), State("dd-uf", "value"), State("theme-eff", "data"),
              prevent_initial_call=True)
def remapa_idioma(lang, uf, tema):
    return figura_mapa(uf, resolver(lang), tema or "light")


# mudança de UF: só recentra/dá zoom via Patch — NÃO reenvia o geojson (~128 KB) a cada clique.
@app.callback(Output("mapa", "figure", allow_duplicate=True),
              Input("dd-uf", "value"), prevent_initial_call=True)
def zoom_uf(uf):
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
              Output("horizontes", "children"),
              Input("sel", "data"), Input("lang", "data"), Input("theme-eff", "data"))
def atualizar(geo_id, lang, tema):
    lang, tema = resolver(lang), (tema or "light")
    if not _geo_valido(geo_id):                 # WS6: geo ausente/forjado → seleção inicial segura
        geo_id = GEO0
    return (cartao_info(geo_id, lang), figura_detalhe(geo_id, lang, tema),
            horizontes(geo_id, lang))


if __name__ == "__main__":
    app.run(debug=os.environ.get("DASH_DEBUG") == "1",
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8050")))
