"""P.2: rota /dados/<geo_id>.csv (allowlist de geo_id, fonte restrita, cabeçalhos, conteúdo)."""
import io

import pandas as pd
import pytest

import app as appmod
import dados


@pytest.fixture(scope="module")
def cli():
    return appmod.server.test_client()


def _geo():
    return dados.ORIGINAL.geo0


def test_csv_ok_cabecalhos_e_colunas(cli):
    r = cli.get(f"/dados/{_geo()}.csv")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert r.headers["Content-Disposition"].startswith("attachment; filename=")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "max-age" in r.headers["Cache-Control"]
    d = pd.read_csv(io.BytesIO(r.data))
    assert list(d.columns) == dados._COLS_CSV + ["fonte", "se_origem"]
    assert sorted(d["h"]) == [1, 2, 3, 4]
    assert (d["fonte"] == "original").all() and d["se_origem"].str.match(r"^\d{4}-\d{2}$").all()
    assert (d["inf"] <= d["prev"]).all() and (d["prev"] <= d["sup"]).all()
    assert d["data_prev"].str.match(r"^\d{4}-\d{2}-\d{2}$").all()


def test_csv_estado_aceito(cli):
    uf = next(g for g in dados.ORIGINAL.nome_por_geo if g.startswith("UF-"))
    assert cli.get(f"/dados/{uf}.csv?fonte=original").status_code == 200


@pytest.mark.parametrize("geo", ["0000000", "..%2Fdados", "%2e%2e%2fapp", "UF-ZZ", "a b", "' OR 1=1"])
def test_csv_geo_invalido_nunca_serve_csv(cli, geo):
    r = cli.get(f"/dados/{geo}.csv")      # com "/" decodificado a rota não casa e o Dash serve o index
    assert not r.headers["Content-Type"].startswith("text/csv")
    assert r.headers.get("Content-Disposition") is None


@pytest.mark.parametrize("geo", ["0000000", "UF-ZZ", "a b", "' OR 1=1"])
def test_csv_geo_desconhecido_404(cli, geo):
    assert cli.get(f"/dados/{geo}.csv").status_code == 404


def test_csv_fonte_invalida_400(cli):
    assert cli.get(f"/dados/{_geo()}.csv?fonte=x").status_code == 400


def test_csv_atual_indisponivel_404(cli, monkeypatch):
    class _Sem:
        def conjunto(self):
            return None
    monkeypatch.setattr(appmod.atual, "global_atual", lambda: _Sem())
    r = cli.get(f"/dados/{_geo()}.csv?fonte=atual")
    assert r.status_code == 404 and b"indispon" in r.data


def test_csv_atual_disponivel(cli, monkeypatch):
    class _Com:
        def conjunto(self):
            return dados.ORIGINAL
    monkeypatch.setattr(appmod.atual, "global_atual", lambda: _Com())
    r = cli.get(f"/dados/{_geo()}.csv?fonte=atual")
    assert r.status_code == 200 and b",atual," in r.data


def test_link_de_download_na_ui():
    from figuras import horizontes
    html = str(horizontes(_geo(), "pt"))
    assert f"/dados/{_geo()}.csv?fonte=original" in html


def test_csv_neutraliza_formulas_em_celulas_de_texto():
    import copy
    c = copy.copy(dados.ORIGINAL)
    prev = dados.ORIGINAL.prev.copy()
    g = dados.ORIGINAL.geo0
    prev.loc[prev["geo_id"] == g, "nome"] = "=HYPERLINK(\"http://x\")"
    object.__setattr__(c, "prev", prev)
    corpo = dados.csv_cidade(c, g, "original")
    assert "'=HYPERLINK" in corpo and ",=HYPERLINK" not in corpo
