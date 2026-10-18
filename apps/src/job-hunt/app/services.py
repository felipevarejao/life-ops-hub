"""Acesso a dados. TODA consulta filtra por owner_sub: um usuário nunca alcança dado de outro."""
import datetime as dt
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .domain import normalize_name
from .forms import parse_datetime
from .models import Application, Company, Interview

CLOSED = ("recusada", "sem_resposta", "aceita")


def list_company_names(db: Session, owner: str) -> list[str]:
    return list(db.scalars(select(Company.name).where(Company.owner_sub == owner).order_by(Company.name)))


def get_or_create_company(db: Session, owner: str, name: str) -> Company:
    key = normalize_name(name)
    company = db.scalar(select(Company).where(Company.owner_sub == owner, Company.name_key == key))
    if company is None:
        company = Company(owner_sub=owner, name=name.strip(), name_key=key)
        db.add(company)
        db.flush()
    return company


def get_application(db: Session, owner: str, app_id: uuid.UUID) -> Application | None:
    return db.scalar(
        select(Application).options(joinedload(Application.company))
        .where(Application.id == app_id, Application.owner_sub == owner))


def find_duplicate(db: Session, owner: str, company_id, title_key: str, exclude_id=None) -> Application | None:
    q = select(Application).where(Application.owner_sub == owner, Application.company_id == company_id,
                                  Application.title_key == title_key)
    if exclude_id is not None:
        q = q.where(Application.id != exclude_id)
    return db.scalar(q)


def other_applications(db: Session, owner: str, a: Application) -> list[Application]:
    return list(db.scalars(
        select(Application).where(Application.owner_sub == owner, Application.company_id == a.company_id,
                                  Application.id != a.id).order_by(Application.title)))


def apply_interviews(db: Session, owner: str, a: Application, rows: list[dict], remove: set[str]) -> bool:
    """Cria, atualiza e remove entrevistas da candidatura. Devolve True se algo mudou."""
    existing = {str(i.id): i for i in a.interviews}
    changed = False
    for r in rows:
        if r["id"]:
            iv = existing.get(r["id"])
            if iv is None or iv.owner_sub != owner:
                raise HTTPException(404)
            if r["id"] in remove:
                db.delete(iv)
                changed = True
                continue
            if r["when"]:
                when = parse_datetime(r["when"])
                if when != iv.scheduled_at:
                    iv.scheduled_at = when
                    changed = True
            for attr in ("kind", "with_whom", "result", "notes"):
                if getattr(iv, attr) != r[attr]:
                    setattr(iv, attr, r[attr])
                    changed = True
        elif r["when"]:
            db.add(Interview(application_id=a.id, owner_sub=owner, scheduled_at=parse_datetime(r["when"]),
                             kind=r["kind"], with_whom=r["with_whom"], result=r["result"], notes=r["notes"]))
            changed = True
    return changed
