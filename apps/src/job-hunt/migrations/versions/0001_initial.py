"""tabelas iniciais: companies, applications, interviews

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

STATUSES = "'interesse','aplicada','triagem','entrevista_tecnica','entrevista_final','proposta','recusada','sem_resposta','aceita'"
WORK_MODES = "'remoto','hibrido','presencial'"
KINDS = "'rh','tecnica','gestor','outra'"


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_sub", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("owner_sub", "name_key", name="uq_companies_owner_key"),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_sub", sa.Text(), nullable=False),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_key", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text()),
        sa.Column("source", sa.Text()),
        sa.Column("work_mode", sa.Text()),
        sa.Column("location", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="aplicada"),
        sa.Column("applied_at", sa.Date()),
        sa.Column("last_interaction_at", sa.Date()),
        sa.Column("next_followup_at", sa.Date()),
        sa.Column("contact", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("owner_sub", "company_id", "title_key", name="uq_applications_owner_company_title"),
        sa.CheckConstraint(f"status IN ({STATUSES})", name="ck_applications_status"),
        sa.CheckConstraint(f"work_mode IS NULL OR work_mode IN ({WORK_MODES})", name="ck_applications_work_mode"),
    )
    op.create_index("ix_applications_owner_status", "applications", ["owner_sub", "status"])
    op.create_index("ix_applications_owner_followup", "applications", ["owner_sub", "next_followup_at"])
    op.create_index("ix_applications_company", "applications", ["company_id"])
    op.create_table(
        "interviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("application_id", sa.Uuid(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_sub", sa.Text(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False, server_default="rh"),
        sa.Column("with_whom", sa.Text()),
        sa.Column("result", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(f"kind IN ({KINDS})", name="ck_interviews_kind"),
    )
    op.create_index("ix_interviews_owner_when", "interviews", ["owner_sub", "scheduled_at"])
    op.create_index("ix_interviews_application", "interviews", ["application_id"])


def downgrade() -> None:
    op.drop_table("interviews")
    op.drop_table("applications")
    op.drop_table("companies")
