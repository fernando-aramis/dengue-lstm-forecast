# -*- coding: utf-8 -*-
"""
Layout da página: blocos editoriais, barra de controles (idioma/tema) e montagem
(`construir_conteudo` + `serve_layout`). Textos vêm de i18n; figuras vêm de figuras.py.
"""
import flask
from datetime import timedelta

from dash import dcc, html

from i18n import tr, resolver, nivel as nivel_tr, fmt_int
from dados import (UFS, nome_uf, DATA_ORIGEM, GEO0, cidades_por_uf, mapa_cid,
                   RESUMO, SE_H1, SE_ORIGEM, DATA_PREV_H1)
from figuras import (figura_mapa, figura_detalhe, cartao_info, horizontes,
                     CORES_NIVEL, ORDEM_NIVEL)


# ---------------------------------------------------------------- blocos reutilizáveis
def stat(big, lbl, tom=None):
    """KPI. tom: None (neutro) | 'brand' (fundo verde) | 'alarm' (número terracota)."""
    corpo = list(big) if isinstance(big, (list, tuple)) else [big]
    cls = "stat" + (f" stat--{tom}" if tom else "")
    return html.Div(className=cls, children=[
        html.Div(corpo, className="big"), html.Div(lbl, className="lbl")])


def situacao(lang):
    """Cartão 'Resumo da situação' do hero: total t+1 + barra empilhada + lista por nível."""
    _, se = SE_H1
    ini, fim = DATA_PREV_H1, DATA_PREV_H1 + timedelta(days=6)
    por, n = RESUMO["por_nivel"], RESUMO["n_cidades"]
    segs, aria = [], []
    for nv in ORDEM_NIVEL:
        c = por.get(nv, 0)
        if c:
            segs.append(html.Span(className="barra-seg",
                                  style={"flexGrow": c, "background": CORES_NIVEL[nv]}))
            aria.append(f"{c} {nivel_tr(lang, nv)}")
    linhas = [html.Div(className="sit-linha", children=[
        html.Span([html.Span(className=f"glifo {nv.lower()}", **{"aria-hidden": "true"}),
                   nivel_tr(lang, nv)], className=f"pill nivel-{nv.lower()}"),
        html.Span(f"{por.get(nv, 0)} "
                  f"{tr(lang, 'palavra_cidade' if por.get(nv, 0) == 1 else 'palavra_cidades')}",
                  className="sit-n tabular")]) for nv in ORDEM_NIVEL]
    return html.Div(className="situacao", children=[
        html.Span(tr(lang, "sit_eyebrow", se=se, ini=ini.strftime("%d/%m"),
                     fim=fim.strftime("%d/%m/%Y")), className="eyebrow"),
        html.Div(fmt_int(RESUMO["total_h1"], lang), className="sit-total tabular"),
        html.Div(tr(lang, "sit_total", n=n), className="sit-sub"),
        html.Div(segs, className="sit-barra", role="img",
                 **{"aria-label": tr(lang, "sit_barra_aria", n=n, lista=", ".join(aria))}),
        html.Div(linhas, className="sit-lista"),
        html.Div(tr(lang, "nota_nivel"), className="sit-nota aux"),
    ])


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
    origem_se = f"SE {SE_ORIGEM[1]}/{SE_ORIGEM[0]} ({DATA_ORIGEM})"
    full = tr(lang, "aviso", origem=origem_se)
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
    itens = [html.Span([html.Span(className=f"glifo {nv.lower()}", **{"aria-hidden": "true"}),
                        nivel_tr(lang, nv)], className="leg-item") for nv in ORDEM_NIVEL]
    itens.append(html.Span([html.Span(className="glifo sem-dado", **{"aria-hidden": "true"}),
                            tr(lang, "leg_sem_dado")], className="leg-item"))
    return html.Div(className="map-legend",
                    children=[html.Span(tr(lang, "legend_title"), className="leg-label"), *itens])


def legenda_serie(lang):
    """Legenda do gráfico de detalhe em HTML (fora do canvas) — Observado/Previsto/Intervalo/Origem."""
    _, se = SE_ORIGEM
    def item(cls, texto):
        return html.Span([html.Span(className=f"serie-sw {cls}"), texto], className="serie-item")
    return html.Div(className="serie-legend", children=[
        item("obs", tr(lang, "serie_obs")), item("prev", tr(lang, "serie_prev")),
        item("int", tr(lang, "serie_int")), item("orig", tr(lang, "serie_origem", se=se))])


def tabela_ranking(lang, n=8):
    """Tabela 1 — maiores previsões (alternativa textual acessível ao mapa)."""
    _, se = SE_H1
    top = mapa_cid.sort_values("prev", ascending=False).head(n)
    linhas = []
    for _, r in top.iterrows():
        nv = r["nivel_alerta"]
        linhas.append(html.Tr([
            html.Td(f"{r['nome']} ({r['uf']})", className="tab-cidade"),
            html.Td(fmt_int(r["prev"], lang), className="tabular"),
            html.Td(fmt_int(r["inf"], lang), className="tabular"),
            html.Td(fmt_int(r["sup"], lang), className="tabular"),
            html.Td(html.Span([html.Span(className=f"glifo {nv.lower()}", **{"aria-hidden": "true"}),
                               nivel_tr(lang, nv)], className=f"pill nivel-{nv.lower()}"))]))
    return html.Div(className="tbl-wrap", children=[html.Table(className="res tab-rank", children=[
        html.Caption([html.Strong("Tabela 1. "), tr(lang, "tab1_caption", se=se)]),
        html.Thead(html.Tr([html.Th(tr(lang, "tab1_cidade")), html.Th(tr(lang, "tab1_prev")),
                            html.Th(tr(lang, "tab1_inf")), html.Th(tr(lang, "tab1_sup")),
                            html.Th(tr(lang, "tab1_nivel"))])),
        html.Tbody(linhas)])])


def construir_conteudo(lang):
    return [
        # hero (capa dos slides: fundo verde full-bleed + resumo da situação)
        html.Header(className="hero", children=[
            html.Div(className="wrap hero-grid", children=[
                html.Div(className="hero-main", children=[
                    html.Div(className="chips", children=[
                        html.Span(tr(lang, "chip1"), className="chip chip--inverse"),
                        html.Span(tr(lang, "chip2"), className="chip chip--inverse"),
                        html.Span(tr(lang, "chip3"), className="chip chip--inverse"),
                        html.Span(tr(lang, "chip4"), className="chip chip--inverse")]),
                    html.Span(tr(lang, "hero_eyebrow"), className="eyebrow eyebrow--inverse"),
                    html.H1([tr(lang, "h1"), html.Br(),
                             html.Span(tr(lang, "h1_acento"), className="acento")]),
                    html.P(tr(lang, "lede"), className="lede"),
                    html.Div(className="hero-autor", children=[
                        html.Strong("Fernando Aramis Colque"),
                        html.Span(tr(lang, "autor_afil"), className="hero-afil")]),
                    html.Div(className="hero-cta", children=[
                        html.A(tr(lang, "cta_painel"), href="#painel", className="btn btn--on-brand"),
                        html.A(tr(lang, "cta_artigo"), href="#artigo", className="btn btn--secondary"),
                        html.A(tr(lang, "cta_citar"), href="#como-citar", className="btn btn--ghost")]),
                ]),
                situacao(lang),
            ]),
        ]),
        html.Div(className="faixa", **{"aria-hidden": "true"}),

        # indicadores: avisos (warn + info) + KPIs
        html.Section(id="indicadores", className="wrap indicadores", children=[
            html.Div(className="avisos", children=[
                html.Div(className="aviso warn", children=[
                    html.Span("⚠"),
                    html.Span([html.Strong(tr(lang, "aviso_warn_t")), " ",
                               tr(lang, "aviso_warn_p")])]),
                _aviso(lang),
            ]),
            html.Div(className="stats", children=[
                stat([html.Span("913 "), html.Span("→", className="arrow"), html.Span(" 15.389")],
                     tr(lang, "stat1")),
                stat("−14%", tr(lang, "stat2"), tom="brand"),
                stat("94–98%", tr(lang, "stat3")),
                stat("1,16", tr(lang, "stat4b"), tom="alarm")]),
        ]),

        # ---- conteúdo em coluna de leitura (.wrap) ----
        html.Div(className="wrap", children=[

        # painel interativo (Figura 1)
        html.Section(id="painel", className="enter", **{"aria-labelledby": "painel-titulo"}, children=[
            html.Div(className="painel-head", children=[
                html.Div(className="sec-head", children=[
                    html.Span(tr(lang, "fig1_eyebrow"), className="eyebrow"),
                    html.H2(tr(lang, "map_h2"), id="painel-titulo")]),
                html.Span([html.Span(className="rec-dot", **{"aria-hidden": "true"}),
                           tr(lang, "recencia", se=SE_ORIGEM[1], ano=SE_ORIGEM[0])],
                          className="recencia mono")]),
            html.P(tr(lang, "map_sub", origem=DATA_ORIGEM), className="sec-sub"),
            html.Figure(className="figura", children=[
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
                        legenda_serie(lang),
                        dcc.Graph(id="detalhe", className="graph-detalhe",
                                  figure=figura_detalhe(GEO0, lang=lang),
                                  config={"displayModeBar": False, "responsive": True}),
                        html.Div(id="horizontes", children=horizontes(GEO0, lang))]),
                ]),
                html.Figcaption([html.Strong("Figura 1. "),
                                 tr(lang, "fig1_caption", se=SE_ORIGEM[1], ano=SE_ORIGEM[0])]),
            ]),
            html.Div(className="painel-extra", children=[
                tabela_ranking(lang),
                html.Div(className="como-ler", children=[
                    html.Span(tr(lang, "como_ler_t"), className="eyebrow eyebrow--inverse"),
                    html.Ol([html.Li(tr(lang, "como_ler_1")), html.Li(tr(lang, "como_ler_2")),
                             html.Li(tr(lang, "como_ler_3"))])]),
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

        ]),  # ---- fecha o .wrap de conteúdo ----

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
        html.Main(id="conteudo", children=html.Div(id="app-content",
                                                   children=construir_conteudo(lang))),
        dcc.Store(id="lang", storage_type="local", data=lang),
        dcc.Store(id="theme"),
        dcc.Store(id="theme-eff"),
        dcc.Store(id="sel"),
        dcc.Interval(id="boot", interval=80, n_intervals=0, max_intervals=1),
    ])
