# -*- coding: utf-8 -*-
"""
Testes de VALIDAÇÃO e FUNCIONAMENTO (sem navegador).
Rodar:  cd webapp && source .venv/bin/activate && pytest tests/test_unit.py -q
Cobre: contraste WCAG AAA da paleta, contrato dos CSVs, ausência da lista aninhada
que causava o erro do React no Dash, invariantes do intervalo (cap do sup), e as
correções do pipeline (nível simplificado e agregação estadual por cidades[0]).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
WEBAPP = os.path.dirname(AQUI)
DATA = os.path.join(WEBAPP, "data")                # repositório (geojson não é saída do pipeline)
# Saída do pipeline sob teste (gate do refresh): previsoes/historico/_meta usam DATA_DIR.
DATA_SAIDA = os.path.abspath(os.environ.get("DATA_DIR") or DATA)
for p in (WEBAPP, os.path.join(WEBAPP, "pipeline")):
    if p not in sys.path:
        sys.path.insert(0, p)


# ---------------------------------------------------------------- contraste WCAG
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contraste(a, b):
    l1, l2 = _lum(a), _lum(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


CREAM, PAPER, CREAM2, INK = "#F3EFE6", "#FBFAF5", "#E9E4D6", "#1C2620"

# pares de TEXTO da interface — padrão AAA (texto normal ≥ 7:1)
PARES_NORMAL = [
    ("ink/cream", INK, CREAM), ("ink/paper", INK, PAPER), ("ink/cream2", INK, CREAM2),
    ("muted/cream", "#414741", CREAM), ("muted/paper", "#414741", PAPER),
    ("muted/cream2", "#414741", CREAM2),
    ("green-ink/cream (kicker,link)", "#2B5540", CREAM),
    ("green-ink/paper (best,accent)", "#2B5540", PAPER),
    ("chip.solid branco/green-d", "#FFFFFF", "#2F5A42"),
    ("topbar cream/ink", CREAM, INK), ("topbar muted/ink", "#C4CEC5", INK),
    ("aviso info", "#255039", "#EAF2EC"), ("aviso warn", "#63430D", "#FCF4E6"),
    ("ícone ink/green-l", INK, "#A9CDA4"),
    ("pill ink/verde", INK, "#D6ECDC"), ("pill ink/amarelo", INK, "#F6E8BE"),
    ("pill ink/laranja", INK, "#FBDFCB"), ("pill ink/vermelho", INK, "#F6D4D9"),
    # JBCS × slides (F1) — pares novos, tema claro (≥ 7:1)
    ("on-brand/brand (hero)", "#F3EFE6", "#1F3B2C"),
    ("on-brand-muted/brand", "#C4CEC5", "#1F3B2C"),
    ("btn-fg/btn-bg", "#FBFAF6", "#2F5A42"),
    ("btn-on-brand-fg/btn-on-brand-bg", "#1C2620", "#A9CDA4"),
    ("green-ink/info-bg (recência)", "#2B5540", "#EAF2EC"),
    ("mono muted/cream-2", "#414741", "#E9E4D6"),
    ("rodapé on-brand-muted/ink", "#C4CEC5", "#1C2620"),
    ("rodapé accent/ink", "#A9CDA4", "#1C2620"),
]
# texto GRANDE (≥ 24px ou ≥ 18,66px bold) — AAA ≥ 4,5:1
PARES_GRANDE = [
    ("hero h1 ink/cream", INK, CREAM),
    ("stat arrow terra/cream", "#A8501A", CREAM),
    ("stat arrow terra/paper", "#A8501A", PAPER),
    ("H1 acento accent/brand (grande)", "#A9CDA4", "#1F3B2C"),
]


def test_contraste_texto_normal_AAA():
    falhas = [(n, round(contraste(f, b), 2)) for n, f, b in PARES_NORMAL if contraste(f, b) < 7.0]
    assert not falhas, f"pares abaixo de 7:1 (AAA normal): {falhas}"


def test_contraste_texto_grande_AAA():
    falhas = [(n, round(contraste(f, b), 2)) for n, f, b in PARES_GRANDE if contraste(f, b) < 4.5]
    assert not falhas, f"pares abaixo de 4,5:1 (AAA grande): {falhas}"


# pares de TEXTO no TEMA ESCURO — AAA ≥ 7:1 (texto claro sobre fundo escuro)
D_BG, D_PAPER, D_C2, D_INK = "#14181A", "#1E2428", "#222A2D", "#ECEFEA"
PARES_DARK = [
    ("ink/bg", D_INK, D_BG), ("ink/paper", D_INK, D_PAPER), ("ink/cream2", D_INK, D_C2),
    ("muted/bg", "#B6BEB7", D_BG), ("muted/paper", "#B6BEB7", D_PAPER),
    ("muted/cream2", "#B6BEB7", D_C2),
    ("green-ink/bg", "#8FD3A4", D_BG), ("green-ink/paper", "#8FD3A4", D_PAPER),
    ("topbar fg/bg", D_INK, "#0E1113"), ("topbar muted/bg", "#9AA39B", "#0E1113"),
    ("seg ativo", "#1C2620", "#F3EFE6"),
    ("aviso info", "#A9DEBB", "#13251A"), ("aviso warn", "#E7C981", "#262012"),
    ("ícone ink/green-l", D_INK, "#274234"),
    ("pill ink/verde", D_INK, "#173322"), ("pill ink/amarelo", D_INK, "#33280B"),
    ("pill ink/laranja", D_INK, "#36220F"), ("pill ink/vermelho", D_INK, "#361820"),
    # JBCS × slides (F1) — pares novos, tema escuro (≥ 7:1)
    ("on-brand/brand (hero)", "#ECEFEA", "#1D3227"),
    ("on-brand-muted/brand", "#B6BEB7", "#1D3227"),
    ("accent/brand (H1 acento)", "#8FD3A4", "#1D3227"),
    ("btn-fg/btn-bg", "#0E1113", "#8FD3A4"),
    ("green-ink/cream-2", "#8FD3A4", "#222A2D"),
    ("bibtex on-brand/#0E1113", "#ECEFEA", "#0E1113"),
    ("rodapé muted/#0E1113", "#B6BEB7", "#0E1113"),
]


def test_contraste_dark_AAA():
    falhas = [(n, round(contraste(f, b), 2)) for n, f, b in PARES_DARK if contraste(f, b) < 7.0]
    assert not falhas, f"tema escuro abaixo de 7:1 (AAA): {falhas}"


def test_css_usa_tokens_AAA():
    css = open(os.path.join(WEBAPP, "assets", "style.css"), encoding="utf-8").read()
    for hexv in ("#414741", "#2B5540", "#2F5A42", "#D6ECDC", "#F6D4D9",
                 "#1F3B2C", "#C4CEC5", "#1D3227"):          # tokens de marca JBCS (F1)
        assert hexv in css, f"token AAA ausente no CSS: {hexv}"
    assert "--font-serif" in css, "token de fonte serif ausente (self-host F1)"
    assert "min-width: 481px" in css and "min-width: 980px" in css, "breakpoints mobile-first ausentes"


# ---------------------------------------------------------------- contrato dos dados
def test_schema_previsoes():
    df = pd.read_csv(os.path.join(DATA_SAIDA, "previsoes.csv"))
    cols = {"nivel_geo", "geo_id", "uf", "nome", "lat", "lon", "data_origem", "h",
            "data_prev", "prev", "inf", "sup", "nivel_alerta"}
    assert cols.issubset(df.columns)
    assert df["h"].between(1, 4).all()
    assert set(df["nivel_geo"].unique()) <= {"municipio", "estado"}
    assert set(df["nivel_alerta"].unique()) <= {"Verde", "Amarelo", "Laranja", "Vermelho"}
    assert (df["prev"] >= 0).all() and (df["inf"] >= 0).all()
    assert (df["sup"] >= df["prev"]).all() and (df["inf"] <= df["prev"]).all()


def test_schema_historico():
    df = pd.read_csv(os.path.join(DATA_SAIDA, "historico.csv"))
    assert {"nivel_geo", "geo_id", "uf", "nome", "lat", "lon", "data", "casos"}.issubset(df.columns)
    assert (df["casos"] >= 0).all()


def _dtype_contrato(t):
    # pandas 2 usa object e pandas 3 usa str para texto: ambos viram "texto"
    return "texto" if str(t) in ("object", "str", "string") else str(t)


def test_contrato_estavel():
    """Colunas, ordem e dtypes dos CSVs == tests/contrato/*.json. Mudança deliberada de contrato
    altera o JSON na MESMA PR (revisão consciente)."""
    for nome in ("previsoes", "historico"):
        esperado = json.load(open(os.path.join(AQUI, "contrato", nome + ".json"), encoding="utf-8"))
        df = pd.read_csv(os.path.join(DATA_SAIDA, nome + ".csv"))
        obtido = [{"nome": c, "dtype": _dtype_contrato(t)} for c, t in df.dtypes.items()]
        assert obtido == esperado["colunas"], f"contrato de {nome}.csv mudou"


def test_geojson_27_ufs():
    g = json.load(open(os.path.join(DATA, "br_uf.geojson"), encoding="utf-8"))
    sig = {f["properties"]["sigla"] for f in g["features"]}
    nomes = {f["properties"]["name"] for f in g["features"]}
    assert len(sig) == 27 and len(nomes) == 27


# ---------------------------------------------------------------- app (layout/callbacks)
def _coleta_listas_aninhadas(raiz):
    from dash.development.base_component import Component
    hits = []

    def rec(n):
        if isinstance(n, Component):
            rec(getattr(n, "children", None))
        elif isinstance(n, (list, tuple)):
            for x in n:
                if isinstance(x, (list, tuple)):
                    hits.append(x)            # lista dentro de lista -> erro do React
                rec(x)
    rec(raiz)
    return hits


def test_layout_sem_lista_aninhada():
    """Regressão do erro 'Objects are not valid as a React child' — nos 3 idiomas."""
    import app as A
    hits = _coleta_listas_aninhadas(A.serve_layout())
    for lg in ("pt", "en", "es"):
        hits += _coleta_listas_aninhadas(A.construir_conteudo(lg))
        for g in [A.ORIGINAL.mapa_cid["geo_id"].iloc[0], "UF-PR", "UF-ZZ"]:
            hits += _coleta_listas_aninhadas(A.cartao_info(g, lg))
    assert hits == [], "há lista aninhada em children (causa o erro do Dash/React)"


def test_i18n_resolver_e_fallback():
    import i18n
    assert i18n.resolver("pt-BR") == "pt"
    assert i18n.resolver("es-ES") == "es"
    assert i18n.resolver("fr") == "en"          # sem correspondência -> EN
    assert i18n.resolver(None) == "en"
    # toda chave existe nos 3 idiomas
    faltando = [(k, lg) for k, v in i18n.T.items() for lg in i18n.IDIOMAS if lg not in v]
    assert not faltando, f"traduções faltando: {faltando[:8]}"


def test_figuras_claro_escuro():
    import app as A
    for tm in ("light", "dark"):
        A.figura_mapa("BR", "en", tm)
        A.figura_detalhe(A.ORIGINAL.mapa_cid["geo_id"].iloc[0], "es", tm)


def test_geojson_simplificado_leve():
    p = os.path.join(DATA, "br_uf.geojson")
    kb = os.path.getsize(p) / 1024
    assert kb < 200, f"geojson {kb:.0f} KB — rode simplificar_geojson.py (alvo < 150)"
    g = json.load(open(p, encoding="utf-8"))
    assert len({f["properties"]["sigla"] for f in g["features"]}) == 27
    assert all({"sigla", "name"} <= set(f["properties"]) for f in g["features"])


def test_meta_proveniencia():
    mp = os.path.join(DATA_SAIDA, "_meta.json")
    assert os.path.exists(mp), "o pipeline deve gravar data/_meta.json"
    m = json.load(open(mp, encoding="utf-8"))
    for k in ("coletado_em", "se_origem", "modelo", "n_cidades", "n_falhas"):
        assert k in m, f"_meta.json sem a chave {k}"
    if m.get("versao", 1) >= 2:                       # proveniência v2 (v1 continua aceito)
        for k in ("versoes", "duracao_treino_s", "campo_casos", "ey_start", "janela", "horizonte",
                  "seed", "epocas_max", "paciencia", "epocas_por_cidade"):
            assert k in m, f"_meta.json v2 sem a chave {k}"
        assert {"python", "tensorflow", "keras", "numpy", "pandas"} <= set(m["versoes"])
        assert len(m["epocas_por_cidade"]) == m["n_cidades"]


def test_modulos_refatorados_importam():
    import dados
    import figuras
    import layout
    assert hasattr(dados, "ORIGINAL") and hasattr(dados.ORIGINAL, "geo0")
    assert hasattr(figuras, "figura_mapa") and hasattr(figuras, "PLOT")
    assert hasattr(layout, "construir_conteudo") and hasattr(layout, "serve_layout")


def test_cartao_estado_e_sem_cobertura():
    import app as A
    # estado COBERTO -> entra no ramo "estado" de cartao_info: escopo de cidades monitoradas + nota de piso
    txt = json.dumps(A.cartao_info("UF-PR"), default=str)
    assert "monitoradas" in txt, "card de estado coberto deveria exibir o escopo de cidades monitoradas"
    # estado SEM cobertura -> mensagem amigável, nunca quebra
    semcob = A.cartao_info("UF-ZZ")
    assert isinstance(semcob, list) and semcob


def test_cap_sup_invariante_e_teto():
    import app as A
    assert (A.ORIGINAL.prev["sup"] >= A.ORIGINAL.prev["prev"]).all()
    assert (A.ORIGINAL.prev["inf"] <= A.ORIGINAL.prev["prev"]).all()
    pico = A.ORIGINAL.hist.groupby("geo_id")["casos"].max()
    m = A.ORIGINAL.prev.join(pico.rename("pico"), on="geo_id").dropna(subset=["pico"])
    teto = np.maximum(1.0, np.maximum(m["pico"], m["prev"])) * A.TETO_FATOR
    assert (m["sup"] <= teto + 1e-6).all(), "sup acima do teto (quebraria a escala do gráfico)"


# ---------------------------------------------------------------- pipeline
def test_nivel_alerta_simplificado():
    import gerar_previsoes_reais as G
    assert G.nivel_alerta(0, 100_000) == "Verde"       # inc 0
    assert G.nivel_alerta(5, 100_000) == "Amarelo"      # inc 5
    assert G.nivel_alerta(20, 100_000) == "Laranja"     # inc 20
    assert G.nivel_alerta(50, 100_000) == "Vermelho"    # inc 50


def test_agregacao_estadual_usa_primeira_cidade():
    """A origem do agregado estadual vem de cidades[0] (não mais da variável vazada)."""
    import gerar_previsoes_reais as G

    def cidade(lat):
        hist = [["municipio", "1", "PR", "X", lat, -49, "2024-01-07", 10]]
        prev = [["municipio", "1", "PR", "X", lat, -49, "2024-01-07", 1,
                 "2024-01-14", 10, 5, 20, "Amarelo"]]
        return {"lat": lat, "lon": -49, "pop": 100_000, "hist": hist, "prev": prev}

    por_uf = {"PR": [cidade(-25.4), cidade(-23.3)]}       # ordem não pode afetar a origem
    hr, pr = [], []
    G.agregar_estados(por_uf, hr, pr)
    estados = [r for r in pr if r[0] == "estado"]
    assert estados, "nenhuma linha estadual gerada"
    assert estados[0][6] == "2024-01-07", "origem do agregado não veio de cidades[0]"
    assert estados[0][9] == 20, "soma das cidades monitoradas incorreta (prev 10+10)"


# ---------------------------------------------------------------- núcleo científico (sem TensorFlow)
def test_para_casos_roundtrip():
    """A inversão normalização+log1p (preparacao.para_casos) deve voltar aos casos originais."""
    import preparacao as P
    lo, hi = 0.0, float(np.log1p(500))                 # faixa de treino fictícia [0, log1p(500)]
    params = {"log1p_min_treino": lo, "log1p_max_treino": hi}
    for casos in (0, 1, 37, 500):                      # casos -> norm -> para_casos -> casos
        norm = (np.log1p(casos) - lo) / (hi - lo)
        volta = float(P.para_casos(norm, params))
        assert abs(volta - casos) < 1e-6, f"round-trip falhou p/ {casos}: obteve {volta}"
    assert float(P.para_casos(-5.0, params)) == 0.0, "para_casos deveria truncar negativos em 0"
    assert abs(float(P.para_casos(1.0, params)) - 500) < 1e-6, "norm=1 deveria devolver o máx do treino"


def test_janelas_shapes_e_nan_futuro():
    """modelo._janelas (sem TF): formatos das janelas e alvo NaN quando o futuro não existe."""
    import modelo as M
    n = 40
    X = np.arange(n, dtype="float32").reshape(n, 1)
    y = np.arange(n, dtype="float32")
    origens = np.arange(M.JANELA - 1, n - M.HORIZONTE)         # origens com alvo conhecido
    Xw, yw = M._janelas(X, y, origens)
    assert Xw.shape == (len(origens), M.JANELA, 1), f"forma de Xw inesperada: {Xw.shape}"
    assert yw.shape == (len(origens), M.HORIZONTE), f"forma de yw inesperada: {yw.shape}"
    t = int(origens[0])                                        # janela = X[t-11..t]; alvo = y[t+1..t+4]
    assert np.allclose(Xw[0, :, 0], X[t - M.JANELA + 1:t + 1, 0]), "janela de entrada desalinhada"
    assert np.allclose(yw[0], y[t + 1:t + 1 + M.HORIZONTE]), "alvo desalinhado"
    _, yb = M._janelas(X, y, np.array([n - 1]))                # origem na borda: t+1..t+4 não existem
    assert np.isnan(yb).all(), "alvo futuro inexistente deveria ser NaN"


# ---------------------------------------------------------------- cabeçalhos HTTP (WS1/WS4)
def test_cabecalhos_seguranca():
    """Trava regressão do after_request: headers de segurança + Cache-Control por tipo de rota."""
    import app as A
    c = A.app.server.test_client()
    r = c.get("/")
    assert r.headers.get("X-Content-Type-Options") == "nosniff", "falta X-Content-Type-Options"
    assert r.headers.get("Referrer-Policy"), "falta Referrer-Policy"
    assert r.headers.get("X-Frame-Options") == "SAMEORIGIN", "falta X-Frame-Options"
    assert r.headers.get("Strict-Transport-Security"), "falta HSTS"
    assert r.headers.get("Permissions-Policy"), "falta Permissions-Policy"
    assert r.headers.get("Content-Security-Policy-Report-Only"), "CSP deve existir (Report-Only por decisão)"
    assert "no-cache" in (r.headers.get("Cache-Control") or ""), "HTML não deve ter cache longo"
    css = c.get("/assets/style.css?m=123")
    assert css.status_code == 200, "assets/style.css deveria responder 200"
    assert "immutable" in (css.headers.get("Cache-Control") or ""), "estático versionado (?m=) deve ser imutável"
    # sem ?m= (fontes/ícones via url() do CSS) NÃO pode ser imutável por 1 ano
    fonte = c.get("/assets/fonts/inter-var.woff2")
    assert "immutable" not in (fonte.headers.get("Cache-Control") or "") and "max-age=86400" in fonte.headers["Cache-Control"]
    # erro nunca é cacheado como imutável (404/500 transitório ficaria 1 ano no navegador/CDN)
    nf = c.get("/assets/nao-existe.png?m=1")
    assert nf.status_code == 404 and nf.headers.get("Cache-Control") == "no-store"
    # o layout varia por Referer/Accept-Language: nada de cache compartilhável
    lay = c.get("/_dash-layout")
    assert lay.headers.get("Cache-Control") == "no-cache" and "Referer" in lay.headers.get("Vary", "")


# ---------------------------------------------------------------- UI nova (F3–F5)
def test_semana_epi():
    from datetime import date

    import dados
    casos = {date(2026, 10, 25): (2026, 43), date(2026, 11, 1): (2026, 44),
             date(2026, 11, 22): (2026, 47), date(2026, 1, 4): (2026, 1),
             date(2026, 1, 1): (2025, 53), date(2024, 12, 29): (2025, 1)}
    for d, exp in casos.items():
        assert dados.semana_epi(d) == exp, f"{d}: {dados.semana_epi(d)} != {exp}"


def test_resumo_situacao():
    import dados
    r = dados.ORIGINAL.resumo
    assert sum(r["por_nivel"].values()) == r["n_cidades"] == len(dados.ORIGINAL.mapa_cid), "soma por nível != n_cidades"
    assert r["total_h1"] == int(dados.ORIGINAL.mapa_cid["prev"].sum()), "total_h1 != soma das previsões"


def test_fmt_int_por_idioma():
    from i18n import fmt_int
    assert fmt_int(5291, "pt") == "5.291" and fmt_int(5291, "es") == "5.291", "pt/es usam ponto"
    assert fmt_int(5291, "en") == "5,291", "en usa vírgula"


def test_horizontes_4_itens():
    import dados
    import figuras
    out = figuras.horizontes(dados.ORIGINAL.geo0, "pt")
    assert len(out[0].children) == 4, f"esperava 4 horizontes, veio {len(out[0].children)}"


def test_tabela_ranking():
    import dados
    import layout
    table = layout.tabela_ranking("pt", n=8).children[0]
    assert type(table.children[0]).__name__ == "Caption", "Caption deve ser o 1º filho da tabela"
    assert len(table.children[2].children) == 8, "n=8 deve limitar a 8 linhas"
    # padrão: lista COMPLETA, da maior para a menor previsão
    completa = layout.tabela_ranking("pt").children[0]
    linhas = completa.children[2].children
    assert len(linhas) == len(dados.ORIGINAL.mapa_cid), "Tabela 1 deve listar todas as cidades monitoradas"
    prevs = [int(l.children[1].children.replace(".", "").replace("\xa0", "")) for l in linhas]
    assert prevs == sorted(prevs, reverse=True), "Tabela 1 deve vir ordenada da maior para a menor"


def test_referencias_doi():
    import re

    import conteudo
    slugs = [r["slug"] for r in conteudo.REFERENCIAS]
    for r in conteudo.REFERENCIAS:
        assert re.match(r"^10\.\d{4,9}/\S+$", r["doi"]), f"DOI inválido: {r['doi']}"
    assert len(set(slugs)) == len(slugs), "slugs de referência duplicados"


def test_citation_cff_route():
    import app as A
    r = A.app.server.test_client().get("/CITATION.cff")
    assert r.status_code == 200 and "cff-version" in r.get_data(as_text=True), "/CITATION.cff deve servir o arquivo"


def test_meta_academica():
    import app as A
    html_ = A.app.server.test_client().get("/").get_data(as_text=True)
    assert "citation_title" in html_, "falta meta citation_title"
    assert "citation_pdf_url" not in html_, "não deve haver citation_pdf_url (sem PDF)"
    assert "application/ld+json" in html_ and "ScholarlyArticle" in html_, "falta JSON-LD"


def test_clipboard_citar():
    """Dois dcc.Clipboard (ABNT + BibTeX) presentes no layout."""
    import app as A
    j = A.app.server.test_client().get("/_dash-layout").get_data(as_text=True)
    assert j.count('"Clipboard"') == 2, "esperava 2 dcc.Clipboard (ABNT e BibTeX)"


# ---------------------------------------------------------------- Fase 5: gráficos
def _tokens_css():
    """Resolve os tokens de assets/style.css: (claro, escuro). Segue var(--x) em cadeia."""
    import re
    css = open(os.path.join(WEBAPP, "assets", "style.css"), encoding="utf-8").read()
    claro_bloco = re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1)
    escuro_bloco = re.search(r':root\[data-theme="dark"\]\s*\{(.*?)\n\}', css, re.S).group(1)
    par = lambda b: dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", b))
    claro = par(claro_bloco)
    escuro = {**claro, **par(escuro_bloco)}

    def resolve(d):
        def r(v, n=0):
            m = re.fullmatch(r"var\((--[\w-]+)\)", v.strip())
            return r(d[m.group(1)], n + 1) if m and n < 5 else v.strip()
        return {k: r(v).upper() for k, v in d.items()}
    return resolve(claro), resolve(escuro)


def test_plot_sincronizado_com_tokens_css():
    """CLAUDE.md: as cores existem em DOIS lugares (tokens CSS e PLOT de figuras.py) e devem ficar em
    sincronia. Este teste trava o que hoje é idêntico. EXCEÇÕES CONHECIDAS no escuro (valores próprios do
    gráfico, escolhidos p/ contraste sobre o papel escuro): grid, axis — não entram aqui. `prev` agora tem
    token próprio (--series-prev) e a legenda HTML acompanha a linha em ambos os temas."""
    import figuras
    claro, escuro = _tokens_css()
    L, D = figuras.PLOT["light"], figuras.PLOT["dark"]
    esperado_claro = {"ink": "--ink", "obs": "--ink", "grid": "--cream-2", "axis": "--line",
                      "paper": "--paper", "prev": "--series-prev", "hover_bg": "--paper", "hover_bd": "--line"}
    for chave, token in esperado_claro.items():
        assert L[chave].upper() == claro[token], f"PLOT[light][{chave}]={L[chave]} ≠ {token}={claro[token]}"
    esperado_escuro = {"ink": "--ink", "obs": "--ink", "paper": "--paper", "hover_bg": "--cream-2",
                       "prev": "--series-prev"}
    for chave, token in esperado_escuro.items():
        assert D[chave].upper() == escuro[token], f"PLOT[dark][{chave}]={D[chave]} ≠ {token}={escuro[token]}"


def test_banda_90_tem_bordas_visiveis_3a1():
    """A banda sozinha tem ~1,3:1 (claro) / 1,6:1 (escuro) — abaixo dos 3:1 de WCAG 1.4.11. As bordas finas
    (sup/inf) na cor da previsão devem existir e ter ≥3:1 contra o papel nos dois temas."""
    import figuras
    from dados import ORIGINAL
    GEO0 = ORIGINAL.geo0
    for tema in ("light", "dark"):
        fig = figuras.figura_detalhe(GEO0, "pt", tema)
        p = figuras.PLOT[tema]
        bordas = [t for t in fig.data if t.mode == "lines" and t.line.width == 1 and t.line.color == p["prev"]]
        assert len(bordas) == 2, f"[{tema}] esperava 2 bordas (sup/inf), achei {len(bordas)}"
        assert contraste(p["prev"], p["paper"]) >= 3.0, f"[{tema}] borda {p['prev']} sobre {p['paper']}"


def test_figura_detalhe_localiza_data_no_hover():
    import figuras
    from dados import ORIGINAL
    GEO0 = ORIGINAL.geo0
    assert figuras.figura_detalhe(GEO0, "pt").layout.xaxis.hoverformat == "%d/%m/%Y"
    assert figuras.figura_detalhe(GEO0, "es").layout.xaxis.hoverformat == "%d/%m/%Y"
    assert figuras.figura_detalhe(GEO0, "en").layout.xaxis.hoverformat == "%m/%d/%Y"


def test_callbacks_toleram_payloads_forjados():
    """Antes: int em _geo_valido → AttributeError/500; clickData malformado → IndexError/TypeError."""
    import app as A
    import dados as D
    assert A._geo_valido(4106902) is False and A._geo_valido(["x"]) is False
    assert A._geo_valido(D.ORIGINAL.geo0) is True and A._geo_valido("UF-PR") is True and A._geo_valido("UF-ZZ") is False
    ns = A.no_update
    for click in ({"points": []}, {"points": ["x"]}, {"points": [{"location": ["SP"]}]},
                  {"points": [{"customdata": 4106902}]}, {}, None, {"points": [{"location": "ZZ"}]}):
        assert A.clique_mapa(click) == (ns, ns)
    assert A.clique_mapa({"points": [{"location": "SP"}]}) == ("SP", ns)
    for uf in (["SP"], 1, {"a": 1}, "ZZ"):                      # uf forjada → escopo nacional, sem exceção
        A.zoom_uf(uf)
        A.remapa_idioma("pt", False, uf, "light")


def test_tema_mapa_espelha_contorno_dos_estados():
    """O Patch de tema deve recolorir também marker.line (antes ficava com o valor do tema claro)."""
    import app as A
    import dados as D
    from figuras import PLOT
    ops = {tuple(o["location"]): o["params"]["value"] for o in A.tema_mapa("dark")._operations}
    assert ops[("data", D.ORIGINAL.idx_choropleth, "marker", "line", "color")] == PLOT["dark"]["mapline"]
    assert ops[("data", D.ORIGINAL.idx_choropleth, "marker", "line", "width")] == PLOT["dark"]["maplinew"]


def test_popular_cidades_ao_trocar_idioma_nao_reverte_a_cidade():
    """Trocar idioma só traduz os rótulos; o value (cidade escolhida) não pode voltar para 'UF-xx'."""
    from dash._callback_context import context_value
    from dash._utils import AttributeDict

    import app as A
    import dados as D
    uf = next(u for u, l in D.ORIGINAL.cidades_por_uf.items() if l)

    def chama(trigger):
        ctx_val = AttributeDict(triggered_inputs=[{"prop_id": trigger}], inputs_list=[], states_list=[],
                                outputs_list=[], args_grouping=[], response=None)
        tok = context_value.set(ctx_val)
        try:
            return A.popular_cidades.__wrapped__(uf, "es") if hasattr(A.popular_cidades, "__wrapped__") \
                else A.popular_cidades(uf, "es")
        finally:
            context_value.reset(tok)
    _, v_lang = chama("lang.data")
    _, v_uf = chama("dd-uf.value")
    assert v_lang is A.no_update and v_uf == f"UF-{uf}"


def _mistura(frente_rgb, alfa, fundo_hex):
    f = fundo_hex.lstrip("#")
    fr = [int(f[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(round(alfa * a + (1 - alfa) * b) for a, b in zip(frente_rgb, fr))


def test_contraste_derivado_dos_tokens_reais_dos_dois_temas():
    """Pares derivados de style.css (não hex digitados): o overlay do .seg-group, o anel de foco sobre
    barra/hero (fundos escuros nos 2 temas), a borda do dropdown e a legenda da série. Regressões medidas
    na auditoria: topbar-muted no escuro 6,2:1 sobre o overlay; foco claro 1,4–1,8:1 sobre barra/hero."""
    claro, escuro = _tokens_css()
    for nome, t in (("claro", claro), ("escuro", escuro)):
        seg_bg = _mistura((255, 255, 255), 0.07, t["--topbar-bg"])          # fundo real dos botões .seg
        assert contraste(t["--topbar-muted"], seg_bg) >= 7.0, f"{nome}: topbar-muted/seg-group"
        assert contraste(t["--topbar-muted"], t["--topbar-bg"]) >= 7.0, f"{nome}: topbar-muted/topbar"
        for fundo in ("--topbar-bg", "--brand"):                             # barra, hero, faixa, rodapé
            assert contraste(t["--focus-on-dark"], t[fundo]) >= 3.0, f"{nome}: foco/{fundo}"
        assert contraste(t["--border-strong"], t["--paper"]) >= 3.0, f"{nome}: borda do dropdown/paper"
        assert contraste(t["--series-prev"], t["--paper"]) >= 3.0, f"{nome}: legenda da série/paper"


def _lab_sim(hexc, mat):
    import numpy as np
    c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    s = np.clip(np.array(mat) @ lin, 0, 1)
    lin = s
    m = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]])
    x = m @ lin / np.array([.95047, 1, 1.08883])
    f = np.where(x > 216 / 24389, np.cbrt(x), (24389 / 27 * x + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def test_paleta_cvd_nao_piora_e_valores_documentados():
    """dados.py documenta o pior par (ΔE76, Machado 2009, sev. 1,0). Trava os números e a direção:
    a paleta CVD nunca pode ser pior que a padrão (antes o comentário afirmava 59,3 — não reproduzível)."""
    import itertools

    import numpy as np

    import dados
    mach = {"deuter": [[.367322, .860646, -.227968], [.280085, .672501, .047413], [-.011820, .042940, .968881]],
            "prot": [[.152286, 1.052583, -.204868], [.114503, .786281, .099216], [-.003882, -.048116, 1.051998]]}

    def pior(pal, k):
        labs = {n: _lab_sim(pal[n], mach[k]) for n in dados.ORDEM_NIVEL}
        return min(np.linalg.norm(labs[a] - labs[b]) for a, b in itertools.combinations(dados.ORDEM_NIVEL, 2))
    esperado = {("padrao", "prot"): 17.4, ("cvd", "prot"): 26.9, ("padrao", "deuter"): 10.1, ("cvd", "deuter"): 11.6}
    for (nome, k), v in esperado.items():
        pal = dados.CORES_NIVEL if nome == "padrao" else dados.CORES_NIVEL_CVD
        assert abs(pior(pal, k) - v) < 0.2, (nome, k, pior(pal, k), v)
    for k in mach:
        assert pior(dados.CORES_NIVEL_CVD, k) >= pior(dados.CORES_NIVEL, k)


def test_bolhas_tem_anel_com_espessura_por_nivel_e_contraste():
    """Cor não é canal único (1.4.1) e a bolha precisa de contorno ≥3:1 (1.4.11): camada de anel sob cada nível,
    espessura crescente e hoverinfo=skip (o clique/hover continua só na bolha)."""
    import dados
    import figuras
    fig = figuras.figura_mapa()
    aneis = [i for i, t in enumerate(fig.data) if str(t.name or "").startswith("anel-")]
    assert aneis == figuras.indices_anel() and aneis
    for i in aneis:
        anel, bolha = fig.data[i], fig.data[i + 1]
        assert anel.hoverinfo == "skip" and anel.customdata is None and bolha.customdata is not None
        assert all(a > b for a, b in zip(anel.marker.size, bolha.marker.size))
    esp = [figuras.ESPESSURA_ANEL[n] for n in dados.ORDEM_NIVEL]
    assert esp == sorted(esp) and len(set(esp)) == 4
    for tema_, fundo_mapa in (("light", "#F5F3EE"), ("dark", "#1A1A1A")):
        ring = figuras.PLOT[tema_]["ring"]
        assert contraste(ring, fundo_mapa) >= 3.0, f"{tema_}: anel/mapa"
        for pal in (dados.CORES_NIVEL, dados.CORES_NIVEL_CVD):
            for nv, cor in pal.items():           # borda perceptível: preenchimento×mapa OU anel×preenchimento
                assert max(contraste(cor, fundo_mapa), contraste(ring, cor)) >= 3.0, f"{tema_}: {nv} {cor}"


def test_tema_do_mapa_recolore_os_aneis():
    import app as A
    import figuras
    ops = {tuple(o["location"]): o["params"]["value"] for o in A.tema_mapa("dark")._operations}
    for i in figuras.indices_anel():
        assert ops[("data", i, "marker", "color")] == figuras.PLOT["dark"]["ring"]


def test_lock_sincronizado():
    """A imagem instala do requirements.lock: todo pin de requirements.txt deve estar igual no lock.
    (O Dependabot só edita o .txt; sem este teste um bump de PR não chegaria à imagem.)"""
    import re
    raiz = os.path.dirname(DATA)
    norm = lambda n: re.sub(r"[-_.]+", "-", n).lower()
    pins = {}
    for ln in open(os.path.join(raiz, "requirements.txt"), encoding="utf-8"):
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s#;]+)", ln.strip())
        if m:
            pins[norm(m.group(1))] = m.group(2)
        else:
            assert not ln.strip() or ln.lstrip().startswith("#"), f"requirements.txt: use pin exato (==): {ln!r}"
    lock = {}
    for ln in open(os.path.join(raiz, "requirements.lock"), encoding="utf-8"):
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s\\;]+)", ln)
        if m:
            lock[norm(m.group(1))] = m.group(2)
    assert pins, "requirements.txt sem pins"
    assert open(os.path.join(raiz, "requirements.lock"), encoding="utf-8").read().count("--hash=sha256:") >= len(pins), \
        "requirements.lock sem hashes (gere com --generate-hashes)"
    dif = {k: (v, lock.get(k)) for k, v in pins.items() if lock.get(k) != v}
    assert not dif, ("requirements.lock divergente de requirements.txt (regere com "
                     f"`uv pip compile ... --generate-hashes`): {dif}")


def test_requirements_ci_numpy_compativel_com_tf():
    """TF 2.18 exige numpy < 2.1: um bump do Dependabot nesta faixa quebra o refresh (ocorreu em 2026-11-28)."""
    import re
    txt = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "pipeline", "requirements-ci.txt"), encoding="utf-8").read()
    m = re.search(r"^numpy[^\n]*$", txt, re.M)
    assert m and re.search(r"<\s*2\.[0-2]\b", m.group(0)), m and m.group(0)
