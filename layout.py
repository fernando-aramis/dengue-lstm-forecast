# -*- coding: utf-8 -*-
"""
Layout da página: blocos editoriais, barra de controles (idioma/tema) e montagem
(`construir_conteudo` + `serve_layout`). Textos vêm de i18n; figuras vêm de figuras.py.
"""
import flask
from dash import dcc, html

from i18n import tr, resolver, nivel as nivel_tr
from dados import UFS, nome_uf, DATA_ORIGEM, GEO0, cidades_por_uf
from figuras import figura_mapa, figura_detalhe, cartao_info, CORES_NIVEL, ORDEM_NIVEL


# ---------------------------------------------------------------- blocos reutilizáveis
def stat(big, lbl, accent=False):
    corpo = list(big) if isinstance(big, (list, tuple)) else [big]
    return html.Div(className="stat accent" if accent else "stat", children=[
        html.Div(corpo, className="big"), html.Div(lbl, className="lbl")])


def card(ico, titulo, texto):
    return html.Div(className="card", children=[
        html.Div(ico, className="ico"), html.H3(titulo), html.P(texto)])


def finding(titulo, texto, warn=False):
    return html.Div(className="finding warn" if warn else "finding",
                    children=[html.H3(titulo), html.P(texto)])


TAB_RES = [  # (chave_modelo, E1h1, E1h4, E2h1, E2h4, colunas_destaque)
    ("mod_ingenuo", "4,8", "11,0", "72", "184", {3, 4}),
    ("mod_ingenuo_sazonal", "11,9", "11,9", "409", "409", set()),
    ("mod_a", "4,6", "9,5", "150", "274", {1, 2}),
    ("mod_b", "7,8", "10,4", "284", "354", set()),
    ("mod_c", "5,4", "9,5", "183", "306", set()),
]


def opcoes_uf(lang):
    return ([{"label": tr(lang, "brasil_todos"), "value": "BR"}]
            + [{"label": nome_uf.get(uf, uf), "value": uf} for uf in UFS])


def opcoes_cidade_br():
    """Todas as cidades (visão BR) — já no layout para o value=GEO0 resolver no 1º render
    (o dropdown do Dash descarta um value que não esteja nas opções iniciais)."""
    todas = sorted((n, g) for lst in cidades_por_uf.values() for n, g in lst)
    return [{"label": n, "value": g} for n, g in todas]


def _aviso(lang):
    full = tr(lang, "aviso", origem=DATA_ORIGEM)
    strong = tr(lang, "aviso_strong")
    resto = full[len(strong):] if full.startswith(strong) else full
    return html.Div(className="aviso info", children=[
        html.Span("ℹ"), html.Span([html.Strong(strong), resto])])


def _seg(tid, conteudo, aria):
    return html.Button(conteudo, id=tid, className="seg", n_clicks=0,
                       title=aria, **{"aria-label": aria})


def cabecalho_corrido(lang):
    """Running header JBCS (mono): curso/UTFPR à esquerda; dados/licença à direita."""
    return [
        html.Span(tr(lang, "rh_esq"), className="rh-esq"),
        html.Span(tr(lang, "rh_esq_curto"), className="rh-esq-curto"),
        html.Span(tr(lang, "rh_dir", licenca="CC BY 4.0"), className="rh-dir"),
    ]


_NAV = [("#painel", "nav_painel"), ("#artigo", "nav_artigo"), ("#sec-2", "nav_metodos"),
        ("#dados", "nav_dados"), ("#como-citar", "nav_citar")]


def nav_links(lang):
    """Navegação por âncora. Desktop = lista; ≤767px = <details> (sem JS)."""
    def itens():
        return [html.A(tr(lang, k), href=h, className="nav-a") for h, k in _NAV]
    return [
        html.Div(itens(), className="nav-desktop"),
        html.Details([html.Summary(tr(lang, "nav_menu")),
                      html.Div(itens(), className="nav-mobile-list")], className="nav-mobile"),
    ]


def barra_controles():
    return html.Div(className="controls", children=[
        html.Div(className="seg-group lang-group", role="group",
                 **{"aria-label": "Idioma / Language / Idioma"}, children=[
                     _seg("lang-pt", "PT", "Português"),
                     _seg("lang-en", "EN", "English"),
                     _seg("lang-es", "ES", "Español")]),
        html.Div(className="seg-group theme-group", role="group",
                 **{"aria-label": "Tema / Theme / Tema"}, children=[
                     _seg("theme-light", "☀", "Light"),
                     _seg("theme-system", "🖥", "System"),
                     _seg("theme-dark", "☾", "Dark"),
                     html.Span(id="theme-label", className="seg-label")]),
    ])


def legenda_niveis(lang):
    """Legenda dos níveis de alerta, em HTML sob o mapa (fora do canvas do Plotly).
    Cor + rótulo (segundo canal além da cor, ajuda daltônicos) e sem colidir com a atribuição."""
    itens = [html.Span([html.Span(className="leg-dot", style={"background": CORES_NIVEL[nv]}),
                        nivel_tr(lang, nv)], className="leg-item") for nv in ORDEM_NIVEL]
    return html.Div(className="map-legend",
                    children=[html.Span(tr(lang, "legend_title"), className="leg-label"), *itens])


def construir_conteudo(lang):
    return [
        # hero
        html.Header(className="hero", children=[
            html.Div(className="chips", children=[
                html.Span(tr(lang, "chip1"), className="chip solid"),
                html.Span(tr(lang, "chip2"), className="chip"),
                html.Span(tr(lang, "chip3"), className="chip"),
                html.Span(tr(lang, "chip4"), className="chip")]),
            html.H1(tr(lang, "h1")),
            html.P(tr(lang, "lede"), className="lede"),
            html.Div(className="stats", children=[
                stat([html.Span("913 "), html.Span("→", className="arrow"), html.Span(" 15.389")],
                     tr(lang, "stat1")),
                stat("−14%", tr(lang, "stat2"), accent=True),
                stat("94–98%", tr(lang, "stat3"), accent=True),
                stat("749", tr(lang, "stat4"))]),
            _aviso(lang),
        ]),

        # mapa + detalhe
        html.Section(className="enter", children=[
            html.Div(className="sec-head", children=[
                html.Span(tr(lang, "map_kicker"), className="kicker"),
                html.H2(tr(lang, "map_h2"))]),
            html.P(tr(lang, "map_sub", origem=DATA_ORIGEM), className="sec-sub"),
            html.Div(className="grid", children=[
                html.Div(className="panel panel-mapa", children=[
                    html.Div(className="pad", children=[
                        html.Div(className="controles", children=[
                            html.Div([html.Label(tr(lang, "lbl_estado")),
                                      dcc.Dropdown(id="dd-uf", options=opcoes_uf(lang), value="BR",
                                                   clearable=False)]),
                            html.Div([html.Label(tr(lang, "lbl_cidade")),
                                      dcc.Dropdown(id="dd-cidade", placeholder=tr(lang, "ph_cidade"),
                                                   options=opcoes_cidade_br(), value=GEO0,
                                                   clearable=False)])])]),
                    dcc.Graph(id="mapa", className="graph-mapa", figure=figura_mapa(lang=lang),
                              config={"displayModeBar": False, "scrollZoom": True, "responsive": True}),
                    legenda_niveis(lang),
                    html.Div(tr(lang, "map_hint"), className="map-hint")]),
                html.Div(className="panel panel-detalhe", children=[
                    html.Div(id="cartao", className="cartao", children=cartao_info(GEO0, lang)),
                    dcc.Graph(id="detalhe", className="graph-detalhe",
                              figure=figura_detalhe(GEO0, lang=lang),
                              config={"displayModeBar": False, "responsive": True})]),
            ]),
        ]),

        # como funciona
        html.Section(children=[
            html.Div(className="sec-head", children=[
                html.Span(tr(lang, "how_kicker"), className="kicker"),
                html.H2(tr(lang, "how_h2"))]),
            html.Div(className="cards", children=[
                card("12", tr(lang, "how1_t"), tr(lang, "how1_p")),
                card("LSTM", tr(lang, "how2_t"), tr(lang, "how2_p")),
                card("90%", tr(lang, "how3_t"), tr(lang, "how3_p")),
                card("SUS", tr(lang, "how4_t"), tr(lang, "how4_p"))]),
        ]),

        # o que o estudo encontrou
        html.Section(children=[
            html.Div(className="sec-head", children=[
                html.Span(tr(lang, "find_kicker"), className="kicker"),
                html.H2(tr(lang, "find_h2"))]),
            html.Div(className="findings", children=[
                finding(tr(lang, "find1_t"), tr(lang, "find1_p")),
                finding(tr(lang, "find2_t"), tr(lang, "find2_p"), warn=True),
                finding(tr(lang, "find3_t"), tr(lang, "find3_p"), warn=True),
                finding(tr(lang, "find4_t"), tr(lang, "find4_p"))]),
        ]),

        # resultados
        html.Section(children=[
            html.Div(className="sec-head", children=[
                html.Span(tr(lang, "res_kicker"), className="kicker"),
                html.H2(tr(lang, "res_h2"))]),
            html.Div(className="tbl-wrap", children=[html.Table(className="res", children=[
                html.Caption(tr(lang, "res_caption")),
                html.Thead(html.Tr([html.Th(tr(lang, "th_modelo")), html.Th(tr(lang, "th_e1h1")),
                                    html.Th(tr(lang, "th_e1h4")), html.Th(tr(lang, "th_e2h1")),
                                    html.Th(tr(lang, "th_e2h4"))])),
                html.Tbody([
                    html.Tr([html.Td(tr(lang, mk))] + [
                        html.Td(v, className="best" if i + 1 in dest else None)
                        for i, v in enumerate([a, b, c, dd])])
                    for mk, a, b, c, dd, dest in TAB_RES])])]),
            html.P(tr(lang, "res_note"), className="sec-sub", style={"marginTop": "14px"}),
        ]),

        # para onde vai
        html.Section(children=[
            html.Div(className="sec-head", children=[
                html.Span(tr(lang, "fut_kicker"), className="kicker"),
                html.H2(tr(lang, "fut_h2"))]),
            html.Div(className="cards", children=[
                card("➊", tr(lang, "fut1_t"), tr(lang, "fut1_p")),
                card("➋", tr(lang, "fut2_t"), tr(lang, "fut2_p")),
                card("➌", tr(lang, "fut3_t"), tr(lang, "fut3_p")),
                card("➍", tr(lang, "fut4_t"), tr(lang, "fut4_p"))]),
        ]),

        # rodapé (JBCS/slides): 3 colunas + aviso + faixa verde
        html.Footer(className="rodape", children=[
            html.Div(className="rodape-cols", children=[
                html.Div([html.H3(tr(lang, "rodape_sobre_t")), html.P(tr(lang, "rodape_sobre_p"))]),
                html.Div([html.H3(tr(lang, "rodape_dados_t")), html.P(tr(lang, "rodape_dados_p"))]),
                html.Div([html.H3(tr(lang, "rodape_lic_t")), html.P(tr(lang, "rodape_lic_p"))]),
            ]),
            html.P(tr(lang, "rodape_aviso"), className="rodape-aviso mono"),
            html.Div(className="faixa-fim", **{"aria-hidden": "true"}),
        ]),
    ]


def serve_layout():
    lang = resolver(flask.request.headers.get("Accept-Language", "") if flask.has_request_context() else "")
    return html.Div([
        html.A(tr(lang, "skip"), href="#conteudo", className="skip-link"),
        html.Div(id="running-header", className="running-header", children=cabecalho_corrido(lang)),
        html.Header(className="topbar", children=[html.Div(className="inner", children=[
            html.Div(className="brand", children=[
                html.Span(className="brand-dot"),
                html.Strong(tr(lang, "brand")),
                html.Span(tr(lang, "curso"), className="muted hide-sm")]),
            html.Nav(id="topnav", className="topnav", children=nav_links(lang),
                     **{"aria-label": tr(lang, "nav_label")}),
            barra_controles()])]),
        html.Main(id="conteudo", children=html.Div(id="app-content", className="wrap",
                                                   children=construir_conteudo(lang))),
        dcc.Store(id="lang", storage_type="local", data=lang),
        dcc.Store(id="theme"),
        dcc.Store(id="theme-eff"),
        dcc.Store(id="sel"),
        dcc.Interval(id="boot", interval=80, n_intervals=0, max_intervals=1),
    ])
