# -*- coding: utf-8 -*-
"""
Figuras Plotly (mapa, gráfico de detalhe) e o cartão de informação, com paleta por tema
(claro/escuro). Separado do app para manter os callbacks enxutos e testável isoladamente.
"""
import numpy as np
import plotly.graph_objects as go
from dash import html

from dados import (
    CORES_NIVEL,
    CORES_NIVEL_CVD,
    GEOJSON_UF,
    ORDEM_NIVEL,
    ORIGINAL,
    nome_uf,
    semana_epi,
)
from formato import plotly_hoverformat_data, plotly_separators
from i18n import fmt_data, fmt_int, tr
from i18n import nivel as nivel_tr

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
              "prev": "#2F5A42", "cmp": "#2E6FB0", "band": "rgba(47,90,66,0.16)", "naocob": "#DCD7C6", "paper": "#FBFAF5",
              "mapstyle": "carto-positron", "legbg": "rgba(251,250,245,0.92)", "legbd": "#D9D4C7",
              "mapline": "rgba(64,92,98,0.60)", "maplinew": 0.8, "ring": "#1C2620",
              "hover_bg": "#FBFAF5", "hover_bd": "#D9D4C7",
              "escala": [[0.0, "#D5E3E2"], [0.5, "#9FC2C6"], [1.0, "#3F6E78"]]},
    "dark":  {"ink": "#ECEFEA", "grid": "#2A3330", "axis": "#3A4541", "obs": "#ECEFEA",
              "prev": "#7FC894", "cmp": "#8DB8E8", "band": "rgba(127,200,148,0.22)", "naocob": "#262D30", "paper": "#1E2428",
              "mapstyle": "carto-darkmatter", "legbg": "rgba(30,36,40,0.92)", "legbd": "#313A39",
              "mapline": "rgba(255,255,255,0.50)", "maplinew": 0.6, "ring": "#F3EFE6",
              "hover_bg": "#222A2D", "hover_bd": "#3A4541",
              "escala": [[0.0, "#20282A"], [0.5, "#315B63"], [1.0, "#79B4BE"]]},
}


ESPESSURA_ANEL = {"Verde": 1, "Amarelo": 2, "Laranja": 3, "Vermelho": 4}   # px por lado (canal além da cor)


def indices_anel(c=ORIGINAL):
    """Índices (em fig.data) das camadas de anel — o Patch de tema precisa recolori-las."""
    mapa_cid, nao_cobertas = c.mapa_cid, c.nao_cobertas
    base = (1 if nao_cobertas else 0) + 1            # [sem cobertura?] + choropleth
    idx = []
    for nv in ORDEM_NIVEL:
        if (mapa_cid["nivel_alerta"] == nv).any():
            idx.append(base)
            base += 2                                 # anel + preenchimento
    return idx


def tema(t):
    return PLOT["dark"] if t == "dark" else PLOT["light"]


def centro_zoom(uf_sel=None, c=ORIGINAL):
    """Centro/zoom do mapa: Brasil inteiro (default) ou enquadrando uma UF selecionada.
    Usado por figura_mapa (rebuild) e pelo callback de zoom via Patch (sem reenviar o geojson)."""
    mapa_cid = c.mapa_cid
    if uf_sel and uf_sel != "BR":
        d = mapa_cid[mapa_cid["uf"] == uf_sel]
        if len(d):
            return dict(lat=float(d["lat"].mean()), lon=float(d["lon"].mean())), 5.4
    return dict(lat=-15.3, lon=-53.0), 3.3        # enquadra o Brasil um pouco mais justo


# ---------------------------------------------------------------- mapa
def figura_mapa(uf_sel=None, lang="pt", tema_nome="light", cvd=False, c=ORIGINAL):
    mapa_cid, mapa_uf, nao_cobertas = c.mapa_cid, c.mapa_uf, c.nao_cobertas
    p = tema(tema_nome)
    cores = CORES_NIVEL_CVD if cvd else CORES_NIVEL   # paleta p/ daltonismo (opt-in)
    fig = go.Figure()

    # camada 0: estados SEM cidade monitorada (fallback) — neutro, apenas contexto
    if nao_cobertas:
        fig.add_trace(go.Choroplethmap(
            geojson=GEOJSON_UF, locations=nao_cobertas, z=[0] * len(nao_cobertas),
            featureidkey="properties.sigla",
            colorscale=[[0, p["naocob"]], [1, p["naocob"]]], showscale=False,
            marker=dict(opacity=0.62, line=dict(width=p["maplinew"], color=p["mapline"])),
            customdata=[[nome_uf[u]] for u in nao_cobertas],
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
                      tr(lang, "hover_estado", v="%{customdata[1]:,.0f}") + "<extra></extra>",
        name=tr(lang, "estados_trace"),
    ))

    # camada 2: bolhas das cidades (frente) — nível de alerta
    for nv in ORDEM_NIVEL:
        d = mapa_cid[mapa_cid["nivel_alerta"] == nv]
        if d.empty:
            continue
        txt = (d["nome"] + " (" + d["uf"] + ")<br>"
               + [tr(lang, "hover_cidade", v=fmt_int(v, lang), nivel=nivel_tr(lang, nv))
                  for v in d["prev"]])
        tam = (9 + (d["prev"] ** 0.5)).clip(9, 40)
        # ANEL: o scattermap não tem marker.line → camada de baixo, maior, na cor do anel (contraste ≥3:1
        # com o mapa e com o preenchimento) e ESPESSURA crescente com o nível (1→4 px): segundo canal
        # além da cor (WCAG 1.4.1) e contorno que garante 1.4.11 mesmo p/ amarelo/laranja sobre o mapa.
        fig.add_trace(go.Scattermap(
            lat=d["lat"], lon=d["lon"], mode="markers", name=f"anel-{nv}", showlegend=False,
            marker=dict(size=tam + 2 * ESPESSURA_ANEL[nv], color=p["ring"], opacity=1),
            hoverinfo="skip"))
        fig.add_trace(go.Scattermap(
            lat=d["lat"], lon=d["lon"], mode="markers",
            marker=dict(size=tam, color=cores[nv], opacity=1),
            name=nivel_tr(lang, nv), customdata=d["geo_id"],
            text=txt, hovertemplate="%{text}<extra></extra>",
        ))

    centro, zoom = centro_zoom(uf_sel, c)
    # legenda de níveis vive FORA do canvas (faixa HTML em layout.py) — não colide com a atribuição
    # do mapa (que antes cobria o nível "Vermelho") e é melhor para leitor de tela.
    fig.update_layout(
        map=dict(style=p["mapstyle"], center=centro, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, separators=plotly_separators(lang),
        font=dict(family="Inter, sans-serif", color=p["ink"]), uirevision="keep",
        hoverlabel=dict(bgcolor=p["hover_bg"], bordercolor=p["hover_bd"],
                        font=dict(family="Inter, sans-serif", size=12, color=p["ink"])),
    )
    return fig


# ---------------------------------------------------------------- detalhe
def sem_serie(geo_id, c=ORIGINAL):
    """True quando não há NADA para desenhar/anunciar (estado sem cidade monitorada).
    Hoje inalcançável com os dados reais (27/27 UFs cobertas), mas o smoke do pipeline com 1
    cidade (CIDADES_GEO=…) e os dados de exemplo o ativam — ver tests/test_sem_cobertura.py."""
    prev, hist = c.prev, c.hist
    return (prev["geo_id"] == geo_id).sum() == 0 and (hist["geo_id"] == geo_id).sum() == 0


def comparacao_valida(geo_id, comp, c=ORIGINAL):
    """Cidade de comparação efetiva: só município vs. município diferente e existente; senão None."""
    prev = c.prev
    if not (isinstance(comp, str) and isinstance(geo_id, str)) or comp == geo_id:
        return None
    if geo_id.startswith("UF-") or comp.startswith("UF-"):
        return None
    return comp if (comp in set(prev["geo_id"]) and geo_id in set(prev["geo_id"])) else None


def figura_detalhe(geo_id, lang="pt", tema_nome="light", comp=None, c=ORIGINAL):
    prev, hist = c.prev, c.hist
    p = tema(tema_nome)
    h = hist[hist["geo_id"] == geo_id].sort_values("data")
    pv = prev[prev["geo_id"] == geo_id].sort_values("h")
    sep = plotly_separators(lang)
    fig = go.Figure()
    if sem_serie(geo_id, c):          # estado vazio: mensagem no lugar do gráfico (mantém a altura reservada)
        fig.add_annotation(xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           text=tr(lang, "detalhe_sem_serie"), align="center",
                           font=dict(family="Inter, sans-serif", size=14, color=p["ink"]))
        fig.update_layout(margin=dict(l=8, r=12, t=14, b=8), autosize=True, showlegend=False,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    comp = comparacao_valida(geo_id, comp, c)
    pref = f"{pv['nome'].iloc[0]} · " if (comp and len(pv)) else ""
    if len(pv):
        xb = list(pv["data_prev"]) + list(pv["data_prev"][::-1])
        yb = list(pv["sup"]) + list(pv["inf"][::-1])
        fig.add_trace(go.Scatter(x=xb, y=yb, fill="toself", fillcolor=p["band"],
                                 line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False))
        # bordas do intervalo: a banda sozinha tem 1,3:1 (claro) / 1,6:1 (escuro) contra o fundo — abaixo
        # dos 3:1 de WCAG 1.4.11 para gráficos. A linha fina na cor da previsão (≈7,5:1) torna o limite visível.
        for lim in ("sup", "inf"):
            fig.add_trace(go.Scatter(x=pv["data_prev"], y=pv[lim], mode="lines", showlegend=False,
                                     hoverinfo="skip", line=dict(color=p["prev"], width=1)))
    if len(h):
        fig.add_trace(go.Scatter(x=h["data"], y=h["casos"], mode="lines", showlegend=False,
                                 line=dict(color=p["obs"], width=2),
                                 name=pref + tr(lang, "g_observado")))
    if len(pv):
        x0 = ([h["data"].iloc[-1]] if len(h) else []) + list(pv["data_prev"])
        y0 = ([h["casos"].iloc[-1]] if len(h) else []) + list(pv["prev"])
        fig.add_trace(go.Scatter(x=x0, y=y0, mode="lines+markers", showlegend=False,
                                 line=dict(color=p["prev"], width=2.5, dash="dash"),
                                 marker=dict(size=7, color=p["paper"], line=dict(color=p["prev"], width=2)),
                                 name=pref + tr(lang, "g_previsto")))
    if comp:                                   # série de comparação: azul + traço pontilhado + losango (não só cor)
        hc = hist[hist["geo_id"] == comp].sort_values("data")
        pc = prev[prev["geo_id"] == comp].sort_values("h")
        nc = pc["nome"].iloc[0] if len(pc) else comp
        if len(hc):
            fig.add_trace(go.Scatter(x=hc["data"], y=hc["casos"], mode="lines", showlegend=False,
                                     line=dict(color=p["cmp"], width=1.75), name=f"{nc} · {tr(lang, 'g_observado')}"))
        if len(pc):
            x0 = ([hc["data"].iloc[-1]] if len(hc) else []) + list(pc["data_prev"])
            y0 = ([hc["casos"].iloc[-1]] if len(hc) else []) + list(pc["prev"])
            fig.add_trace(go.Scatter(x=x0, y=y0, mode="lines+markers", showlegend=False,
                                     line=dict(color=p["cmp"], width=2.5, dash="dot"),
                                     marker=dict(size=8, symbol="diamond", color=p["paper"],
                                                 line=dict(color=p["cmp"], width=2)),
                                     name=f"{nc} · {tr(lang, 'g_previsto')}"))
    if len(h):                                 # linha de origem (última semana observada) + rótulo SE
        ultima = h["data"].iloc[-1]
        fig.add_shape(type="line", x0=ultima, x1=ultima, y0=0, y1=1, yref="paper",
                      line=dict(color=p["axis"], width=1, dash="dot"))
        _, se = semana_epi(ultima.date())
        fig.add_annotation(x=ultima, y=1, yref="paper", text=tr(lang, "se_abrev", se=se), showarrow=False,
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
    fig.update_xaxes(showgrid=False, linecolor=p["axis"], hoverformat=plotly_hoverformat_data(lang))
    fig.update_yaxes(gridcolor=p["grid"], rangemode="tozero", zeroline=False)
    return fig


def tabela_comparacao(geo_id, comp, lang="pt", c=ORIGINAL):
    """Alternativa textual do gráfico comparativo: t+1…t+4 das duas cidades (valor + IC de 90%)."""
    prev = c.prev
    linhas = []
    for g in (geo_id, comp):
        pv = prev[prev["geo_id"] == g].sort_values("h")
        celulas = [html.Td([html.Span(fmt_int(r["prev"], lang), className="cmp-v tabular"),
                            html.Span(f"{fmt_int(r['inf'], lang)}–{fmt_int(r['sup'], lang)}", className="cmp-ic")])
                   for _, r in pv.iterrows()]
        linhas.append(html.Tr([html.Th(pv["nome"].iloc[0], scope="row", className="notranslate")] + celulas))
    cab = html.Tr([html.Td("")] + [html.Th(f"t+{h}", scope="col") for h in (1, 2, 3, 4)])
    return html.Div(className="tabela-scroll", role="region", tabIndex=0,
                    **{"aria-label": tr(lang, "cmp_tab_cap")},
                    children=html.Table(className="tabela-cmp", children=[
                        html.Caption(tr(lang, "cmp_tab_cap")), html.Thead(cab), html.Tbody(linhas)]))


def horizontes(geo_id, lang="pt", comp=None, c=ORIGINAL):
    """Lista t+1…t+4 (valor + IC) + frase do alargamento da faixa. Vai abaixo do gráfico de detalhe."""
    prev = c.prev
    pv = prev[prev["geo_id"] == geo_id].sort_values("h")
    if pv.empty:
        return []
    itens = []
    for _, r in pv.iterrows():
        cls = "horiz-item h1" if int(r["h"]) == 1 else "horiz-item"
        itens.append(html.Li(className=cls, children=[
            html.Span([html.Span(f"t+{int(r['h'])}", className="horiz-h"),       # horizonte e data em 2 linhas fixas
                       html.Span(fmt_data(r['data_prev'], lang, 'curto'), className="horiz-d")],
                      className="horiz-t mono"),
            html.Span(fmt_int(r["prev"], lang), className="horiz-v tabular"),
            html.Span(f"{fmt_int(r['inf'], lang)}–{fmt_int(r['sup'], lang)}", className="horiz-ic mono")]))
    h1, h4 = pv.iloc[0], pv.iloc[-1]
    m1, m4 = round((h1["sup"] - h1["inf"]) / 2), round((h4["sup"] - h4["inf"]) / 2)
    return [html.Ol(itens, className="horizontes"),
            html.P(tr(lang, "horiz_nota", a=fmt_int(m1, lang), b=fmt_int(m4, lang)),
                   className="horiz-nota aux"),
            html.P(tr(lang, "gloss_linha"), className="horiz-nota aux"),
            *([tabela_comparacao(geo_id, comp, lang, c), html.P(tr(lang, "cmp_hint"), className="horiz-nota aux")]
              if comparacao_valida(geo_id, comp, c) else [])]


def cartao_info(geo_id, lang="pt", c=ORIGINAL):
    prev = c.prev
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
        html.Div(tr(lang, "card_casos", v=fmt_int(r["prev"], lang)), className="valor"),
        html.Div(tr(lang, "card_intervalo", inf=fmt_int(r["inf"], lang), sup=fmt_int(r["sup"], lang)),
                 className="sub"),
        html.Div([tr(lang, "card_nivel"),
                  html.Span([html.Span(className=f"glifo {nv.lower()}", **{"aria-hidden": "true"}),
                             nivel_tr(lang, nv)], className=f"pill nivel-{nv.lower()}")],
                 className="sub", style={"marginTop": "8px"}),
        html.Div(tr(lang, "nota_nivel"), className="sub nota"),
    ]
    return cartao


def resumo_cartao(geo_id, lang="pt", comp=None, c=ORIGINAL):
    """Resumo curto do cartão para anúncio em aria-live (ao trocar de cidade)."""
    prev = c.prev
    p1 = prev[(prev["geo_id"] == geo_id) & (prev["h"] == 1)]
    if p1.empty:
        if isinstance(geo_id, str) and geo_id.startswith("UF-"):   # estado sem cidade monitorada:
            uf = geo_id[3:]                                        # antes era "" → leitor de tela mudo
            return tr(lang, "cartao_resumo_aria_semcob", nome=nome_uf.get(uf, uf))
        return ""
    r = p1.iloc[0]
    txt = tr(lang, "cartao_resumo_aria", nome=r["nome"],
             v=fmt_int(r["prev"], lang), nivel=nivel_tr(lang, r["nivel_alerta"]))
    comp = comparacao_valida(geo_id, comp, c)
    if comp:
        c1 = prev[(prev["geo_id"] == comp) & (prev["h"] == 1)].iloc[0]
        txt += " " + tr(lang, "cartao_resumo_cmp_aria", nome=c1["nome"], v=fmt_int(c1["prev"], lang),
                        nivel=nivel_tr(lang, c1["nivel_alerta"]))
    return txt
