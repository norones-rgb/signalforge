"""add oauth states and token metadata

Revision ID: 0003_oauth_states
Revises: 0002_schedule_backoff
Create Date: 2026-02-07 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_oauth_states"
down_revision = "0002_schedule_backoff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("x_accounts", sa.Column("oauth_token_type", sa.String(length=50), nullable=True))
    op.add_column("x_accounts", sa.Column("oauth_scopes", sa.Text(), nullable=True))

    op.create_table(
        "oauth_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(length=32), server_default="x", nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("code_verifier", sa.String(length=255), nullable=False),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("state", name="uq_oauth_states_state"),
    )


def downgrade() -> None:
    op.drop_table("oauth_states")
    op.drop_column("x_accounts", "oauth_scopes")
    op.drop_column("x_accounts", "oauth_token_type")
