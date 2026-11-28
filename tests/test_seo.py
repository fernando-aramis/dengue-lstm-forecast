# -*- coding: utf-8 -*-
"""SEO (Fase 1.13–1.15): metatags, canonical, robots/sitemap, imagem OG. Sem navegador."""
import os
import re
import struct

import pytest

import app as A
import conteudo

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def html():
    return A.server.test_client().get("/").get_data(as_text=True)


def _meta(html, chave, valor):
    m = re.search(rf'<meta {chave}="{re.escape(valor)}" content="([^"]*)"', html)
    return m.group(1) if m else None


def test_description_e_og_completo(html):
    assert 60 <= len(_meta(html, "name", "description") or "") <= 200
    for p in ("og:description", "og:url", "og:image", "og:locale", "og:site_name", "og:image:alt"):
        assert _meta(html, "property", p), p
    assert _meta(html, "property", "og:url") == conteudo.PUBLIC_URL + "/"
    assert _meta(html, "property", "og:image").endswith("/assets/og.png")
    assert _meta(html, "name", "twitter:card") == "summary_large_image"


def test_canonical_unico_e_sem_hreflang(html):
    assert html.count('rel="canonical"') == 1
    assert f'<link rel="canonical" href="{conteudo.PUBLIC_URL}/">' in html
    assert "hreflang" not in html


def test_jsonld_tem_date_modified(html):
    assert re.search(r'"dateModified": "\d{4}-\d{2}-\d{2}"', html)


@pytest.mark.parametrize("caminho,tipo,trecho", [
    ("/robots.txt", "text/plain", "Sitemap: " + conteudo.PUBLIC_URL + "/sitemap.xml"),
    ("/sitemap.xml", "application/xml", "<loc>" + conteudo.PUBLIC_URL + "/</loc>"),
])
def test_robots_e_sitemap(caminho, tipo, trecho):
    r = A.server.test_client().get(caminho)
    assert r.status_code == 200 and r.mimetype == tipo and trecho in r.get_data(as_text=True)
    assert r.headers["Cache-Control"] == "public, max-age=3600"
    assert r.headers["X-Content-Type-Options"] == "nosniff"          # herda os cabeçalhos de segurança


def test_sitemap_so_tem_a_raiz():
    corpo = A.server.test_client().get("/sitemap.xml").get_data(as_text=True)
    assert corpo.count("<url>") == 1


def test_imagem_og_1200x630_e_leve():
    p = os.path.join(WEBAPP, "assets", "og.png")
    assert os.path.getsize(p) < 300 * 1024
    with open(p, "rb") as f:
        cab = f.read(24)
    assert cab[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", cab[16:24]) == (1200, 630)
