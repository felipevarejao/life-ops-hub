"""Identidade vinda do authentik (forward auth) e proteção contra CSRF.

O app NÃO trata senha nem login. O Traefik só entrega a requisição depois que o
authentik autenticou, e repassa quem é o usuário nestes headers.
"""
import os
from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import HTTPException, Request

ENV = os.environ.get("ENV", "prod")
DEV_USER_UID = os.environ.get("DEV_USER_UID", "")
DEV_USER_NAME = os.environ.get("DEV_USER_NAME", "Dev")


@dataclass(frozen=True)
class User:
    uid: str   # X-authentik-uid: identificador estável, é o "dono" dos registros
    name: str


def _utf8(value: str) -> str:
    # Headers chegam decodificados como latin-1; reconverte para UTF-8 (acentos).
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def current_user(request: Request) -> User:
    uid = request.headers.get("x-authentik-uid", "").strip()
    if uid:
        name = request.headers.get("x-authentik-name") or request.headers.get("x-authentik-username") or "Você"
        return User(uid=uid, name=_utf8(name).strip())
    # Exceção só para desenvolvimento local. Fora do ENV=dev ela não existe.
    if ENV == "dev" and DEV_USER_UID:
        return User(uid=DEV_USER_UID, name=DEV_USER_NAME)
    raise HTTPException(status_code=401, detail="Não autenticado")


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def origin_ok(request: Request) -> bool:
    """Requisições que alteram dados precisam vir do próprio host (anti-CSRF)."""
    if request.method in SAFE_METHODS:
        return True
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return False
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    return urlparse(source).netloc.lower() == host.lower()
