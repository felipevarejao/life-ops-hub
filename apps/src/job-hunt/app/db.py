"""Conexão com o Postgres. A URL vem sempre de DATABASE_URL (nunca no código)."""
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL não definida")
    # Aceita a URI no formato que o CloudNativePG entrega (postgresql://...).
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(database_url(), pool_pre_ping=True)
    return _engine


def get_session():
    """Dependência do FastAPI: uma sessão por requisição."""
    with Session(get_engine()) as session:
        yield session
