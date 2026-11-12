# -*- coding: utf-8 -*-
"""
Figuras Plotly (mapa, gráfico de detalhe) e o cartão de informação, com paleta por tema
(claro/escuro). Separado do app para manter os callbacks enxutos e testável isoladamente.
"""
import numpy as np
import plotly.graph_objects as go
from dash import html

from i18n import tr, nivel as nivel_tr, fmt_int
from dados import (GEOJSON_UF, mapa_uf, mapa_cid, nome_uf, COBERTAS, NAO_COBERTAS,
                   prev, hist, CORES_NIVEL, ORDEM_NIVEL, semana_epi)

# paletas de GRÁFICO por tema (coerentes com o CSS claro/escuro)
PLOT = {
    # 'escala' = choropleth ESTADUAL (previsão total). Matiz TEAL/ardósia, deliberadamente distinta
    # do verde→vermelho dos NÍVEIS de alerta (evita ler estado-verde + bolha-verde como "tudo ok").
    # 'mapline' = contorno dos estados; no CLARO é um traço escuro p/ a costa destacar do mar cinza
    # do basemap (positron); no ESCURO é branco suave (já aprovado). Piso da escala no claro puxa p/
    # teal visível, para a terra não sumir no mar.
    # 'hover_bg'/'hover_bd' = caixa de hover do Plotly (tooltip). Sem isto, o 'x unified' cai no
    # default (caixa semitransparente + fonte escura): no ESCURO fica texto escuro sobre fundo
    # escuro (ilegível). Fixamos fundo sólido do tema + fonte 'ink' p/ alto contraste nos dois temas.
    "light": {"ink": "#1C2620", "grid": "#E9E4D6", "axis": "#D9D4C7", "obs": "#1C2620",
              "prev": "#2F5A42", "band": "rgba(47,90,66,0.16)", "naocob": "#DCD7C6", "paper": "#FBFAF5",
              "mapstyle": "carto-positron", "legbg": "rgba(251,250,245,0.92)", "legbd": "#D9D4C7",
              "mapline": "rgba(64,92,98,0.60)", "maplinew": 0.8,
              "hover_bg": "#FBFAF5", "hover_bd": "#D9D4C7",
              "escala": [[0.0, "#D5E3E2"], [0.5, "#9FC2C6"], [1.0, "#3F6E78"]]},
    "dark":  {"ink": "#ECEFEA", "grid": "#2A3330", "axis": "#3A4541", "obs": "#ECEFEA",
              "prev": "#7FC894", "band": "rgba(127,200,148,0.22)", "naocob": "#262D30", "paper": "#1E2428",
              "mapstyle": "carto-darkmatter", "legbg": "rgba(30,36,40,0.92)", "legbd": "#313A39",
              "mapline": "rgba(255,255,255,0.50)", "maplinew": 0.6,
              "hover_bg": "#222A2D", "hover_bd": "#3A4541",
              "escala": [[0.0, "#20282A"], [0.5, "#315B63"], [1.0, "#79B4BE"]]},
}


def tema(t):
    return PLOT["dark"] if t == "dark" else PLOT["light"]


def centro_zoom(uf_sel=None):
    """Centro/zoom do mapa: Brasil inteiro (default) ou enquadrando uma UF selecionada.
    Usado por figura_mapa (rebuild) e pelo callback de zoom via Patch (sem reenviar o geojson)."""
    if uf_sel and uf_sel != "BR":
        d = mapa_cid[mapa_cid["uf"] == uf_sel]
        if len(d):
            return dict(lat=float(d["lat"].mean()), lon=float(d["lon"].mean())), 5.4
    return dict(lat=-15.3, lon=-53.0), 3.3        # enquadra o Brasil um pouco mais justo


# ---------------------------------------------------------------- mapa
def figura_mapa(uf_sel=None, lang="pt", tema_nome="light"):
    p = tema(tema_nome)
    fig = go.Figure()

    # camada 0: estados SEM cidade monitorada (fallback) — neutro, apenas contexto
    if NAO_COBERTAS:
        fig.add_trace(go.Choroplethmap(
            geojson=GEOJSON_UF, locations=NAO_COBERTAS, z=[0] * len(NAO_COBERTAS),
            featureidkey="properties.sigla",
            colorscale=[[0, p["naocob"]], [1, p["naocob"]]], showscale=False,
            marker=dict(opacity=0.62, line=dict(width=p["maplinew"], color=p["mapline"])),
            customdata=[[nome_uf[u]] for u in NAO_COBERTAS],
            hovertemplate="<b>%{customdata[0]}</b><br>" + tr(lang, "sem_cobertura") + "<extra></extra>",
            name=tr(lang, "sem_cobertura"),
        ))

    # camada 1: choropleth estadual (fundo) — "calor" previsto por estado
    z = np.log1p(mapa_uf["prev"].clip(lower=0))
    fig.add_trace(go.Choroplethmap(
        geojson=GEOJSON_UF, locations=mapa_uf["uf"], z=z,
        featureidkey="properties.sigla", colorscale=p["escala"], showscale=False,
        marker=dict(opacity=0.62, line=dict(width=p["maplinew"], color=p["mapline"])),
        customdata=np.stack([mapa_uf["nome"], mapa_uf["prev"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                      tr(lang, "hover_estado", v="%{customdata[1]:.0f}") + "<extra></extra>",
        name=tr(lang, "estados_trace"),
    ))

    # camada 2: bolhas das cidades (frente) — nível de alerta
    for nv in ORDEM_NIVEL:
        d = mapa_cid[mapa_cid["nivel_alerta"] == nv]
        if d.empty:
            continue
        txt = (d["nome"] + " (" + d["uf"] + ")<br>"
               + [tr(lang, "hover_cidade", v=int(v), nivel=nivel_tr(lang, nv))
                  for v in d["prev"]])
        fig.add_trace(go.Scattermap(
            lat=d["lat"], lon=d["lon"], mode="markers",
            marker=dict(size=(9 + (d["prev"] ** 0.5)).clip(9, 40), color=CORES_NIVEL[nv], opacity=0.92),
            name=nivel_tr(lang, nv), customdata=d["geo_id"],
            text=txt, hovertemplate="%{text}<extra></extra>",
        ))

    centro, zoom = centro_zoom(uf_sel)
    # legenda de níveis vive FORA do canvas (faixa HTML em layout.py) — não colide com a atribuição
    # do mapa (que antes cobria o nível "Vermelho") e é melhor para leitor de tela.
    fig.update_layout(
        map=dict(style=p["mapstyle"], center=centro, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(family="Inter, sans-serif", color=p["ink"]), uirevision="keep",
        hoverlabel=dict(bgcolor=p["hover_bg"], bordercolor=p["hover_bd"],
                        font=dict(family="Inter, sans-serif", size=12, color=p["ink"])),
    )
    return fig


# ---------------------------------------------------------------- detalhe
def figura_detalhe(geo_id, lang="pt", tema_nome="light"):
    p = tema(tema_nome)
    h = hist[hist["geo_id"] == geo_id].sort_values("data")
    pv = prev[prev["geo_id"] == geo_id].sort_values("h")
    sep = ",." if lang in ("pt", "es") else ".,"
    fig = go.Figure()
    if len(pv):
        xb = list(pv["data_prev"]) + list(pv["data_prev"][::-1])
        yb = list(pv["sup"]) + list(pv["inf"][::-1])
        fig.add_trace(go.Scatter(x=xb, y=yb, fill="toself", fillcolor=p["band"],
                                 line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False))
    if len(h):
        fig.add_trace(go.Scatter(x=h["data"], y=h["casos"], mode="lines", showlegend=False,
                                 line=dict(color=p["obs"], width=2), name=tr(lang, "g_observado")))
    if len(pv):
        x0 = ([h["data"].iloc[-1]] if len(h) else []) + list(pv["data_prev"])
        y0 = ([h["casos"].iloc[-1]] if len(h) else []) + list(pv["prev"])
        fig.add_trace(go.Scatter(x=x0, y=y0, mode="lines+markers", showlegend=False,
                                 line=dict(color=p["prev"], width=2.5, dash="dash"),
                                 marker=dict(size=7, color=p["paper"], line=dict(color=p["prev"], width=2)),
                                 name=tr(lang, "g_previsto")))
    if len(h):                                 # linha de origem (última semana observada) + rótulo SE
        ultima = h["data"].iloc[-1]
        fig.add_shape(type="line", x0=ultima, x1=ultima, y0=0, y1=1, yref="paper",
                      line=dict(color=p["axis"], width=1, dash="dot"))
        _, se = semana_epi(ultima.date())
        fig.add_annotation(x=ultima, y=1, yref="paper", text=f"SE {se}", showarrow=False,
                           xanchor="left", yanchor="bottom",
                           font=dict(size=10, family="IBM Plex Mono, monospace", color=p["ink"]))
    fig.update_layout(
        margin=dict(l=8, r=12, t=14, b=8), autosize=True, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color=p["ink"], size=12),
        yaxis_title=tr(lang, "g_ytitle"), xaxis_title=None, showlegend=False, separators=sep,
        hovermode="x unified",
        hoverlabel=dict(bgcolor=p["hover_bg"], bordercolor=p["hover_bd"],
                        font=dict(family="Inter, sans-serif", size=12, color=p["ink"])),
    )
    fig.update_xaxes(showgrid=False, linecolor=p["axis"])
    fig.update_yaxes(gridcolor=p["grid"], rangemode="tozero", zeroline=False)
    return fig


def horizontes(geo_id, lang="pt"):
    """Lista t+1…t+4 (valor + IC) + frase do alargamento da faixa. Vai abaixo do gráfico de detalhe."""
    pv = prev[prev["geo_id"] == geo_id].sort_values("h")
    if pv.empty:
        return []
    itens = []
    for _, r in pv.iterrows():
        cls = "horiz-item h1" if int(r["h"]) == 1 else "horiz-item"
        itens.append(html.Li(className=cls, children=[
            html.Span(f"t+{int(r['h'])} · {r['data_prev'].strftime('%d/%m')}", className="horiz-t mono"),
            html.Span(fmt_int(r["prev"], lang), className="horiz-v tabular"),
            html.Span(f"{fmt_int(r['inf'], lang)}–{fmt_int(r['sup'], lang)}", className="horiz-ic mono")]))
    h1, h4 = pv.iloc[0], pv.iloc[-1]
    m1, m4 = round((h1["sup"] - h1["inf"]) / 2), round((h4["sup"] - h4["inf"]) / 2)
    return [html.Ol(itens, className="horizontes"),
            html.P(tr(lang, "horiz_nota", a=fmt_int(m1, lang), b=fmt_int(m4, lang)),
                   className="horiz-nota aux")]


def cartao_info(geo_id, lang="pt"):
    p1 = prev[(prev["geo_id"] == geo_id) & (prev["h"] == 1)]
    if p1.empty:
        if isinstance(geo_id, str) and geo_id.startswith("UF-"):   # estado sem cobertura
            uf = geo_id[3:]
            return [
                html.Div(className="cartao-head", children=[
                    html.Span(nome_uf.get(uf, uf), className="nome"),
                    html.Span(tr(lang, "escopo_estado"), className="escopo")]),
                html.P(tr(lang, "sem_cob_cartao"), className="sub", style={"marginTop": "12px"}),
            ]
        return tr(lang, "card_prompt")
    r = p1.iloc[0]
    nv = r["nivel_alerta"]
    estado = r["nivel_geo"] == "estado"
    escopo = tr(lang, "escopo_cidades") if estado else tr(lang, "escopo_municipio")
    cartao = [html.Div(className="cartao-head", children=[
        html.Span(r["nome"], className="nome"), html.Span(escopo, className="escopo")])]
    if estado:
        cartao.append(html.Div(tr(lang, "nota_piso"), className="sub nota"))
    cartao += [
        html.Span(tr(lang, "card_prev"), className="label"),
        html.Div(tr(lang, "card_casos", v=int(r["prev"])), className="valor"),
        html.Div(tr(lang, "card_intervalo", inf=int(r["inf"]), sup=int(r["sup"])), className="sub"),
        html.Div([tr(lang, "card_nivel"),
                  html.Span([html.Span(className=f"glifo {nv.lower()}", **{"aria-hidden": "true"}),
                             nivel_tr(lang, nv)], className=f"pill nivel-{nv.lower()}")],
                 className="sub", style={"marginTop": "8px"}),
        html.Div(tr(lang, "nota_nivel"), className="sub nota"),
    ]
    return cartao
