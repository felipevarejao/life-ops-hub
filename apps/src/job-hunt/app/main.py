import datetime as dt
import os
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import services
from .auth import User, current_user, origin_ok
from .db import get_session
from .domain import (INTERVIEW_KINDS, STATUS_LABELS, STATUSES, TZ, WORK_MODES, normalize_name,
                     reference_href, today)
from .forms import read_application_form, read_interviews
from .models import Application, Company, Interview

BASE = Path(__file__).parent
HUB_URL = os.environ.get("HUB_URL", "https://personalhub.felipevarejao.dev.br")
KIND_LABELS = dict(INTERVIEW_KINDS)
WEEKDAYS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
NOTICES = {"criada": "Candidatura criada.", "salva": "Alterações salvas.", "repetida": "Esta vaga já estava cadastrada."}

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")  # autoescape ligado


def link(name: str, obj_id=None) -> str:
    if name == "detail":
        return f"/applications/{obj_id}"
    if name == "delete":
        return f"/applications/{obj_id}/delete"
    return {"hoje": "/", "pipeline": "/pipeline", "new": "/applications/new",
            "save": "/applications", "hub": HUB_URL}[name]


templates.env.filters["ref_href"] = reference_href
templates.env.globals.update(
    form_method="post", static_url=lambda p: f"/static/{p}", link=link, STATUSES=STATUSES,
    STATUS_LABELS=STATUS_LABELS, WORK_MODES=WORK_MODES, INTERVIEW_KINDS=INTERVIEW_KINDS)


@app.middleware("http")
async def protecoes(request: Request, call_next):
    if not origin_ok(request):
        return JSONResponse({"detail": "Origem não permitida"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'")
    return response


@app.exception_handler(StarletteHTTPException)
async def erros(request: Request, exc: StarletteHTTPException):
    if exc.status_code in (400, 404):
        try:
            user = current_user(request)
        except HTTPException:
            user = User(uid="", name="")
        msg = str(exc.detail) if exc.status_code == 400 else "Não encontrado."
        return templates.TemplateResponse(request, "error.html", {"user": user, "active": "", "msg": msg},
                                          status_code=exc.status_code)
    return await http_exception_handler(request, exc)


# ---------- utilidades ----------
def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(404)


def followup_label(d: dt.date, t: dt.date):
    n = (d - t).days
    if n < 0:
        return f"atrasado {-n} dia{'s' if -n != 1 else ''}", "late"
    if n == 0:
        return "hoje", "today"
    return f"em {n} dia{'s' if n != 1 else ''}", "soon"


def _view(a: Application) -> dict:
    return {"id": str(a.id), "company": a.company.name, "title": a.title, "status": a.status,
            "reference": a.reference, "source": a.source, "work_mode": a.work_mode, "location": a.location,
            "applied_at": a.applied_at, "last_interaction_at": a.last_interaction_at,
            "next_followup_at": a.next_followup_at, "contact": a.contact, "notes": a.notes}


def _form_page(request, user, db, a_view, interviews, others, notice):
    ctx = {"user": user, "active": "pipeline" if a_view else "new", "a": a_view, "interviews": interviews,
           "others": others, "notice": notice, "today": today().isoformat(),
           "companies": [{"name": n} for n in services.list_company_names(db, user.uid)]}
    return templates.TemplateResponse(request, "application.html", ctx)


# ---------- rotas ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def hoje(request: Request, user: User = Depends(current_user), db: Session = Depends(get_session)):
    owner, t = user.uid, today()
    now = dt.datetime.now(dt.timezone.utc)

    fu = db.scalars(
        select(Application).options(joinedload(Application.company))
        .where(Application.owner_sub == owner, Application.next_followup_at.is_not(None),
               Application.next_followup_at <= t + dt.timedelta(days=7),
               Application.status.notin_(services.CLOSED))
        .order_by(Application.next_followup_at)).all()
    followups = []
    for a in fu:
        label, tone = followup_label(a.next_followup_at, t)
        followups.append({"id": a.id, "company": a.company.name, "title": a.title, "label": label, "tone": tone})

    ivs = db.scalars(
        select(Interview).options(joinedload(Interview.application).joinedload(Application.company))
        .where(Interview.owner_sub == owner, Interview.scheduled_at >= now,
               Interview.scheduled_at <= now + dt.timedelta(days=7))
        .order_by(Interview.scheduled_at)).all()
    interviews = []
    for i in ivs:
        local = i.scheduled_at.astimezone(TZ)
        interviews.append({
            "id": i.application_id, "company": i.application.company.name, "title": i.application.title,
            "kind": KIND_LABELS.get(i.kind, i.kind), "with_whom": i.with_whom,
            "when": f"{WEEKDAYS[local.weekday()]} {local:%d/%m} {local:%H:%M}"})

    st = db.scalars(
        select(Application).options(joinedload(Application.company))
        .where(Application.owner_sub == owner, Application.status.in_(("aplicada", "triagem")),
               Application.applied_at.is_not(None), Application.applied_at <= t - dt.timedelta(days=10),
               or_(Application.last_interaction_at.is_(None),
                   Application.last_interaction_at <= Application.applied_at))
        .order_by(Application.applied_at)).all()
    stale = [{"id": a.id, "company": a.company.name, "title": a.title,
              "label": f"aplicada há {(t - a.applied_at).days} dias"} for a in st]

    ctx = {"user": user, "active": "hoje", "followups": followups, "interviews": interviews, "stale": stale}
    return templates.TemplateResponse(request, "hoje.html", ctx)


@app.get("/pipeline")
def pipeline(request: Request, q: str = "", status: str = "", user: User = Depends(current_user),
             db: Session = Depends(get_session)):
    q, t = q.strip()[:100], today()
    if status not in STATUS_LABELS:
        status = ""
    query = (select(Application).join(Application.company).options(contains_eager(Application.company))
             .where(Application.owner_sub == user.uid))
    if q:
        pat = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(or_(Application.title.ilike(pat, escape="\\"), Company.name.ilike(pat, escape="\\")))
    if status:
        query = query.where(Application.status == status)
    by_status: dict[str, list] = {}
    for a in db.scalars(query.order_by(Application.next_followup_at.asc().nulls_last(), Company.name)).all():
        nxt, tone = ("", "")
        if a.next_followup_at and a.status not in services.CLOSED:
            nxt, tone = followup_label(a.next_followup_at, t)
        by_status.setdefault(a.status, []).append(
            {"id": a.id, "company": a.company.name, "title": a.title, "next": nxt, "tone": tone})
    groups = [{"key": k, "label": label, "rows": by_status[k]} for k, label in STATUSES if k in by_status]
    ctx = {"user": user, "active": "pipeline", "q": q, "status": status, "groups": groups}
    return templates.TemplateResponse(request, "pipeline.html", ctx)


@app.get("/applications/new")
def new_form(request: Request, user: User = Depends(current_user), db: Session = Depends(get_session)):
    return _form_page(request, user, db, None, [], [], None)


@app.post("/applications")
async def create(request: Request, user: User = Depends(current_user), db: Session = Depends(get_session)):
    form = await request.form()
    d = read_application_form(form)
    rows, _ = read_interviews(form)
    owner = user.uid
    company = services.get_or_create_company(db, owner, d["company"])
    title_key = normalize_name(d["title"])
    dup = services.find_duplicate(db, owner, company.id, title_key)
    if dup is not None:
        db.commit()
        return RedirectResponse(f"/applications/{dup.id}?aviso=repetida", status_code=303)
    if d["next_followup_at"] is None and d["applied_at"]:
        d["next_followup_at"] = d["applied_at"] + dt.timedelta(days=7)
    a = Application(owner_sub=owner, company_id=company.id, title=d["title"], title_key=title_key,
                    status=d["status"], reference=d["reference"], source=d["source"], work_mode=d["work_mode"],
                    location=d["location"], contact=d["contact"], notes=d["notes"],
                    applied_at=d["applied_at"], next_followup_at=d["next_followup_at"])
    db.add(a)
    db.flush()
    if services.apply_interviews(db, owner, a, rows, set()):
        a.last_interaction_at = today()
    db.commit()
    return RedirectResponse(f"/applications/{a.id}?aviso=criada", status_code=303)


@app.get("/applications/{app_id}")
def detail(app_id: str, request: Request, aviso: str = "", user: User = Depends(current_user),
           db: Session = Depends(get_session)):
    a = services.get_application(db, user.uid, _uuid(app_id))
    if a is None:
        raise HTTPException(404)
    interviews = [{"id": str(i.id), "kind": i.kind, "with_whom": i.with_whom, "result": i.result,
                   "notes": i.notes, "when_input": i.scheduled_at.astimezone(TZ).strftime("%Y-%m-%dT%H:%M")}
                  for i in a.interviews]
    others = [{"id": str(o.id), "title": o.title, "status": o.status}
              for o in services.other_applications(db, user.uid, a)]
    return _form_page(request, user, db, _view(a), interviews, others, NOTICES.get(aviso))


@app.post("/applications/{app_id}")
async def update(app_id: str, request: Request, user: User = Depends(current_user),
                 db: Session = Depends(get_session)):
    owner = user.uid
    a = services.get_application(db, owner, _uuid(app_id))
    if a is None:
        raise HTTPException(404)
    form = await request.form()
    d = read_application_form(form)
    rows, remove = read_interviews(form)

    title_key = normalize_name(d["title"])
    company_id = a.company_id
    if normalize_name(d["company"]) != a.company.name_key:
        company_id = services.get_or_create_company(db, owner, d["company"]).id
    if (company_id != a.company_id or title_key != a.title_key) and \
            services.find_duplicate(db, owner, company_id, title_key, exclude_id=a.id):
        raise HTTPException(400, "Já existe essa vaga nessa empresa.")

    status_changed = d["status"] != a.status
    a.company_id, a.title, a.title_key, a.status = company_id, d["title"], title_key, d["status"]
    a.reference, a.source, a.work_mode, a.location = d["reference"], d["source"], d["work_mode"], d["location"]
    a.contact, a.notes = d["contact"], d["notes"]
    a.applied_at, a.next_followup_at = d["applied_at"], d["next_followup_at"]
    interviews_changed = services.apply_interviews(db, owner, a, rows, remove)
    if status_changed or interviews_changed:
        a.last_interaction_at = today()
    db.commit()
    return RedirectResponse(f"/applications/{a.id}?aviso=salva", status_code=303)


@app.post("/applications/{app_id}/delete")
async def delete(app_id: str, user: User = Depends(current_user), db: Session = Depends(get_session)):
    a = services.get_application(db, user.uid, _uuid(app_id))
    if a is None:
        raise HTTPException(404)
    db.delete(a)
    db.commit()
    return RedirectResponse("/pipeline", status_code=303)
