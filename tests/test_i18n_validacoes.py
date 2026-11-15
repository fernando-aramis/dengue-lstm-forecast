# -*- coding: utf-8 -*-
"""Validações de i18n/locale que faltavam (auditoria pós-fase 6)."""
import json
import re

import pytest

import app as A
from dash._utils import to_json
import i18n
from layout import serve_layout, _contexto_inicial

LANGS = ("pt", "en", "es")
NOVAS = ("cartao_resumo_aria_semcob", "detalhe_sem_serie", "se_abrev", "figura_pref", "tabela_pref",
         "idioma_label", "tema_label", "boot_lede", "boot_msg", "boot_noscript")


def test_paridade_completa_das_chaves_e_placeholders():
    for chave, d in i18n.T.items():
        for l in LANGS:
            assert l in d, f"{chave}: falta {l}"
            if not (chave == "artigo_nota_idioma" and l == "pt"):    # pt dispensa a nota de idioma
                assert str(d[l]).strip(), f"{chave}.{l} vazio"
        ph = {l: set(re.findall(r"\{(\w+)", str(d[l]))) for l in LANGS}
        assert ph["pt"] == ph["en"] == ph["es"], f"{chave}: placeholders divergem {ph}"
    for k in NOVAS:
        assert k in i18n.T


def test_tr_chave_inexistente_e_idioma_invalido():
    assert i18n.tr("pt", "nao_existe_xyz") == "nao_existe_xyz"
    assert i18n.tr("zz", "brand") == i18n.tr("en", "brand")


def _layout_txt(lang):
    with A.server.test_request_context(headers={"Accept-Language": lang}):
        return json.dumps(json.loads(to_json(serve_layout())), ensure_ascii=False)


@pytest.mark.parametrize("lang,ausentes", [("en", ["Tabela 1.", "Figura 1.", "Tabela 2.", "Figura 2."]),
                                           ("es", ["Tabela 1.", "Table 1.", "Figure 1."])])
def test_rotulos_de_figura_e_tabela_seguem_o_idioma(lang, ausentes):
    txt = _layout_txt(lang)
    for a in ausentes:
        assert a not in txt, f"{lang}: '{a}' hard-coded em outro idioma"
    assert i18n.tr(lang, "tabela_pref", n=1) in txt and i18n.tr(lang, "figura_pref", n=1) in txt


def _acha(no, classe):
    if isinstance(no, dict):
        if classe in str(no.get("props", {}).get("className", "")):
            return no["props"]
        for v in no.values():
            r = _acha(v, classe)
            if r:
                return r
    elif isinstance(no, list):
        for v in no:
            r = _acha(v, classe)
            if r:
                return r
    return None


@pytest.mark.parametrize("lang", ["en", "es"])
def test_nota_de_idioma_tem_lang_do_texto(lang):
    """A nota só aparece fora de pt e está no idioma da UI (antes: lang="pt" fixo → leitor de tela errado)."""
    with A.server.test_request_context(headers={"Accept-Language": lang}):
        arvore = json.loads(to_json(serve_layout()))
    nota = _acha(arvore, "artigo-nota-idioma")
    assert nota is not None and nota.get("lang") == lang


@pytest.mark.parametrize("referer,al,esperado", [
    ("http://x/?lang=es&cidade=4106902", "en-US", ("es", "4106902")),
    ("http://x/?lang=xx", "pt-BR,pt;q=0.9", ("pt", None)),
    ("http://x/?lang=PT", "en", ("pt", None)),
    ("", "es", ("es", None)),
    ("", "fr", ("en", None)),                                   # sem correspondência → en
    ("http://x/?lang=" + "a" * 5000, "pt", ("pt", None)),        # valor gigante é ignorado
    ("::::não é url::::", "pt", ("pt", None)),
])
def test_contexto_inicial_valida_referer(referer, al, esperado):
    with A.server.test_request_context(headers={"Referer": referer, "Accept-Language": al}):
        lang, sel = _contexto_inicial()
    assert lang == esperado[0]
    assert sel == esperado[1]


def test_cidade_forjada_nao_vaza_para_o_layout():
    with A.server.test_request_context(headers={"Referer": "http://x/?cidade=<script>alert(1)</script>"}):
        txt = json.dumps(json.loads(to_json(serve_layout())), ensure_ascii=False)
    assert "<script>alert" not in txt


def test_index_tem_html_lang_precoce_e_shell_trilingue():
    idx = A.app.index_string
    assert "document.documentElement.lang=l" in idx                # <html lang> antes do boot
    for l in LANGS:
        assert f'<div class="boot-l" lang="{l}">' in idx
        assert i18n.tr(l, "boot_msg") in idx
    assert 'translate="no">DOI' in idx


def test_aria_labels_de_grupo_traduzidos():
    assert '"Idioma / Language / Idioma"' not in _layout_txt("en")


def test_sem_formatacao_numerica_fora_de_formato_py():
    """Varredura estática: strftime, '{:,}' e replace(',', '.') só em formato.py."""
    import os
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for f in ("layout.py", "figuras.py", "app.py"):
        src = open(os.path.join(raiz, f), encoding="utf-8").read()
        assert "strftime" not in src, f
        assert "{:,}" not in src and ':,}' not in src.replace(":,.0f", ""), f
        assert '.replace(",", ".")' not in src, f
