# -*- coding: utf-8 -*-
"""
Valida os geocodes de cidades.py contra a API de localidades do IBGE.

Para cada município, confere se o geocode existe e se nome/UF batem com o cadastro oficial.
Imprime um relatório (OK / divergência) e sai com código != 0 se houver divergência.

Uso:  python validar_geocodes.py
Fonte: https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{geocode}
"""
import gzip
import json
import sys
import time
import unicodedata
import urllib.request

from cidades import CIDADES
import _log

log = _log.configurar("dengue.geocodes")
IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{}"


def _norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def consultar(geocode, tentativas=3):
    url = IBGE.format(geocode)
    if not url.lower().startswith("https://"):        # guarda: só HTTPS (bloqueia file://, etc.)
        raise ValueError(f"URL não-HTTPS bloqueada: {url}")
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dengue-webapp/1.0",
                                                       "Accept-Encoding": "identity"})
            # URL é constante HTTPS (IBGE), já validada pela guarda acima
            with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310
                bruto = r.read()
            if bruto[:2] == b"\x1f\x8b":            # resposta gzip -> descomprime
                bruto = gzip.decompress(bruto)
            d = json.loads(bruto.decode("utf-8"))
            if not d:
                return None
            return {"nome": d["nome"],
                    "uf": d["microrregiao"]["mesorregiao"]["UF"]["sigla"]}
        except Exception as e:                       # noqa: BLE001
            if i == tentativas - 1:
                log.warning("geocode %s: erro de consulta (%s)", geocode, e)
            time.sleep(1.0 * (i + 1))
    return None


def main():
    divergencias = []
    for nome, uf, geocode, *_ in CIDADES:
        of = consultar(geocode)
        if of is None:
            divergencias.append((geocode, nome, uf, "não encontrado no IBGE"))
            print(f"  ✗ {geocode} {nome}/{uf}: não encontrado")
            continue
        nome_ok = _norm(of["nome"]) == _norm(nome)
        uf_ok = of["uf"] == uf
        if nome_ok and uf_ok:
            print(f"  ✓ {geocode} {nome}/{uf}")
        else:
            msg = f"IBGE diz {of['nome']}/{of['uf']}"
            divergencias.append((geocode, nome, uf, msg))
            print(f"  ✗ {geocode} {nome}/{uf}: {msg}")

    print(f"\n{len(CIDADES) - len(divergencias)}/{len(CIDADES)} geocodes OK.")
    if divergencias:
        log.error("%d divergência(s): %s", len(divergencias), divergencias)
        sys.exit(1)
    print("Todos os geocodes conferem com o IBGE.")


if __name__ == "__main__":
    main()
