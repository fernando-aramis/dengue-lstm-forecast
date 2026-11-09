# -*- coding: utf-8 -*-
"""
Simplifica a geometria da malha estadual (offline, uma vez) para reduzir o payload do mapa.

O peso do geojson é o nº de vértices (~58 mil), não a precisão decimal — então arredondar não
adianta; aqui aplica-se Douglas-Peucker (shapely) preservando topologia e as propriedades
`sigla`/`name`. Gera backup do original e sobrescreve data/br_uf.geojson com a versão enxuta.

Uso:  python simplificar_geojson.py            (tolerância padrão 0.02°)
      TOLERANCIA=0.03 python simplificar_geojson.py
Requer shapely (ver pipeline/requirements.txt). Não entra na imagem de serving.
"""
import json
import os

from shapely.geometry import shape, mapping

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "..", "data")
ORIG = os.path.join(DATA, "br_uf.geojson")
BACKUP = os.path.join(DATA, "br_uf.full.geojson")
TOLERANCIA = float(os.environ.get("TOLERANCIA", "0.02"))   # graus (~2 km); mapa é nacional


def _n_vertices(geom):
    tot = 0

    def cnt(o):
        nonlocal tot
        if isinstance(o, (list, tuple)):
            if o and isinstance(o[0], (int, float)):
                tot += 1
            else:
                for x in o:
                    cnt(x)
    cnt(geom["coordinates"])
    return tot


def main():
    # idempotente: simplifica SEMPRE a partir do original pristino (backup), nunca do já reduzido
    fonte = BACKUP if os.path.exists(BACKUP) else ORIG
    with open(fonte, encoding="utf-8") as f:
        g = json.load(f)
    if not os.path.exists(BACKUP):
        with open(BACKUP, "w", encoding="utf-8") as f:
            json.dump(g, f, ensure_ascii=False)
        print(f"Backup do original -> {os.path.basename(BACKUP)}")

    v_antes = sum(_n_vertices(ft["geometry"]) for ft in g["features"])
    invalidas = 0
    for ft in g["features"]:
        geom = shape(ft["geometry"]).simplify(TOLERANCIA, preserve_topology=True)
        if not geom.is_valid:                 # repara auto-interseções da simplificação
            geom = geom.buffer(0)
            invalidas += 1
        ft["geometry"] = mapping(geom)
        # mantém só as propriedades usadas pelo app
        ft["properties"] = {"sigla": ft["properties"]["sigla"], "name": ft["properties"]["name"]}
    v_depois = sum(_n_vertices(ft["geometry"]) for ft in g["features"])
    if not all(shape(ft["geometry"]).is_valid for ft in g["features"]):
        raise ValueError("geometria inválida após reparo")

    saida = json.dumps(g, ensure_ascii=False, separators=(",", ":"))
    with open(ORIG, "w", encoding="utf-8") as f:
        f.write(saida)

    if len({ft["properties"]["sigla"] for ft in g["features"]}) != 27:
        raise ValueError("perdeu UFs!")
    tam_kb = round(len(saida.encode("utf-8")) / 1024)
    tam_orig = round(os.path.getsize(BACKUP) / 1024)
    print(f"Tolerância {TOLERANCIA}° · vértices {v_antes} -> {v_depois} "
          f"({100 * (1 - v_depois / v_antes):.0f}% menos) · {invalidas} geometria(s) reparada(s)")
    print(f"Tamanho {tam_orig} KB -> {tam_kb} KB · 27 UFs preservadas (sigla+name)")


if __name__ == "__main__":
    main()
