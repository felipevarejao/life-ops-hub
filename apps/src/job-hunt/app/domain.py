"""Listas fixas do domínio (chave interna, rótulo na tela)."""

STATUSES = [
    ("interesse", "Interesse"),
    ("aplicada", "Aplicada"),
    ("triagem", "Triagem"),
    ("entrevista_tecnica", "Entrevista técnica"),
    ("entrevista_final", "Entrevista final"),
    ("proposta", "Proposta"),
    ("recusada", "Recusada"),
    ("sem_resposta", "Sem resposta"),
    ("aceita", "Aceita"),
]
STATUS_LABELS = dict(STATUSES)

WORK_MODES = [("remoto", "Remoto"), ("hibrido", "Híbrido"), ("presencial", "Presencial")]
INTERVIEW_KINDS = [("rh", "RH"), ("tecnica", "Técnica"), ("gestor", "Gestor"), ("outra", "Outra")]


def reference_href(value):
    """Devolve um href seguro para o campo "link ou referência", ou None se for só texto.

    Só vira link se for http(s) ou começar com www., e sem espaços. Qualquer outra
    coisa (inclusive javascript:) é exibida como texto puro.
    """
    if not isinstance(value, str):
        return None
    v = value.strip()
    if not v or any(c.isspace() for c in v):
        return None
    low = v.lower()
    if low.startswith(("http://", "https://")):
        return v
    if low.startswith("www."):
        return "https://" + v
    return None


def normalize_name(value):
    """Chave de comparação: minúsculas, sem acento, espaços colapsados.

    "Banco  Inter", "banco inter" e "Banco Ínter" geram a mesma chave.
    """
    import re
    import unicodedata

    v = unicodedata.normalize("NFKD", value or "")
    v = "".join(c for c in v if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", v).strip().casefold()


import datetime as _dt
import os as _os
from zoneinfo import ZoneInfo as _ZoneInfo

TZ = _ZoneInfo(_os.environ.get("APP_TZ", "America/Sao_Paulo"))


def today() -> _dt.date:
    return _dt.datetime.now(TZ).date()
