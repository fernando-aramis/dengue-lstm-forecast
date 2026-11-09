# -*- coding: utf-8 -*-
"""
EDA e preparação dos dados, replicando as etapas documentadas na planilha do projeto
(abas log_de_limpeza, regras_variaveis, EDA, parametros de IAGA04_Fernando_Dengue_Curitiba.xlsx).

Entrada: série semanal de uma cidade (de infodengue.buscar_cidade).
Saída de `preparar`: DataFrame pronto para o modelo + dicionário de parâmetros (mín/máx de treino).

Decisões herdadas do estudo:
  • Alvo e entrada = log(1 + casos)  -> estabiliza a assimetria (passo 1 de regras_variaveis).
  • Normalização Min-Max com mín/máx SÓ do treino, para não vazar o teste (passo 16 do log).
  • Semana do ano em seno/cosseno, período 52,18 (passo 1/2 de regras_variaveis).
  • Zeros e outliers (acima de Q3+1,5·IQR) são MANTIDOS: são reais (passos 8 e 9 do log).
  • Semanas recentes ainda em notificação são sinalizadas (passo 7 do log). Em produção usamos
    o nowcast (casos_est), que corrige o atraso, então elas são mantidas e só marcadas.
Diferença de fonte: a alertcity não traz precipitação; o modelo de produção é o univariado
(só casos), que foi o melhor no estudo — logo isso não afeta o modelo, só limita a EDA de clima.
"""
import numpy as np
import pandas as pd

PERIODO_SAZONAL = 52.18
N_PRELIMINAR = 3          # semanas finais marcadas como "em revisão" (atraso de notificação)


# ---------------------------------------------------------------- EDA
def eda(df, campo_casos="casos"):
    """Reproduz as estatísticas da aba EDA: assimetria antes/depois do log, perfil sazonal,
    zeros, limite IQR de outliers e correlação dos casos com o clima defasado."""
    s = df.copy()
    s["casos"] = s[campo_casos].clip(lower=0)
    s["log1p_casos"] = np.log1p(s["casos"])
    s["semana_epi"] = (s["epiweek"] % 100).astype(int)

    q1, q3 = s["casos"].quantile([0.25, 0.75])
    iqr = q3 - q1
    limite_iqr = q3 + 1.5 * iqr

    # correlação log(1+casos) × clima defasado (0..12 semanas), como na Figura 1c do artigo
    lags = {}
    for var in ("temp_med", "rel_humid_med"):
        if var in s.columns and s[var].notna().sum() > 30:
            cors = {h: s["log1p_casos"].corr(s[var].shift(h)) for h in range(0, 13)}
            melhor = max(cors, key=lambda h: abs(cors[h]))
            lags[var] = {"melhor_lag": melhor, "corr": round(cors[melhor], 3),
                         "por_lag": {h: round(c, 3) for h, c in cors.items()}}

    return {
        "n_semanas": len(s),
        "periodo": (s["date"].min().date().isoformat(), s["date"].max().date().isoformat()),
        "descritivas": {
            "casos": _desc(s["casos"]),
            "log1p_casos": _desc(s["log1p_casos"]),
        },
        "assimetria_casos": round(s["casos"].skew(), 2),
        "assimetria_log1p": round(s["log1p_casos"].skew(), 2),
        "semanas_zero": int((s["casos"] == 0).sum()),
        "limite_iqr": round(limite_iqr, 1),
        "semanas_acima_iqr": int((s["casos"] > limite_iqr).sum()),
        "pico_semana_epi": int(s.groupby("semana_epi")["casos"].mean().idxmax()),
        "corr_clima_defasado": lags,
    }


def _desc(x):
    return {"media": round(x.mean(), 2), "mediana": round(x.median(), 2), "desvio": round(x.std(), 2)}


# ---------------------------------------------------------------- preparação
def preparar(df, campo_casos="casos_est", semanas_validacao=52):
    """Monta o DataFrame pronto para o modelo e os parâmetros de normalização.

    campo_casos='casos_est' usa o nowcast (corrige atraso) — recomendado para previsão ao vivo.
    Use 'casos' para reproduzir exatamente o notificado do estudo.
    semanas_validacao: tamanho da cauda de validação, cujo mín/máx NÃO entram na normalização.
    """
    s = df.copy().sort_values("date").reset_index(drop=True)

    # passos 8/9: casos como inteiro não-negativo; zeros e outliers mantidos
    s["casos"] = s[campo_casos].clip(lower=0).round().astype(int)

    # passo 10/11: unicidade por semana epidemiológica (agrega eventuais repetidas pela média)
    s = s.groupby("epiweek", as_index=False).agg({
        "date": "first", "casos": "mean",
        **{c: "mean" for c in ("temp_med", "rel_humid_med") if c in s.columns},
    }).sort_values("date").reset_index(drop=True)
    s["casos"] = s["casos"].round().astype(int)

    # passo 7: sinaliza as semanas finais ainda em notificação (mantidas, pois usamos nowcast)
    s["semana_incompleta"] = 0
    s.loc[s.index >= len(s) - N_PRELIMINAR, "semana_incompleta"] = 1

    # engenharia de variáveis (regras_variaveis)
    s["log1p_casos"] = np.log1p(s["casos"])                      # ln(1+casos)
    s["semana_epi"] = (s["epiweek"] % 100).astype(int)
    s["ano_epi"] = (s["epiweek"] // 100).astype(int)
    ang = 2 * np.pi * s["semana_epi"] / PERIODO_SAZONAL
    s["sin_semana"] = np.sin(ang)
    s["cos_semana"] = np.cos(ang)

    # passo 16: normalização Min-Max com parâmetros SÓ do treino (sem a cauda de validação)
    corte = max(1, len(s) - semanas_validacao)
    lo = float(s["log1p_casos"].iloc[:corte].min())
    hi = float(s["log1p_casos"].iloc[:corte].max())
    s["log1p_casos_norm"] = (s["log1p_casos"] - lo) / (hi - lo) if hi > lo else 0.0

    params = {"log1p_min_treino": lo, "log1p_max_treino": hi,
              "campo_casos": campo_casos, "corte_treino": corte}
    return s, params


def para_casos(y_norm, params):
    """Inverte normalização + log1p: volta para casos reais (não-negativos)."""
    lo, hi = params["log1p_min_treino"], params["log1p_max_treino"]
    return np.clip(np.expm1(np.asarray(y_norm) * (hi - lo) + lo), 0, None)


if __name__ == "__main__":
    from infodengue import buscar_cidade
    d = buscar_cidade(4106902, ey_start=2010)
    import json
    print("=== EDA Curitiba (dados ao vivo) ===")
    print(json.dumps({k: v for k, v in eda(d).items() if k != "corr_clima_defasado"},
                     ensure_ascii=False, indent=2))
    e = eda(d)
    for var, info in e["corr_clima_defasado"].items():
        print(f"  {var}: melhor lag = {info['melhor_lag']} sem, corr = {info['corr']}")
    s, p = preparar(d)
    print("\n=== preparado ===")
    print("linhas:", len(s), "| norm min/max treino:",
          round(p["log1p_min_treino"], 3), round(p["log1p_max_treino"], 3))
    print("máx normalizado (geral):", round(s["log1p_casos_norm"].max(), 3))
    print(s[["date", "casos", "log1p_casos", "sin_semana", "log1p_casos_norm", "semana_incompleta"]].tail(5).to_string(index=False))
