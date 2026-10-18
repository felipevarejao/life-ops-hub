"""Modelos do Job Hunt. Todo registro tem owner_sub (o X-authentik-uid do dono)."""
import datetime as dt
import uuid

from sqlalchemy import (CheckConstraint, Date, DateTime, ForeignKey, Index, Text,
                        UniqueConstraint, Uuid, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .domain import INTERVIEW_KINDS, STATUSES, WORK_MODES


def _in(column: str, pairs) -> str:
    return f"{column} IN ({', '.join(repr(k) for k, _ in pairs)})"


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (UniqueConstraint("owner_sub", "name_key", name="uq_companies_owner_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_sub: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_key: Mapped[str] = mapped_column(Text, nullable=False)  # normalize_name(name)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applications: Mapped[list["Application"]] = relationship(back_populates="company", passive_deletes="all")


class Application(Base):
    """Uma candidatura = uma vaga numa empresa. O título pertence a ela, não à empresa."""
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("owner_sub", "company_id", "title_key", name="uq_applications_owner_company_title"),
        CheckConstraint(_in("status", STATUSES), name="ck_applications_status"),
        CheckConstraint("work_mode IS NULL OR " + _in("work_mode", WORK_MODES), name="ck_applications_work_mode"),
        Index("ix_applications_owner_status", "owner_sub", "status"),
        Index("ix_applications_owner_followup", "owner_sub", "next_followup_at"),
        Index("ix_applications_company", "company_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_sub: Mapped[str] = mapped_column(Text, nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_key: Mapped[str] = mapped_column(Text, nullable=False)  # normalize_name(title)
    reference: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    work_mode: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="aplicada", server_default="aplicada")
    applied_at: Mapped[dt.date | None] = mapped_column(Date)
    last_interaction_at: Mapped[dt.date | None] = mapped_column(Date)
    next_followup_at: Mapped[dt.date | None] = mapped_column(Date)
    contact: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company: Mapped[Company] = relationship(back_populates="applications")
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Interview.scheduled_at")


class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint(_in("kind", INTERVIEW_KINDS), name="ck_interviews_kind"),
        Index("ix_interviews_owner_when", "owner_sub", "scheduled_at"),
        Index("ix_interviews_application", "application_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    owner_sub: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="rh", server_default="rh")
    with_whom: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="interviews")
