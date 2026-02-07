"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-06 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "x_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200)),
        sa.Column("handle", sa.String(length=100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("oauth_access_token_enc", sa.Text()),
        sa.Column("oauth_refresh_token_enc", sa.Text()),
        sa.Column("oauth_expires_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "workspace_id", "handle", name="uq_x_accounts_workspace_handle"
        ),
    )

    op.create_table(
        "account_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
        sa.Column("daily_post_min", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("daily_post_max", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column(
            "allowed_hours",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("min_spacing_hours", sa.Integer(), server_default=sa.text("2"), nullable=False),
        sa.Column("allow_links", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("link_post_ratio", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("thread_ratio", sa.Float(), server_default=sa.text("0.2"), nullable=False),
        sa.Column("max_thread_len", sa.Integer(), server_default=sa.text("5"), nullable=False),
        sa.Column(
            "format_weights",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "topic_weights",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column("type", sa.String(length=50), server_default="rss", nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_ingested_at", sa.DateTime(timezone=True)),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "url", name="uq_sources_workspace_url"),
    )

    op.create_table(
        "ideas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sources.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(length=500)),
        sa.Column("summary", sa.Text()),
        sa.Column("url", sa.String(length=2000)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("raw_content", sa.Text()),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="new", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("fingerprint", name="uq_ideas_fingerprint"),
    )
    op.create_index("ix_ideas_fingerprint", "ideas", ["fingerprint"])

    op.create_table(
        "drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="SET NULL"),
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("format", sa.String(length=100), server_default="tweet_single", nullable=False),
        sa.Column("is_thread", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("thread_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("score", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="draft", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("content_fingerprint", name="uq_drafts_content_fingerprint"),
    )
    op.create_index("ix_drafts_content_fingerprint", "drafts", ["content_fingerprint"])

    op.create_table(
        "schedule_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "draft_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drafts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="scheduled", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "draft_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drafts.id", ondelete="SET NULL"),
        ),
        sa.Column("x_post_id", sa.String(length=200), unique=True),
        sa.Column("x_post_url", sa.String(length=2048)),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("is_thread", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="posted", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "post_metrics_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("impressions", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("likes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reposts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("replies", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("bookmarks", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("clicks", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("post_id", "metric_date", name="uq_post_metrics_daily"),
    )

    op.create_table(
        "template_performance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("format", sa.String(length=100), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("impressions_avg", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("like_rate", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("repost_rate", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "x_account_id", "format", "metric_date", name="uq_template_performance"
        ),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "x_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "meta",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("template_performance")
    op.drop_table("post_metrics_daily")
    op.drop_table("posts")
    op.drop_table("schedule_queue")
    op.drop_index("ix_drafts_content_fingerprint", table_name="drafts")
    op.drop_table("drafts")
    op.drop_index("ix_ideas_fingerprint", table_name="ideas")
    op.drop_table("ideas")
    op.drop_table("sources")
    op.drop_table("account_settings")
    op.drop_table("x_accounts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("workspaces")
