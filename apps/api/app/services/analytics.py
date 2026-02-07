from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Post, PostMetricsDaily, XAccount


def summary_for_range(session: Session, workspace_id: UUID, days: int) -> dict:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    metrics = session.execute(
        select(
            func.coalesce(func.sum(PostMetricsDaily.impressions), 0),
            func.coalesce(func.sum(PostMetricsDaily.likes), 0),
            func.coalesce(func.sum(PostMetricsDaily.reposts), 0),
            func.coalesce(func.sum(PostMetricsDaily.replies), 0),
            func.coalesce(func.sum(PostMetricsDaily.bookmarks), 0),
            func.coalesce(func.sum(PostMetricsDaily.clicks), 0),
        )
        .select_from(PostMetricsDaily)
        .join(Post, PostMetricsDaily.post_id == Post.id)
        .join(XAccount, Post.x_account_id == XAccount.id)
        .where(XAccount.workspace_id == workspace_id)
        .where(PostMetricsDaily.metric_date >= start_date)
    ).one()

    return {
        "from": str(start_date),
        "to": str(end_date),
        "impressions": int(metrics[0]),
        "likes": int(metrics[1]),
        "reposts": int(metrics[2]),
        "replies": int(metrics[3]),
        "bookmarks": int(metrics[4]),
        "clicks": int(metrics[5]),
    }
