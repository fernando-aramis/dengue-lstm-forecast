# -*- coding: utf-8 -*-
"""Formatação por idioma (A1): números e datas corretos em PT/EN/ES."""
from datetime import date

import pytest

import formato as f

NBSP, ENDASH, MINUS = " ", "–", "−"


@pytest.mark.parametrize("lang,esperado", [("pt", "15.389"), ("es", "15.389"), ("en", "15,389")])
def test_fmt_int_milhar(lang, esperado):
    assert f.fmt_int(15389, lang) == esperado


@pytest.mark.parametrize("lang,esperado", [("pt", "1,16"), ("es", "1,16"), ("en", "1.16")])
def test_fmt_dec(lang, esperado):
    assert f.fmt_dec(1.16, lang, 2) == esperado


@pytest.mark.parametrize("lang,esperado", [("pt", "1.234,5"), ("en", "1,234.5")])
def test_fmt_dec_milhar_e_decimal(lang, esperado):
    assert f.fmt_dec(1234.5, lang, 1) == esperado


@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_fmt_pct_negativo_usa_sinal_de_menos(lang):
    out = f.fmt_pct(-0.14, lang)
    assert out == f"{MINUS}14%"
    assert "-" not in out  # hífen-menos não entra


@pytest.mark.parametrize("lang,esperado", [("pt", "01/11"), ("es", "01/11"), ("en", "11/01")])
def test_fmt_data_curto_ordem_por_idioma(lang, esperado):
    assert f.fmt_data(date(2026, 11, 1), lang, "curto") == esperado


@pytest.mark.parametrize("lang,esperado", [("pt", "01/11/2026"), ("en", "11/01/2026")])
def test_fmt_data_ano(lang, esperado):
    assert f.fmt_data(date(2026, 11, 1), lang, "ano") == esperado


@pytest.mark.parametrize("lang,esperado", [("pt", "1 nov"), ("en", "Nov 1"), ("es", "1 nov")])
def test_fmt_data_mes(lang, esperado):
    assert f.fmt_data(date(2026, 11, 1), lang, "mes") == esperado


def test_fmt_intervalo_usa_endash():
    assert f.fmt_intervalo(94, 98, "pt") == f"94{ENDASH}98"


def test_plotly_separators():
    assert f.plotly_separators("pt") == ",."
    assert f.plotly_separators("es") == ",."
    assert f.plotly_separators("en") == ".,"


def test_idioma_desconhecido_cai_em_pt():
    assert f.fmt_int(1000, "zz") == "1.000"


def test_reexport_via_i18n():
    import i18n
    assert i18n.fmt_int(15389, "en") == "15,389"
    assert i18n.fmt_dec(1.16, "pt", 2) == "1,16"


# ------------------------------------------------------------------ locale do Plotly (Fase 5)
@pytest.mark.parametrize("lang", ["pt", "en", "es"])
def test_plotly_locale_completo_e_coerente(lang):
    loc = f.plotly_locale(lang)["format"]
    assert len(loc["months"]) == len(loc["shortMonths"]) == 12
    assert len(loc["days"]) == len(loc["shortDays"]) == 7
    assert loc["shortMonths"] == f._MESES[f._lang(lang)]          # fonte única dos nomes de mês
    assert loc["decimal"] + loc["thousands"] == f.plotly_separators(lang)   # mesmos separadores do A1
    assert all(m.lower().startswith(s.lower()[:3]) for m, s in zip(loc["months"], loc["shortMonths"]))


def test_plotly_locale_data_dia_primeiro_so_em_pt_es():
    assert f.plotly_locale("pt")["format"]["date"] == f.plotly_locale("es")["format"]["date"] == "%d/%m/%Y"
    assert f.plotly_locale("en")["format"]["date"] == "%m/%d/%Y"
