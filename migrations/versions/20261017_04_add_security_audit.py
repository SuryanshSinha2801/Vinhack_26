"""Add append-only security audit events.

Revision ID: 20261017_04
Revises: 20261017_03
Create Date: 2026-10-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261017_04"
down_revision: Union[str, None] = "20261017_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "security_audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_reference", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_audit_events_event_type"), "security_audit_events", ["event_type"])
    op.create_index(op.f("ix_security_audit_events_actor_user_id"), "security_audit_events", ["actor_user_id"])
    op.create_index(op.f("ix_security_audit_events_actor_reference"), "security_audit_events", ["actor_reference"])
    op.create_index(op.f("ix_security_audit_events_created_at"), "security_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_security_audit_events_created_at"), table_name="security_audit_events")
    op.drop_index(op.f("ix_security_audit_events_actor_reference"), table_name="security_audit_events")
    op.drop_index(op.f("ix_security_audit_events_actor_user_id"), table_name="security_audit_events")
    op.drop_index(op.f("ix_security_audit_events_event_type"), table_name="security_audit_events")
    op.drop_table("security_audit_events")
