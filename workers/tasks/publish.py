from __future__ import annotations

import logging
import os
from datetime import timedelta

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models import Draft, Post, ScheduleQueue, XAccount
from app.services.safety import split_thread
from app.services.x_client import get_x_client
from celery_app import celery_app
from shared.utils.time import utc_now


logger = logging.getLogger(__name__)


def _posting_disabled() -> bool:
    value = os.getenv("POSTING_DISABLED", "false").lower()
    return value in {"1", "true", "yes"}


def _max_attempts() -> int:
    try:
        return int(os.getenv("PUBLISH_MAX_ATTEMPTS", "3"))
    except ValueError:
        return 3


def _next_backoff(attempts: int) -> timedelta:
    base_minutes = 5
    delay = base_minutes * (2 ** max(attempts - 1, 0))
    return timedelta(minutes=min(delay, 60))


@celery_app.task(name="publish_post")
def publish_post() -> dict:
    if _posting_disabled():
        logger.warning("publishing disabled via POSTING_DISABLED")
        return {"status": "disabled"}

    published = 0
    failed = 0

    with SessionLocal() as session:
        now = utc_now()
        due_items = session.scalars(
            select(ScheduleQueue)
            .where(ScheduleQueue.status == "scheduled")
            .where(ScheduleQueue.scheduled_for <= now)
            .where(or_(ScheduleQueue.next_attempt_at.is_(None), ScheduleQueue.next_attempt_at <= now))
            .order_by(ScheduleQueue.scheduled_for.asc())
        ).all()

        for item in due_items:
            if item.attempts >= _max_attempts():
                item.status = "failed"
                failed += 1
                continue

            account = session.get(XAccount, item.x_account_id)
            if not account or not account.is_enabled:
                item.status = "skipped"
                continue

            draft = session.get(Draft, item.draft_id)
            if not draft:
                item.status = "skipped"
                continue

            client = get_x_client(account)

            try:
                if draft.is_thread:
                    tweets = split_thread(draft.content)
                    if not tweets:
                        raise ValueError("empty thread")

                    parent_id = None
                    response = None
                    for tweet in tweets:
                        response = client.post_tweet(tweet, reply_to_id=parent_id)
                        parent_id = response.post_id

                    post = Post(
                        x_account_id=account.id,
                        draft_id=draft.id,
                        x_post_id=parent_id,
                        x_post_url=response.url if response else None,
                        posted_at=utc_now(),
                        is_thread=True,
                        status="posted",
                    )
                else:
                    response = client.post_tweet(draft.content)
                    post = Post(
                        x_account_id=account.id,
                        draft_id=draft.id,
                        x_post_id=response.post_id,
                        x_post_url=response.url,
                        posted_at=utc_now(),
                        is_thread=False,
                        status="posted",
                    )

                session.add(post)
                item.status = "posted"
                item.next_attempt_at = None
                draft.status = "posted"
                published += 1
            except Exception as exc:
                item.attempts += 1
                item.last_error = str(exc)
                if item.attempts >= _max_attempts():
                    item.status = "failed"
                else:
                    item.next_attempt_at = utc_now() + _next_backoff(item.attempts)
                failed += 1
                logger.error(
                    "publish failed",
                    extra={"schedule_id": str(item.id), "error": str(exc)},
                )

        session.commit()

    logger.info("publish_post complete", extra={"published": published, "failed": failed})
    return {"published": published, "failed": failed}
