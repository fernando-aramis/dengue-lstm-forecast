# -*- coding: utf-8 -*-
"""
Dataset "atual" (Fase 1.8): busca server-side, em segundo plano, o último run publicado na branch `data`
e o expõe como um `dados.Conjunto`, sem nunca bloquear requisições nem o `/health`.

Regras de segurança/robustez (ver plano 21 §5.2):
- NUNCA roda no import (os testes importam `app` sem disparar rede); a thread daemon é iniciada por
  worker, de forma preguiçosa (`iniciar()`), ou por `post_worker_init` em `gunicorn.conf.py`.
- URL base fixa na allowlist; `DADOS_ATUAIS_URL` só vale se o host estiver nela. HTTP em loopback só
  com `DADOS_ATUAIS_TESTE=1`. Sem redirecionamentos. Timeout 5 s; teto de 2 MB por arquivo.
- `latest.json` aponta o run imutável; os arquivos têm o SHA-256 conferido (evita mistura de execuções;
  é consistência, não autenticidade: o hash vem da mesma origem — a confiança é no repositório + TLS).
- Fetcher injetável: testes não fazem rede real.

Estados: carregando | disponivel | defasado | indisponivel (com motivo curto).
"""
import hashlib
import io
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

import pandas as pd

import dados

BASE_PADRAO = "https://raw.githubusercontent.com/fernando-aramis/dengue-lstm-forecast/data/"
HOSTS_PERMITIDOS = {"raw.githubusercontent.com"}
PREFIXO_PERMITIDO = "/fernando-aramis/dengue-lstm-forecast/"   # só este repositório, não qualquer um do host
LIMITE_BYTES = 2 * 1024 * 1024
TIMEOUT_S = 5
BACKOFF_S = (0, 15, 60, 300)
RECHECAGEM_S = 6 * 3600
ARQUIVOS = ("previsoes.csv", "historico.csv", "_meta.json")
OPCIONAIS = ("limite_treino.csv", "previsoes_anterior.csv", "desempenho.json")      # só são buscados se o ponteiro lista o hash; ausente/divergente só desliga o recurso (o run segue)
_RE_RUN = re.compile(r"^[0-9]{6}-[0-9a-f]{7}$")

CARREGANDO, DISPONIVEL, DEFASADO, INDISPONIVEL = "carregando", "disponivel", "defasado", "indisponivel"


class ErroAtual(Exception):
    """Falha esperada e tratada: vira estado `indisponivel` com `str(e)` como motivo curto."""


# ---- configuração e rede ---------------------------------------------------------------------
def habilitado():
    return os.environ.get("DADOS_ATUAIS", "1") != "0"


def max_idade_semanas():
    try:
        return max(1, int(os.environ.get("ATUAL_MAX_IDADE_SEMANAS", "3")))
    except ValueError:
        return 3


def url_base():
    """Base das URLs; override por `DADOS_ATUAIS_URL` só se o host estiver na allowlist
    (ou loopback http com `DADOS_ATUAIS_TESTE=1`). Qualquer outra coisa cai na padrão."""
    cru = os.environ.get("DADOS_ATUAIS_URL", "").strip()
    if not cru:
        return BASE_PADRAO
    p = urllib.parse.urlsplit(cru)
    teste = os.environ.get("DADOS_ATUAIS_TESTE") == "1"
    if p.scheme == "https" and p.hostname in HOSTS_PERMITIDOS and p.path.startswith(PREFIXO_PERMITIDO):
        pass
    elif teste and p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost", "::1"):
        pass
    else:
        return BASE_PADRAO
    return cru if cru.endswith("/") else cru + "/"


class _SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):   # noqa: D401 — recusa qualquer salto
        return None


def fetch_http(url, etag=None):
    """Fetcher real → (status, corpo|None, etag|None). 304 → (304, None, etag).
    Levanta ErroAtual em HTTP != 200/304, rede, timeout ou corpo acima do teto."""
    req = urllib.request.Request(url, headers={"User-Agent": "dengue-painel/atual"})
    if etag:
        req.add_header("If-None-Match", etag)
    opener = urllib.request.build_opener(_SemRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT_S) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            novo = r.headers.get("ETag")
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return 304, None, etag
        raise ErroAtual(f"HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErroAtual("rede indisponível") from e
    if len(corpo) > LIMITE_BYTES:
        raise ErroAtual("arquivo acima do limite")
    return 200, corpo, novo


# ---- um ciclo de busca + validação -----------------------------------------------------------
def _json(corpo, o_que):
    try:
        v = json.loads(corpo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ErroAtual(f"{o_que} inválido") from None
    if not isinstance(v, dict):
        raise ErroAtual(f"{o_que} inválido")
    return v


def buscar(base, fetcher, etag=None):
    """Lê latest.json e os arquivos do run apontado (hash conferido).
    → (None, etag) se 304; senão ((prev_df, hist_df, meta, run, limite_df|None, anterior_df|None, desempenho_dict|None), etag)."""
    st, corpo, novo = fetcher(base + "latest.json", etag)
    if st == 304:
        return None, novo
    if corpo is None:
        raise ErroAtual("latest.json ausente")
    ptr = _json(corpo, "latest.json")
    run = ptr.get("run")
    if not isinstance(run, str) or not _RE_RUN.match(run):
        raise ErroAtual("latest.json sem run válido")
    hashes = ptr.get("sha256")
    if not isinstance(hashes, dict):
        raise ErroAtual("latest.json sem hashes")
    brutos = {}
    for nome in ARQUIVOS:
        esperado = hashes.get(nome)
        if not isinstance(esperado, str):
            raise ErroAtual(f"hash de {nome} ausente")
        _, dados_, _ = fetcher(f"{base}runs/{run}/{nome}", None)
        if dados_ is None:
            raise ErroAtual(f"{nome} ausente")
        if hashlib.sha256(dados_).hexdigest() != esperado.lower():
            raise ErroAtual(f"hash de {nome} não confere")
        brutos[nome] = dados_
    for nome in OPCIONAIS:
        esperado = hashes.get(nome)
        if esperado is None:
            continue
        try:
            _, dados_, _ = fetcher(f"{base}runs/{run}/{nome}", None)
        except ErroAtual:
            dados_ = None                     # opcional: ausente/erro de rede = recurso desligado, o run segue
        if isinstance(esperado, str) and dados_ is not None and hashlib.sha256(dados_).hexdigest() == esperado.lower():
            brutos[nome] = dados_             # hash divergente também só desliga o recurso (afeta só o aviso)
    meta = _json(brutos["_meta.json"], "_meta.json")
    try:
        prev = pd.read_csv(io.BytesIO(brutos["previsoes.csv"]), parse_dates=["data_origem", "data_prev"])
        hist = pd.read_csv(io.BytesIO(brutos["historico.csv"]), parse_dates=["data"])
    except (ValueError, KeyError, pd.errors.ParserError):
        raise ErroAtual("CSV inválido") from None
    lim = None
    if "limite_treino.csv" in brutos:
        try:
            lim = pd.read_csv(io.BytesIO(brutos["limite_treino.csv"]), dtype={"geo_id": str})
        except (ValueError, pd.errors.ParserError):
            lim = None            # opcional: ilegível = recurso desligado, não derruba o run
    ant = None
    if "previsoes_anterior.csv" in brutos:
        try:
            ant = pd.read_csv(io.BytesIO(brutos["previsoes_anterior.csv"]), parse_dates=["data_origem", "data_prev"])
        except (ValueError, KeyError, pd.errors.ParserError):
            ant = None            # opcional: ilegível = "o que mudou" oculto, não derruba o run
    desemp = None
    if "desempenho.json" in brutos:
        try:
            desemp = json.loads(brutos["desempenho.json"])
        except (ValueError, UnicodeDecodeError):
            desemp = None         # opcional: ilegível = desempenho oculto (validar_desempenho filtra o resto)
    return (prev, hist, meta, run, lim, ant, desemp), novo


def montar(prev, hist, meta, original, lim=None, ant=None, desemp=None):
    """Valida e constrói o Conjunto atual. Levanta ErroAtual com motivo curto."""
    try:
        dados.validar(prev, hist)
        c = dados.carregar((prev, hist, meta, lim, ant, desemp))
    except RuntimeError as e:
        raise ErroAtual("dados inválidos: " + str(e).split(": ", 1)[-1][:80]) from None
    origem_meta = meta.get("se_origem")      # no _meta, `se_origem` é a data de origem (AAAA-MM-DD)
    if origem_meta is not None and str(origem_meta)[:10] != c.data_origem:
        raise ErroAtual("se_origem do _meta diverge dos dados")
    if c.data_origem < original.data_origem:
        raise ErroAtual("anterior ao original")
    return c


def idade_semanas(c, hoje=None):
    hoje = hoje or date.today()
    return (hoje - date.fromisoformat(c.data_origem)).days / 7


# ---- estado do processo ----------------------------------------------------------------------
class Atual:
    """Carrega/atualiza o dataset atual. `tentar()` é síncrono (testável); a thread só o repete."""

    def __init__(self, fetcher=fetch_http, original=None, hoje=None, dormir=None):
        self._fetch = fetcher
        self._original = original or dados.ORIGINAL
        self._hoje = hoje
        self._dormir = dormir
        self._lock = threading.Lock()
        self._etag = None
        self._c = None
        self._motivo = None
        self._run = None
        self._coletado = None
        self._estado = CARREGANDO if habilitado() else INDISPONIVEL
        if not habilitado():
            self._motivo = "desligado"
        self._thread = None
        self._pid = None

    # leitura -------------------------------------------------------------------------------
    def estado(self):
        with self._lock:
            est, c = self._estado, self._c
            if est == DISPONIVEL and c is not None and idade_semanas(c, self._hoje) > max_idade_semanas():
                est = DEFASADO
            return {"estado": est, "motivo": self._motivo, "run": self._run,
                    "se_origem": c.se_origem if c else None, "data_origem": c.data_origem if c else None,
                    "coletado_em": self._coletado}

    def conjunto(self):
        """Conjunto utilizável (disponivel ou defasado) ou None."""
        with self._lock:
            return self._c if self._estado in (DISPONIVEL, DEFASADO) else None

    # escrita -------------------------------------------------------------------------------
    def tentar(self):
        """Uma tentativa. True se terminou sem erro (inclui 304). Troca atômica sob lock."""
        if not habilitado():
            return True
        try:
            res, novo_etag = buscar(url_base(), self._fetch, self._etag)
            if res is None:           # 304: nada mudou
                self._etag = novo_etag
                with self._lock:
                    if self._c is None:
                        self._estado, self._motivo = INDISPONIVEL, "sem dados"
                return True
            prev, hist, meta, run, lim, ant, desemp = res
            c = montar(prev, hist, meta, self._original, lim, ant, desemp)
        except Exception as e:     # noqa: BLE001 — nada pode matar a thread; só ErroAtual tem motivo exibível
            motivo = str(e) if isinstance(e, ErroAtual) else "erro inesperado"
            with self._lock:
                if self._c is None:           # mantém o último bom, se houver
                    self._estado, self._motivo = INDISPONIVEL, motivo
            return False
        self._etag = novo_etag     # só após validar: um run rejeitado é reavaliado no próximo ciclo
        with self._lock:
            self._c, self._run, self._estado, self._motivo = c, run, DISPONIVEL, None
            self._coletado = meta.get("coletado_em")
        return True

    def _laco(self):
        dormir = self._dormir or time.sleep
        falhas = 0
        while True:
            if self.tentar():
                falhas, espera = 0, RECHECAGEM_S
            else:
                falhas += 1       # 1ª tentativa imediata; depois 15 s, 60 s, 5 min; então a cada 6 h
                espera = BACKOFF_S[falhas] if falhas < len(BACKOFF_S) else RECHECAGEM_S
            dormir(espera)

    def iniciar(self):
        """Idempotente e seguro a fork: inicia a thread daemon deste processo (nunca no import)."""
        if not habilitado():
            return False
        with self._lock:
            if self._thread is not None and self._pid == os.getpid() and self._thread.is_alive():
                return False
            self._pid = os.getpid()
            self._thread = threading.Thread(target=self._laco, name="atual", daemon=True)
            self._thread.start()
            return True


_GLOBAL = None
_GLOBAL_LOCK = threading.Lock()


def desempenho_vigente():
    """Fase 3.3: desempenho realizado a exibir, independente da fonte escolhida — o do `atual` carregado, senão o
    do original; None = recurso oculto. Sem rede."""
    c = global_atual().conjunto()
    return (c.desempenho if c is not None and c.desempenho else None) or dados.ORIGINAL.desempenho


def global_atual():
    """Instância única do processo (criada sob demanda, sem rede)."""
    global _GLOBAL
    with _GLOBAL_LOCK:
        if _GLOBAL is None:
            _GLOBAL = Atual()
        return _GLOBAL
