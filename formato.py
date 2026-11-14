# -*- coding: utf-8 -*-
"""Formatação de números e datas por idioma (PT/EN/ES), sem dependência externa.

Centraliza o que antes estava espalhado: `fmt_int` nasceu em `i18n.py` e agora vive
aqui; `i18n` o re-exporta para não quebrar `from i18n import fmt_int`.

Regra de separadores:
  - pt/es: milhar '.'  decimal ','   (15.389  ·  1,16)
  - en:    milhar ','  decimal '.'   (15,389  ·  1.16)

Datas: pt/es = dd/mm (dia primeiro); en = mm/dd (mês primeiro). Nomes de mês nos 3 idiomas.
"""

NBSP = " "     # espaço inseparável (número + unidade)
ENDASH = "–"   # travessão curto, para intervalos
MINUS = "−"    # sinal de menos tipográfico (não o hífen-menos)

# (milhar, decimal) por idioma
_SEP = {"pt": (".", ","), "es": (".", ","), "en": (",", ".")}

_MESES = {
    "pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
}


def _lang(lang):
    return lang if lang in _SEP else "pt"


def _remap(s, lang):
    """Remapeia a saída padrão do Python (',' milhar, '.' decimal) para o idioma."""
    mil, dec = _SEP[_lang(lang)]
    return s.replace(",", "\x00").replace(".", dec).replace("\x00", mil)


def fmt_int(v, lang="pt"):
    """Inteiro com separador de milhar por idioma: 5291 -> '5.291' (pt/es) / '5,291' (en)."""
    return _remap(f"{int(round(v)):,}", lang)


def fmt_dec(v, lang="pt", casas=2):
    """Decimal por idioma: 1.16 -> '1,16' (pt/es) / '1.16' (en)."""
    return _remap(f"{float(v):,.{casas}f}", lang)


def fmt_pct(v, lang="pt", casas=0, sinal=False):
    """Percentagem a partir de uma fração: -0.14 -> '−14%'. `v` é razão (0.14 = 14%)."""
    num = fmt_dec(abs(v) * 100, lang, casas)
    pre = MINUS if v < 0 else ("+" if sinal and v > 0 else "")
    return f"{pre}{num}%"


def fmt_data(d, lang="pt", estilo="curto"):
    """Data por idioma. estilo: 'curto' dd/mm · 'ano' dd/mm/aaaa · 'mes' '12 nov'/'Nov 12'.
    pt/es põem o dia primeiro; en põe o mês primeiro."""
    L = _lang(lang)
    if estilo == "mes":
        mes = _MESES[L][d.month - 1]
        return f"{mes} {d.day}" if L == "en" else f"{d.day} {mes}"
    if estilo == "ano":
        return f"{d.month:02d}/{d.day:02d}/{d.year}" if L == "en" else f"{d.day:02d}/{d.month:02d}/{d.year}"
    # curto
    return f"{d.month:02d}/{d.day:02d}" if L == "en" else f"{d.day:02d}/{d.month:02d}"


def fmt_intervalo(a, b, lang="pt", fmt=fmt_int):
    """Intervalo 'a–b' com travessão curto (sem espaços): usado em horizontes/IC."""
    return f"{fmt(a, lang)}{ENDASH}{fmt(b, lang)}"


# separadores para o Plotly (layout.separators = "<decimal><milhar>")
_MESES_LONGOS = {
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
           "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
           "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
           "octubre", "noviembre", "diciembre"],
}
_DIAS = {
    "pt": ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"],
    "en": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "es": ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
}
_DIAS_CURTOS = {
    "pt": ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
    "en": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "es": ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
}


def plotly_locale(lang):
    """Locale do Plotly (meses/dias/data/separadores) para `dcc.Graph(config={"locale", "locales"})`.
    O Plotly do Dash não traz locales e a CSP proíbe CDN; o Plotly aceita locales INLINE, então os
    eixos de data saem em pt/en/es sem dependência nova (reusa _MESES — fonte única dos nomes)."""
    L = _lang(lang)
    mil, dec = _SEP[L]
    return {"dictionary": {}, "format": {
        "months": _MESES_LONGOS[L], "shortMonths": _MESES[L],
        "days": _DIAS[L], "shortDays": _DIAS_CURTOS[L],
        "date": "%m/%d/%Y" if L == "en" else "%d/%m/%Y", "decimal": dec, "thousands": mil}}


def plotly_hoverformat_data(lang):
    """Formato da data no cabeçalho do hover (dia-primeiro em pt/es, mês-primeiro em en)."""
    return "%m/%d/%Y" if _lang(lang) == "en" else "%d/%m/%Y"


def plotly_separators(lang):
    mil, dec = _SEP[_lang(lang)]
    return dec + mil
