# -*- coding: utf-8 -*-
"""
Modelo LSTM univariado (versão A do estudo) + intervalos por predição conformal adaptativa.
Mesma arquitetura do projeto original (IAGA04_Fernando_Dengue_LSTM.py), aplicada em modo de
PRODUÇÃO: treina em toda a série e prevê as 4 semanas seguintes à última observada.

Requer TensorFlow. Se não estiver instalado, use pip install tensorflow-cpu (ou rode no Colab).
"""
import numpy as np

from preparacao import para_casos

JANELA, HORIZONTE = 12, 4
SEED = 42
# teto do limite superior do intervalo, como múltiplo do pico histórico da série.
# Em surto fora da faixa de treino, prev_norm+q pode passar de 1 e o expm1 dispara;
# o teto evita que a banda superior quebre a escala do gráfico sem apagar a incerteza.
# ESPELHADO em dados.py (guarda defensiva no serving p/ CSVs já gravados). Mantenha os dois iguais.
TETO_FATOR = 3.0


def _tf():
    import tensorflow as tf
    from tensorflow import keras
    keras.utils.set_random_seed(SEED)
    return tf, keras


def _janelas(X, y, origens):
    """Para cada origem t: entrada = t-11..t ; alvo = t+1..t+4 (NaN quando ainda não existe)."""
    y = np.concatenate([y, np.full(HORIZONTE, np.nan)])
    Xw = np.stack([X[t - JANELA + 1:t + 1] for t in origens])
    yw = np.stack([y[t + 1:t + 1 + HORIZONTE] for t in origens])
    return Xw.astype("float32"), yw.astype("float32")


def _criar_modelo(n_features, keras, unidades=(64, 32)):
    from tensorflow.keras import layers
    m = keras.Sequential([layers.Input((JANELA, n_features))])
    for i, u in enumerate(unidades):
        m.add(layers.LSTM(u, return_sequences=i < len(unidades) - 1))
        m.add(layers.Dropout(0.2))
    m.add(layers.Dense(HORIZONTE))
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])
    return m


def treinar_prever(s, params, semanas_validacao=52, W_conformal=52, alfa=0.10,
                   epocas=500, paciencia=30, verbose=0):
    """Treina a LSTM A e devolve a previsão das próximas 4 semanas com intervalo de 90%.

    Retorna: lista de dicts [{h, data_prev, prev, inf, sup}] e métricas simples do ajuste.
    """
    _, keras = _tf()
    X = s[["log1p_casos_norm"]].values.astype("float32")
    y = s["log1p_casos_norm"].values.astype("float32")
    n = len(s)

    # origens com alvo conhecido: t+HORIZONTE <= n-1
    ult = n - 1 - HORIZONTE
    corte_val = ult - semanas_validacao
    orig_fit = np.arange(JANELA - 1, corte_val + 1)
    orig_val = np.arange(corte_val + 1, ult + 1)
    if len(orig_fit) < 20 or len(orig_val) < 4:                 # série curta: sem validação separada
        orig_fit = np.arange(JANELA - 1, ult + 1)
        orig_val = orig_fit[-min(8, len(orig_fit)):]

    Xf, yf = _janelas(X, y, orig_fit)
    Xv, yv = _janelas(X, y, orig_val)
    modelo = _criar_modelo(1, keras)
    hist = modelo.fit(Xf, yf, validation_data=(Xv, yv), epochs=epocas, batch_size=16,
                      verbose=verbose,
                      callbacks=[keras.callbacks.EarlyStopping(patience=paciencia,
                                                               restore_best_weights=True)])

    # previsão do futuro: janela terminando na última semana observada
    janela_final = X[n - JANELA:n][None, :, :]
    prev_norm = modelo.predict(janela_final, verbose=0)[0]       # (4,) em escala normalizada
    prev_casos = para_casos(prev_norm, params)

    # conformal adaptativo: resíduos (escala normalizada) das últimas W origens conhecidas, por h
    orig_recent = np.arange(max(JANELA - 1, ult - W_conformal + 1), ult + 1)
    Xr, yr = _janelas(X, y, orig_recent)
    pr = modelo.predict(Xr, verbose=0)
    resid = yr - pr                                              # (origens, 4)

    ult_data = s["date"].iloc[-1]
    teto = max(1.0, float(s["casos"].max())) * TETO_FATOR     # pico histórico × fator
    saida = []
    for h in range(1, HORIZONTE + 1):
        r = resid[:, h - 1]
        r = r[~np.isnan(r)]
        q = np.quantile(np.abs(r), 1 - alfa) if len(r) else 0.0
        p = max(0.0, float(prev_casos[h - 1]))
        inf = max(0.0, float(para_casos(prev_norm[h - 1] - q, params)))
        sup = float(para_casos(prev_norm[h - 1] + q, params))
        sup = max(p, min(sup, teto))                          # teto p/ não quebrar a escala
        saida.append({"h": h, "data_prev": (ult_data + np.timedelta64(7 * h, "D")),
                      "prev": p, "inf": min(inf, p), "sup": sup})
    meta = {"epocas": len(hist.history["loss"]), "data_origem": ult_data}
    return saida, meta
