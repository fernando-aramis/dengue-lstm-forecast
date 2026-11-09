# -*- coding: utf-8 -*-
"""
Gera dados de EXEMPLO (placeholder) para o app rodar ponta a ponta antes de existir
o modelo real por cidade.

Produz, em webapp/data/:
  - historico.csv  : últimas N semanas de casos observados (por cidade e por estado)
  - previsoes.csv  : previsão de 4 semanas + banda conformal de 90% (por cidade e por estado)

>>> ISTO NÃO É PREVISÃO REAL. <<<
Quando o modelo pooled estiver treinado, troque este script por `gerar_previsoes_reais.py`,
que grava os MESMOS arquivos no MESMO schema — o app não precisa mudar nada.

Usa só stdlib + numpy (roda sem pandas/tensorflow).
"""
import csv
import os
from datetime import date, timedelta

import numpy as np

from cidades import CIDADES, UF_NOME

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "..", "data")
os.makedirs(DATA, exist_ok=True)

N_HIST = 16          # semanas de histórico mostradas no gráfico
HORIZONTE = 4        # semanas previstas
RNG = np.random.default_rng(42)

# Semana epidemiológica de referência (segunda-feira mais recente, p/ alinhar com o InfoDengue).
hoje = date(2026, 11, 2)   # fixa p/ reprodutibilidade; no pipeline real: use a última epiweek disponível
DATA_ORIGEM = hoje


def serie_sazonal(pop, fase, pico_rel):
    """Série semanal sintética com formato sazonal de dengue (pico no verão do Hemisfério Sul)."""
    semanas = np.arange(N_HIST + HORIZONTE)
    # escala de magnitude ~ população
    base = max(3.0, pop / 1_000_000 * 40)
    sazonal = np.exp(pico_rel * np.sin(2 * np.pi * (semanas / 52.0) + fase))
    ruido = RNG.normal(1.0, 0.12, size=semanas.shape).clip(0.6, 1.5)
    valores = base * sazonal * ruido
    return valores


def nivel_alerta(casos, pop):
    """Nível simplificado por incidência semanal (casos/100 mil hab). Inspirado nas faixas do InfoDengue."""
    inc = casos / pop * 100_000
    if inc < 2.5:
        return "Verde"
    if inc < 10:
        return "Amarelo"
    if inc < 30:
        return "Laranja"
    return "Vermelho"


def linhas_cidade(nome, uf, geocode, lat, lon, pop):
    fase = RNG.uniform(-0.6, 0.6)
    pico_rel = RNG.uniform(0.7, 1.3)
    serie = serie_sazonal(pop, fase, pico_rel)
    hist = serie[:N_HIST]
    fut = serie[N_HIST:]

    hist_rows, prev_rows = [], []
    for i, v in enumerate(hist):
        d = DATA_ORIGEM - timedelta(weeks=(N_HIST - 1 - i))
        hist_rows.append(["municipio", geocode, uf, nome, lat, lon, d.isoformat(), round(float(v))])

    # Banda conformal cresce com o horizonte (imita o que você já observou: ~largura sobe com h).
    for h in range(1, HORIZONTE + 1):
        v = float(fut[h - 1])
        d = DATA_ORIGEM + timedelta(weeks=h)
        largura = v * (0.25 + 0.12 * h)          # placeholder; no real vem dos resíduos conformais
        inf = max(0.0, v - largura)
        sup = v + largura
        prev_rows.append(["municipio", geocode, uf, nome, lat, lon,
                          DATA_ORIGEM.isoformat(), h, d.isoformat(),
                          round(v), round(inf), round(sup), nivel_alerta(v, pop)])
    return hist_rows, prev_rows


def main():
    hist_rows, prev_rows = [], []
    por_uf = {}

    for nome, uf, geocode, lat, lon, pop in CIDADES:
        hr, pr = linhas_cidade(nome, uf, geocode, lat, lon, pop)
        hist_rows += hr
        prev_rows += pr
        por_uf.setdefault(uf, []).append((nome, geocode, lat, lon, pop, hr, pr))

    # ---- Fallback estadual: agrega as cidades cobertas de cada UF (soma de casos) ----
    for uf, cidades in por_uf.items():
        pop_uf = sum(c[4] for c in cidades)
        lat_uf = float(np.mean([c[2] for c in cidades]))
        lon_uf = float(np.mean([c[3] for c in cidades]))
        geo_uf = f"UF-{uf}"
        nome_uf = UF_NOME[uf]

        # histórico estadual = soma por data
        soma_hist = {}
        for c in cidades:
            for row in c[5]:
                soma_hist[row[6]] = soma_hist.get(row[6], 0) + row[7]
        for d, v in sorted(soma_hist.items()):
            hist_rows.append(["estado", geo_uf, uf, nome_uf, lat_uf, lon_uf, d, v])

        soma_prev = {}
        for c in cidades:
            for row in c[6]:
                h = row[7]
                acc = soma_prev.setdefault(h, {"data": row[8], "prev": 0, "inf": 0, "sup": 0})
                acc["prev"] += row[9]
                acc["inf"] += row[10]
                acc["sup"] += row[11]
        for h in sorted(soma_prev):
            a = soma_prev[h]
            prev_rows.append(["estado", geo_uf, uf, nome_uf, lat_uf, lon_uf,
                              DATA_ORIGEM.isoformat(), h, a["data"],
                              a["prev"], a["inf"], a["sup"], nivel_alerta(a["prev"], pop_uf)])

    with open(os.path.join(DATA, "historico.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nivel_geo", "geo_id", "uf", "nome", "lat", "lon", "data", "casos"])
        w.writerows(hist_rows)

    with open(os.path.join(DATA, "previsoes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nivel_geo", "geo_id", "uf", "nome", "lat", "lon",
                    "data_origem", "h", "data_prev", "prev", "inf", "sup", "nivel_alerta"])
        w.writerows(prev_rows)

    print(f"OK: {len(hist_rows)} linhas de histórico, {len(prev_rows)} linhas de previsão.")
    print("Arquivos em webapp/data/ (DADOS DE EXEMPLO — não é previsão real).")


if __name__ == "__main__":
    main()
