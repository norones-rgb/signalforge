from __future__ import annotations

import logging

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Post, PostMetricsDaily
from app.services.x_client import get_x_client
from celery_app import celery_app
from shared.utils.time import utc_now


logger = logging.getLogger(__name__)


@celery_app.task(name="pull_analytics")
def pull_analytics() -> dict:
    created = 0
    failed = 0

    with SessionLocal() as session:
        posts = session.scalars(select(Post).where(Post.x_post_id.isnot(None))).all()

        for post in posts:
            metric_date = utc_now().date()
            exists = session.scalar(
                select(PostMetricsDaily.id)
                .where(PostMetricsDaily.post_id == post.id)
                .where(PostMetricsDaily.metric_date == metric_date)
            )
            if exists:
                continue

            account = post.account
            client = get_x_client(account)
            try:
                metrics = client.fetch_metrics(post.x_post_id)
            except Exception as exc:
                failed += 1
                logger.error(
                    "analytics fetch failed",
                    extra={"post_id": str(post.id), "error": str(exc)},
                )
                continue

            metrics_row = PostMetricsDaily(
                post_id=post.id,
                metric_date=metric_date,
                impressions=int(metrics.get("impressions", 0)),
                likes=int(metrics.get("likes", 0)),
                reposts=int(metrics.get("reposts", 0)),
                replies=int(metrics.get("replies", 0)),
                bookmarks=int(metrics.get("bookmarks", 0)),
                clicks=int(metrics.get("clicks", 0)),
            )
            session.add(metrics_row)
            created += 1

        session.commit()

    logger.info("pull_analytics complete", extra={"created": created, "failed": failed})
    return {"created": created, "failed": failed}
