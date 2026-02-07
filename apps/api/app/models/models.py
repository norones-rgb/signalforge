from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    users: Mapped[list["User"]] = relationship(back_populates="workspace")
    accounts: Mapped[list["XAccount"]] = relationship(back_populates="workspace")
    sources: Mapped[list["Source"]] = relationship(back_populates="workspace")
    ideas: Mapped[list["Idea"]] = relationship(back_populates="workspace")
    drafts: Mapped[list["Draft"]] = relationship(back_populates="workspace")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="workspace")


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="users")


class XAccount(Base):
    __tablename__ = "x_accounts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(sa.String(200))
    handle: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("true")
    )
    oauth_access_token_enc: Mapped[str | None] = mapped_column(sa.Text)
    oauth_refresh_token_enc: Mapped[str | None] = mapped_column(sa.Text)
    oauth_expires_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    oauth_token_type: Mapped[str | None] = mapped_column(sa.String(50))
    oauth_scopes: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="accounts")
    settings: Mapped["AccountSettings"] = relationship(
        back_populates="account", uselist=False, cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(back_populates="account")
    ideas: Mapped[list["Idea"]] = relationship(back_populates="account")
    drafts: Mapped[list["Draft"]] = relationship(back_populates="account")
    schedule_queue: Mapped[list["ScheduleQueue"]] = relationship(back_populates="account")
    posts: Mapped[list["Post"]] = relationship(back_populates="account")
    template_performance: Mapped[list["TemplatePerformance"]] = relationship(
        back_populates="account"
    )

    __table_args__ = (
        sa.UniqueConstraint("workspace_id", "handle", name="uq_x_accounts_workspace_handle"),
    )


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(sa.String(32), nullable=False, server_default="x")
    state: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    code_verifier: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    x_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)


class AccountSettings(Base):
    __tablename__ = "account_settings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    x_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    timezone: Mapped[str] = mapped_column(sa.String(64), nullable=False, server_default="UTC")
    daily_post_min: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("1")
    )
    daily_post_max: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("3")
    )
    allowed_hours: Mapped[list[int]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=sa.text("'[]'::jsonb")
    )
    min_spacing_hours: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("2")
    )
    allow_links: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    link_post_ratio: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    thread_ratio: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0.2")
    )
    max_thread_len: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("5")
    )
    format_weights: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    topic_weights: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    account: Mapped["XAccount"] = relationship(back_populates="settings")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    x_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
    )
    type: Mapped[str] = mapped_column(sa.String(50), nullable=False, server_default="rss")
    url: Mapped[str] = mapped_column(sa.String(2000), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("true")
    )
    last_ingested_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="sources")
    account: Mapped[Optional["XAccount"]] = relationship(back_populates="sources")
    ideas: Mapped[list["Idea"]] = relationship(back_populates="source")

    __table_args__ = (
        sa.UniqueConstraint("workspace_id", "url", name="uq_sources_workspace_url"),
    )


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    x_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("sources.id", ondelete="SET NULL"),
    )
    title: Mapped[str | None] = mapped_column(sa.String(500))
    summary: Mapped[str | None] = mapped_column(sa.Text)
    url: Mapped[str | None] = mapped_column(sa.String(2000))
    published_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    raw_content: Mapped[str | None] = mapped_column(sa.Text)
    fingerprint: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    score: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, server_default="new")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="ideas")
    account: Mapped[Optional["XAccount"]] = relationship(back_populates="ideas")
    source: Mapped[Optional["Source"]] = relationship(back_populates="ideas")
    drafts: Mapped[list["Draft"]] = relationship(back_populates="idea")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    x_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
    )
    idea_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("ideas.id", ondelete="SET NULL"),
    )
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content_fingerprint: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    format: Mapped[str] = mapped_column(sa.String(100), nullable=False, server_default="tweet_single")
    is_thread: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    thread_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("1")
    )
    score: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, server_default="draft")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="drafts")
    account: Mapped[Optional["XAccount"]] = relationship(back_populates="drafts")
    idea: Mapped[Optional["Idea"]] = relationship(back_populates="drafts")
    schedule_items: Mapped[list["ScheduleQueue"]] = relationship(back_populates="draft")
    posts: Mapped[list["Post"]] = relationship(back_populates="draft")


class ScheduleQueue(Base):
    __tablename__ = "schedule_queue"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    x_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    draft_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("drafts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    scheduled_for: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, server_default="scheduled")
    attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    next_attempt_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    account: Mapped["XAccount"] = relationship(back_populates="schedule_queue")
    draft: Mapped["Draft"] = relationship(back_populates="schedule_items")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    x_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    draft_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("drafts.id", ondelete="SET NULL"),
    )
    x_post_id: Mapped[str | None] = mapped_column(sa.String(200), unique=True)
    x_post_url: Mapped[str | None] = mapped_column(sa.String(2048))
    posted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    is_thread: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, server_default="posted")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    account: Mapped["XAccount"] = relationship(back_populates="posts")
    draft: Mapped[Optional["Draft"]] = relationship(back_populates="posts")
    metrics: Mapped[list["PostMetricsDaily"]] = relationship(back_populates="post")


class PostMetricsDaily(Base):
    __tablename__ = "post_metrics_daily"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    impressions: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    likes: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    reposts: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    replies: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    bookmarks: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    clicks: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    post: Mapped["Post"] = relationship(back_populates="metrics")

    __table_args__ = (
        sa.UniqueConstraint("post_id", "metric_date", name="uq_post_metrics_daily"),
    )


class TemplatePerformance(Base):
    __tablename__ = "template_performance"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    x_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    format: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    metric_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    impressions_avg: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    like_rate: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    repost_rate: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    account: Mapped["XAccount"] = relationship(back_populates="template_performance")

    __table_args__ = (
        sa.UniqueConstraint(
            "x_account_id", "format", "metric_date", name="uq_template_performance"
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    x_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("x_accounts.id", ondelete="SET NULL"),
    )
    event_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    meta: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="audit_logs")

