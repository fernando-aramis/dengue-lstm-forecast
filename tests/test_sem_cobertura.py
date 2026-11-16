# -*- coding: utf-8 -*-
"""
Estado "estado sem cidade monitorada" (sem cobertura).

Com os dados reais (33 cidades) todas as 27 UFs estão cobertas, então o estado é inalcançável —
mas o smoke do pipeline (CIDADES_GEO=4106902 MODO_RAPIDO=1) e os dados de exemplo o ativam (26 UFs
sem cobertura). Estes testes montam uma CÓPIA TEMPORÁRIA do app só com Curitiba e exercitam toda a
cadeia de defesas num subprocesso (os dados são lidos na importação; não dá para trocá-los no
processo do pytest). O projeto em si não é tocado.
"""
import json
import os
import shutil
import subprocess
import sys

import pandas as pd
import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
WEBAPP = os.path.dirname(AQUI)
CURITIBA = "4106902"

SCRIPT = r"""
import sys, json
sys.path.insert(0, ".")
import app as A, dados as D, figuras as F
out = {}
out["nao_cobertas"] = len(D.NAO_COBERTAS)
out["idx"] = D.IDX_CHOROPLETH
fig = F.figura_mapa()
out["traces"] = [t.type for t in fig.data]
out["t0_hover"] = fig.data[0].hovertemplate
ops = A.tema_mapa("dark")._operations
out["patch_locs"] = [list(o["location"]) for o in ops]
out["resumo"] = {l: F.resumo_cartao("UF-AC", l) for l in ("pt", "en", "es")}
out["resumo_cidade"] = F.resumo_cartao("4106902", "pt")
d = F.figura_detalhe("UF-AC", "pt")
out["detalhe_traces"] = len(d.data)
out["detalhe_msg"] = [a.text for a in d.layout.annotations]
out["detalhe_cidade_traces"] = len(F.figura_detalhe("4106902", "pt").data)
at_uf = A.atualizar("UF-AC", "pt", "light", None)
at_cid = A.atualizar("4106902", "pt", "light", None)
out["hidden_uf"] = at_uf[4]
out["hidden_cidade"] = at_cid[4]
out["live_uf"] = at_uf[3]
out["horizontes_uf"] = len(at_uf[2])
print("@@" + json.dumps(out))
"""


@pytest.fixture(scope="module")
def um_cidade(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("um_cidade")
    for f in os.listdir(WEBAPP):
        if f.endswith(".py"):
            shutil.copy(os.path.join(WEBAPP, f), raiz / f)
    os.symlink(os.path.join(WEBAPP, "assets"), raiz / "assets")
    (raiz / "data").mkdir()
    for f in ("br_uf.geojson", "_meta.json", "eda.json"):
        shutil.copy(os.path.join(WEBAPP, "data", f), raiz / "data" / f)
    for f in ("previsoes.csv", "historico.csv"):
        df = pd.read_csv(os.path.join(WEBAPP, "data", f))
        df[df["geo_id"].astype(str).isin([CURITIBA, "UF-PR"])].to_csv(raiz / "data" / f, index=False)
    r = subprocess.run([sys.executable, "-I", "-c", SCRIPT], cwd=raiz, capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stderr[-1500:]
    linha = [x for x in r.stdout.splitlines() if x.startswith("@@")][-1]
    return json.loads(linha[2:])


def test_cobertura_derivada_dos_dados(um_cidade):
    assert um_cidade["nao_cobertas"] == 26           # 27 UFs − PR (a única com cidade)
    assert um_cidade["idx"] == 1                     # camada cinza no índice 0 empurra o choropleth


def test_mapa_tem_camada_cinza_com_hover_nominal(um_cidade):
    assert um_cidade["traces"] == ["choroplethmap", "choroplethmap", "scattermap", "scattermap"]   # + anel + bolha
    assert "Sem cidade monitorada" in um_cidade["t0_hover"]   # cor não é o único canal


def test_tema_recolore_as_duas_camadas_com_indice_deslocado(um_cidade):
    locs = um_cidade["patch_locs"]
    assert ["data", 0, "colorscale"] in locs         # camada "sem cobertura"
    assert ["data", 1, "colorscale"] in locs         # choropleth estadual (IDX_CHOROPLETH=1)


@pytest.mark.parametrize("lang,trecho", [("pt", "sem cidade monitorada"), ("en", "no monitored city"),
                                         ("es", "sin ciudad monitoreada")])
def test_leitor_de_tela_e_avisado(um_cidade, lang, trecho):
    """Antes: resumo_cartao devolvia '' e o aria-live ficava mudo neste estado."""
    msg = um_cidade["resumo"][lang]
    assert "Acre" in msg and trecho in msg.lower()
    assert um_cidade["live_uf"] == um_cidade["resumo"]["pt"]
    assert "casos previstos" in um_cidade["resumo_cidade"]    # cidade monitorada: texto inalterado


def test_grafico_vazio_vira_mensagem_e_legenda_some(um_cidade):
    assert um_cidade["detalhe_traces"] == 0
    assert um_cidade["detalhe_msg"] and "Sem série temporal" in um_cidade["detalhe_msg"][0]
    assert um_cidade["hidden_uf"] is True            # legenda da série oculta
    assert um_cidade["horizontes_uf"] == 0
    # cidade monitorada: gráfico com séries e legenda visível (caminho principal intacto)
    assert um_cidade["detalhe_cidade_traces"] >= 3
    assert um_cidade["hidden_cidade"] is False


def test_dados_reais_nao_ativam_o_estado():
    """Com os dados reais o estado segue inalcançável: nenhuma legenda oculta, nada de cinza no mapa."""
    for p in (WEBAPP, os.path.join(WEBAPP, "pipeline")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import app as A
    import dados as D
    assert D.NAO_COBERTAS == [] and D.IDX_CHOROPLETH == 0
    assert A.atualizar(D.GEO0, "pt", "light", None)[4] is False
