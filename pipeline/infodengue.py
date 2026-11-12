# -*- coding: utf-8 -*-
"""
Coleta de dados reais do InfoDengue (API alertcity), por município.

Fonte equivalente à da Sprint 2024 usada no estudo (SINAN via InfoDengue). A API pública
devolve a série semanal de casos prováveis e o clima disponível (temperatura e umidade).

NOTA sobre precipitação: a alertcity NÃO traz precip_tot (que no estudo veio do ERA5/Mosqlimate).
Como o estudo concluiu que o clima piorou o modelo (sobreajuste) e a versão univariada (só casos)
foi a melhor, o pipeline de produção usa SÓ CASOS — então a ausência de precip não é limitante.
Temperatura e umidade são trazidas apenas para a EDA.
"""
import io
import os
import time
import urllib.request

import pandas as pd

import _log

BASE = "https://info.dengue.mat.br/api/alertcity"
COLUNAS_MIN = {"date", "epiweek", "casos", "casos_est"}   # contrato mínimo esperado da API
log = _log.configurar("dengue.infodengue")

# Timeout + cache (WS9): permite paralelizar a coleta sem estourar o rate limit da API e acelera
# re-runs. Cache por geocode, fresco por ~1 dia (os dados do InfoDengue são semanais). Desligável
# por env (INFODENGUE_CACHE=0). O diretório .cache/ fica sob pipeline/ (já fora da imagem de serving).
_AQUI = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = int(os.environ.get("INFODENGUE_TIMEOUT", "30"))            # era 60: falha mais rápido
CACHE_ON = os.environ.get("INFODENGUE_CACHE", "1") != "0"
CACHE_DIR = os.environ.get("INFODENGUE_CACHE_DIR", os.path.join(_AQUI, ".cache", "infodengue"))
CACHE_TTL_H = float(os.environ.get("INFODENGUE_CACHE_TTL_H", "18"))  # ~mesmo dia


def _cache_path(geocode, disease, ey_start, ey_end):
    return os.path.join(CACHE_DIR, f"{disease}_{geocode}_{ey_start}_{ey_end}.csv")


def _cache_fresca(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 3600 < CACHE_TTL_H
    except OSError:
        return False


def buscar_cidade(geocode, ey_start=2015, ey_end=None, disease="dengue", tentativas=3, pausa=1.5):
    """Baixa a série semanal de um município. Retorna DataFrame ordenado por data.

    Colunas devolvidas: date (domingo da SE), epiweek (YYYYWW), casos (prováveis notificados),
    casos_est (nowcast), temp_med, rel_humid_med, pop.
    """
    if ey_end is None:
        ey_end = pd.Timestamp.today().year
    url = (f"{BASE}?geocode={geocode}&disease={disease}&format=csv"
           f"&ew_start=1&ew_end=53&ey_start={ey_start}&ey_end={ey_end}")
    if not url.lower().startswith("https://"):        # guarda: só HTTPS (bloqueia file://, etc.)
        raise ValueError(f"URL não-HTTPS bloqueada: {url}")

    cache = _cache_path(geocode, disease, ey_start, ey_end) if CACHE_ON else None
    if cache and _cache_fresca(cache):                # cache fresco → não bate na API (evita rate limit)
        try:
            with open(cache, encoding="utf-8") as fh:
                return _padronizar(pd.read_csv(io.StringIO(fh.read())))
        except Exception as e:                        # noqa: BLE001  (cache corrompido → rebaixa p/ rede)
            log.warning("cache inválido p/ %s (%s); buscando na API", geocode, e)

    erro = None
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dengue-webapp/1.0"})
            # URL é constante HTTPS (BASE), já validada pela guarda acima
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # nosec B310
                bruto = r.read().decode("utf-8", errors="replace")
            df = pd.read_csv(io.StringIO(bruto))
            if len(df) == 0:
                raise ValueError("resposta vazia")
            resultado = _padronizar(df)               # valida o schema ANTES de gravar o cache
            if cache:
                try:
                    os.makedirs(CACHE_DIR, exist_ok=True)
                    with open(cache, "w", encoding="utf-8") as fh:
                        fh.write(bruto)
                except OSError as e:
                    log.warning("não gravou cache p/ %s: %s", geocode, e)
            return resultado
        except Exception as e:                      # noqa: BLE001
            erro = e
            time.sleep(pausa * (i + 1))
    raise RuntimeError(f"Falha ao baixar geocode {geocode}: {erro}")


def _padronizar(df):
    df = df.rename(columns={
        "data_iniSE": "date", "SE": "epiweek",
        "tempmed": "temp_med", "umidmed": "rel_humid_med",
    })
    faltando = COLUNAS_MIN - set(df.columns)
    if faltando:                           # a API mudou o contrato -> falha clara (não silenciosa)
        log.error("schema inesperado da API: faltam %s; colunas recebidas: %s",
                  sorted(faltando), list(df.columns))
        raise ValueError(f"colunas ausentes na resposta da API: {sorted(faltando)}")
    df["date"] = pd.to_datetime(df["date"])
    cols = ["date", "epiweek", "casos", "casos_est", "temp_med", "rel_humid_med", "pop"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].sort_values("date").reset_index(drop=True)
    # tipos numéricos
    for c in df.columns:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


if __name__ == "__main__":
    d = buscar_cidade(4106902, ey_start=2023)       # Curitiba, teste rápido
    print(d.tail(8).to_string(index=False))
    print("linhas:", len(d), "| período:", d["date"].min().date(), "→", d["date"].max().date())
