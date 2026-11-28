# -*- coding: utf-8 -*-
"""Publicação consistente e probe (Fase 1.2) — funções puras, sem rede."""
import hashlib
import json
import os
import re
import shutil

import probe
import publicar_run

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(AQUI), "data")


def _saida(tmp_path):
    d = tmp_path / "saida"
    d.mkdir()
    for n in ("previsoes.csv", "historico.csv", "_meta.json", "eda.json"):
        shutil.copy(os.path.join(DATA, n), d / n)
    return str(d)


def test_nome_run_formato_e_sha_invalido():
    assert publicar_run.nome_run("2026-11-15", "ABCDEF1234") == ("202646-abcdef1", "202646")
    assert publicar_run.nome_run("2026-11-15", None)[0] == "202646-0000000"
    assert publicar_run.nome_run("2026-11-15", "zzzzzzzz")[0] == "202646-0000000"
    assert re.match(r"^[0-9]{6}-[0-9a-f]{7}$", publicar_run.nome_run("2026-01-04", "1234567")[0])


def test_publicar_gera_run_imutavel_e_ponteiro_confere(tmp_path):
    destino = tmp_path / "data"
    destino.mkdir()
    run = publicar_run.publicar(_saida(tmp_path), str(destino), commit="a1b2c3d4")
    ptr = json.load(open(destino / "latest.json", encoding="utf-8"))
    assert ptr["run"] == run and ptr["se_origem"] == json.load(open(os.path.join(DATA, "_meta.json")))["se_origem"][:10]
    for nome in ("previsoes.csv", "historico.csv", "_meta.json"):
        corpo = (destino / "runs" / run / nome).read_bytes()
        assert hashlib.sha256(corpo).hexdigest() == ptr["sha256"][nome]
    assert not (destino / "latest.json.tmp").exists()


def test_publicar_exige_obrigatorios(tmp_path):
    import pytest
    d = tmp_path / "vazio"
    d.mkdir()
    with pytest.raises(SystemExit):
        publicar_run.publicar(str(d), str(tmp_path))


def test_probe_decisao():
    assert probe.precisa_treinar("2026-11-22", None) is True
    assert probe.precisa_treinar("2026-11-22", "2026-11-15") is True
    assert probe.precisa_treinar("2026-11-15", "2026-11-15") is False
    assert probe.precisa_treinar(None, "2026-11-15") is True       # falha de consulta: treina


def test_probe_le_ponteiro(tmp_path):
    p = tmp_path / "latest.json"
    p.write_text(json.dumps({"se_origem": "2026-11-15"}))
    assert probe.ler_publicada(str(p)) == "2026-11-15"
    assert probe.ler_publicada(str(tmp_path / "nao.json")) is None
    p.write_text("lixo")
    assert probe.ler_publicada(str(p)) is None
