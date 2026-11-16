# -*- coding: utf-8 -*-
"""Lacunas do Nielsen tratadas no refino final: glossário no ponto de uso, comparação entre cidades,
validação do valor forjado de `cmp` e cor da série de comparação (contraste + sincronia PLOT↔CSS)."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import figuras as F  # noqa: E402
import app as A  # noqa: E402
from dados import prev  # noqa: E402
from i18n import T  # noqa: E402
from test_unit import contraste  # noqa: E402

CWB, ARACAJU = "4106902", None


def _texto(no):
    """Texto de uma árvore de componentes Dash (para asserts sobre o que o usuário lê)."""
    if no is None:
        return ""
    if isinstance(no, (str, int, float)):
        return str(no)
    if isinstance(no, (list, tuple)):
        return " ".join(_texto(n) for n in no)
    return _texto(getattr(no, "children", None))


def _outra_cidade():
    ids = [g for g in prev["geo_id"].unique() if g != CWB]
    return ids[0]


@pytest.mark.parametrize("lang,sigla", [("pt", "SE"), ("en", "EW"), ("es", "SE")])
def test_glossario_t_n_e_se_no_ponto_de_uso(lang, sigla):
    """t+N e SE são explicados abaixo dos cartões t+1…t+4 (antes: jargão sem glossário)."""
    txt = _texto(F.horizontes(CWB, lang))
    assert "t+N" in txt and f"{sigla}:" in txt


@pytest.mark.parametrize("lang,chave", [("pt", "número de reprodução"), ("en", "reproduction number"),
                                         ("es", "número reproductivo")])
def test_rt_expandido_na_nota_do_nivel(lang, chave):
    assert chave in T["nota_nivel"][lang]


@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_conformal_ganha_glosa_na_primeira_aparicao_visivel(lang):
    for k in ("map_fonte", "aviso_info_p"):
        if k in T:
            assert re.search(r"conforme|conformal", T[k][lang], re.I) is None or "(" in T[k][lang]
    # nenhuma chave de interface usa "conformal" sem a glosa entre parênteses (o artigo explica no corpo)
    for k, v in T.items():
        if k.startswith(("aviso_", "map_", "lede", "sit_")) and re.search(r"conforma?l?e?", v[lang], re.I):
            assert "(" in v[lang], f"{k}/{lang}: 'conformal' sem glosa"


@pytest.mark.parametrize("forjado", [None, 0, 1.5, [], {}, "", "abc", "UF-PR", CWB])
def test_comparacao_valida_rejeita_valores_forjados(forjado):
    assert F.comparacao_valida(CWB, forjado) is None


def test_comparacao_valida_aceita_municipio_diferente_e_rejeita_estado_principal():
    outra = _outra_cidade()
    assert F.comparacao_valida(CWB, outra) == outra
    assert F.comparacao_valida("UF-PR", outra) is None       # comparar só vale entre municípios
    assert F.comparacao_valida(123, outra) is None


def test_figura_com_comparacao_tem_canal_alem_da_cor():
    outra = _outra_cidade()
    base = F.figura_detalhe(CWB, "pt", "light")
    comp = F.figura_detalhe(CWB, "pt", "light", outra)
    assert len(comp.data) == len(base.data) + 2
    novas = comp.data[len(base.data):]
    prevista = [t for t in novas if t.mode == "lines+markers"][0]
    assert prevista.line.dash == "dot" and prevista.marker.symbol == "diamond"   # forma/traço, não só cor
    nomes = " ".join(t.name or "" for t in comp.data)
    assert "Curitiba" in nomes and prev[prev["geo_id"] == outra]["nome"].iloc[0] in nomes   # hover distingue as cidades


def test_comparacao_valida_nao_altera_a_figura_quando_invalida():
    base = F.figura_detalhe(CWB, "pt", "light")
    assert len(F.figura_detalhe(CWB, "pt", "light", "forjado").data) == len(base.data)


def test_tabela_de_comparacao_e_alternativa_textual():
    outra = _outra_cidade()
    sem = _texto(F.horizontes(CWB, "pt"))
    com = F.horizontes(CWB, "pt", outra)
    assert T["cmp_tab_cap"]["pt"] not in sem
    assert T["cmp_tab_cap"]["pt"] in _texto(com) and T["cmp_hint"]["pt"] in _texto(com)
    assert "Curitiba" in _texto(com) and prev[prev["geo_id"] == outra]["nome"].iloc[0] in _texto(com)


def test_anuncio_do_cartao_inclui_a_comparacao():
    outra = _outra_cidade()
    assert len(F.resumo_cartao(CWB, "pt", outra)) > len(F.resumo_cartao(CWB, "pt"))
    assert F.resumo_cartao(CWB, "pt", "forjado") == F.resumo_cartao(CWB, "pt")


def test_callbacks_toleram_cmp_forjado():
    for forjado in (None, 7, ["x"], {"a": 1}, "UF-PR", "zzz", CWB):
        saida = A.atualizar(CWB, "pt", "light", forjado)
        assert len(saida) == 8 and saida[6] is True            # legenda da comparação oculta
        if forjado != CWB:            # CWB é município válido p/ o store (a comparação efetiva é filtrada em atualizar)
            assert A.selecionar_cmp(forjado) is None
    assert A.selecionar_cmp(_outra_cidade()) == _outra_cidade()
    assert A.atualizar("UF-PR", "pt", "light", _outra_cidade())[5] is True    # dropdown desabilitado p/ estado


@pytest.mark.parametrize("tema,fundo", [("light", "paper"), ("dark", "paper")])
def test_cor_da_serie_de_comparacao_tem_contraste_de_grafico(tema, fundo):
    """WCAG 1.4.11: linha do gráfico ≥3:1 sobre o fundo; e distinta da previsão da cidade principal."""
    p = F.PLOT[tema]
    assert contraste(p["cmp"], p[fundo]) >= 3.0
    assert p["cmp"].lower() != p["prev"].lower() and p["cmp"].lower() != p["obs"].lower()


def test_token_css_da_comparacao_acompanha_o_plot():
    css = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.css"),
               encoding="utf-8").read()
    achados = re.findall(r"--series-cmp:\s*(#[0-9A-Fa-f]{6})", css)
    assert [a.lower() for a in achados][:2] == [F.PLOT["light"]["cmp"].lower(), F.PLOT["dark"]["cmp"].lower()]


def test_resultados_chave_vem_depois_do_painel():
    from layout import construir_conteudo

    def ids(no, acc):
        if isinstance(no, (list, tuple)):
            for n in no:
                ids(n, acc)
        elif no is not None and not isinstance(no, (str, int, float)):
            if getattr(no, "id", None):
                acc.append(no.id)
            ids(getattr(no, "children", None), acc)
        return acc
    ordem = ids(construir_conteudo("pt"), [])
    assert ordem.index("painel") < ordem.index("resultados-chave")
    assert ordem.index("indicadores") < ordem.index("painel")
