# -*- coding: utf-8 -*-
"""
axe-core (vendorizado em tests/vendor/, MPL-2.0 — sem CDN) com as regras AAA, que o axe padrão NÃO roda.

* Estados FECHADOS (página inteira, 2 temas): 0 violações. Foi aqui que o contraste 6,2:1 dos botões da
  barra no escuro passou despercebido.
* Estados ABERTOS (menu de acessibilidade e dropdown): o Dash 4.5 emite marcação interna que o axe
  rejeita e que NÃO é corrigível do nosso lado (ver docs/ui/A11Y-EXCECOES.md). A exceção é um conjunto
  FECHADO de regras: qualquer regra nova, ou aumento de ocorrências acima do teto, falha o teste.
"""
import os

import pytest
from test_e2e import URL, pagina, servidor  # noqa: F401  (fixtures)

AXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "axe.min.js")
TAGS = ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]
# regra → teto de ocorrências aceito (marcação do Dash 4.5: role=option em <label>, botões aninhados,
# popover radix sem nome, listbox sem nome). Valores medidos em 2026-11-15 com margem pequena.
EXCECOES_DASH = {"aria-allowed-role": 40, "nested-interactive": 40, "aria-dialog-name": 2,
                 "aria-input-field-name": 3}   # medido: 33/33/1/1 (dropdown) e 2/2/0/1 (menu a11y)


def _axe(pg):
    pg.add_script_tag(path=AXE)
    return pg.evaluate("""async (tags) => {
      const r = await axe.run(document, {runOnly: {type: 'tag', values: tags}});
      return r.violations.map(v => [v.id, v.nodes.length, v.nodes[0].target.join(' ').slice(0, 70)]);}""", TAGS)


def _abre(pg, largura, tema):
    pg.set_viewport_size({"width": largura, "height": 900})
    pg.goto(URL.rstrip("/") + "/?lang=pt")
    pg.wait_for_selector("#cartao", timeout=40000)
    pg.wait_for_timeout(1200)
    if tema == "dark":
        if largura < 1180:
            pg.click(".prefs-trigger")
        pg.click("#theme-dark")
        pg.wait_for_function("()=>document.documentElement.dataset.theme==='dark'", timeout=15000)
        if largura < 1180:
            pg.keyboard.press("Escape")
        pg.wait_for_timeout(1000)                        # fim da transição de cor (senão o axe mede no meio)


@pytest.mark.parametrize("largura", [390, 1280])
@pytest.mark.parametrize("tema", ["light", "dark"])
def test_axe_aaa_estados_fechados(pagina, largura, tema):
    _abre(pagina, largura, tema)
    assert _axe(pagina) == []


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_axe_menus_abertos_so_tem_as_excecoes_do_dash(pagina, tema):
    _abre(pagina, 1280, tema)
    pagina.click("summary.a11y-summary")
    pagina.wait_for_timeout(400)
    achados = _axe(pagina)
    pagina.keyboard.press("Escape")
    pagina.click("#dd-cidade")
    pagina.wait_for_timeout(500)
    achados += _axe(pagina)
    for regra, n, alvo in achados:
        assert regra in EXCECOES_DASH, f"regra nova fora da exceção: {regra} ({n}) em {alvo}"
        assert n <= EXCECOES_DASH[regra], f"{regra}: {n} ocorrências > teto {EXCECOES_DASH[regra]}"
