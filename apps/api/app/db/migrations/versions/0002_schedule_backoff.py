"""add schedule backoff

Revision ID: 0002_schedule_backoff
Revises: 0001_initial
Create Date: 2026-02-06 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_schedule_backoff"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "schedule_queue",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("schedule_queue", "next_attempt_at")
