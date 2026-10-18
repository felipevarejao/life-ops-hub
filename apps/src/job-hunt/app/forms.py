"""Leitura e validação dos formulários. Erro de validação = HTTP 400 com mensagem."""
import datetime as dt

from fastapi import HTTPException

from .domain import INTERVIEW_KINDS, STATUS_LABELS, TZ, WORK_MODES

WORK_MODE_KEYS = {k for k, _ in WORK_MODES}
KIND_KEYS = {k for k, _ in INTERVIEW_KINDS}


def _text(form, key: str, maxlen: int):
    value = (form.get(key) or "").strip()
    if len(value) > maxlen:
        raise HTTPException(400, "Um dos campos passou do tamanho máximo.")
    return value or None


def parse_date(value, label: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, f"Data inválida em {label}.")


def parse_datetime(value: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(value.strip()).replace(tzinfo=TZ)
    except ValueError:
        raise HTTPException(400, "Data e hora da entrevista inválidas.")


def read_application_form(form) -> dict:
    company = _text(form, "company", 200)
    title = _text(form, "title", 200)
    if not company or not title:
        raise HTTPException(400, "Empresa e vaga são obrigatórias.")
    status = form.get("status") or "aplicada"
    if status not in STATUS_LABELS:
        raise HTTPException(400, "Status inválido.")
    work_mode = form.get("work_mode") or None
    if work_mode and work_mode not in WORK_MODE_KEYS:
        raise HTTPException(400, "Modalidade inválida.")
    return {
        "company": company, "title": title, "status": status, "work_mode": work_mode,
        "reference": _text(form, "reference", 500), "source": _text(form, "source", 120),
        "location": _text(form, "location", 120), "contact": _text(form, "contact", 300),
        "notes": _text(form, "notes", 5000),
        "applied_at": parse_date(form.get("applied_at"), "Aplicada em"),
        "next_followup_at": parse_date(form.get("next_followup_at"), "Próximo follow-up"),
    }


def read_interviews(form):
    """Campos iv_* se repetem, um conjunto por bloco; o servidor junta por posição."""
    keys = ("iv_id", "iv_when", "iv_kind", "iv_with", "iv_result", "iv_notes")
    cols = [form.getlist(k) for k in keys]
    n = len(cols[0])
    if any(len(c) != n for c in cols):
        raise HTTPException(400, "Formulário de entrevistas inconsistente.")
    rows = []
    for i in range(n):
        kind = cols[2][i] or "rh"
        if kind not in KIND_KEYS:
            raise HTTPException(400, "Tipo de entrevista inválido.")
        rows.append({
            "id": cols[0][i].strip(), "when": cols[1][i].strip(), "kind": kind,
            "with_whom": cols[3][i].strip()[:120] or None,
            "result": cols[4][i].strip()[:200] or None,
            "notes": cols[5][i].strip()[:5000] or None,
        })
    return rows, set(form.getlist("iv_remove"))
