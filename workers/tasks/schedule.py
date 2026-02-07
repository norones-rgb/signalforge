from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import AccountSettings, Draft, Post, ScheduleQueue, XAccount
from app.services.safety import contains_link
from app.services.scheduler import (
    _allowed_hours,
    _candidate_times,
    _daily_target,
    _parse_timezone,
    limit_thread_and_link_drafts,
    weighted_choice,
)
from celery_app import celery_app
from shared.utils.time import utc_now


logger = logging.getLogger(__name__)


def _day_bounds(tz):
    now_local = utc_now().astimezone(tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(_parse_timezone("UTC")), end_local.astimezone(_parse_timezone("UTC"))


@celery_app.task(name="schedule_posts")
def schedule_posts() -> dict:
    scheduled = 0

    with SessionLocal() as session:
        accounts = session.scalars(select(XAccount).where(XAccount.is_enabled.is_(True))).all()

        for account in accounts:
            settings = session.scalar(
                select(AccountSettings).where(AccountSettings.x_account_id == account.id)
            )
            if not settings:
                continue

            tz = _parse_timezone(settings.timezone)
            day_start, day_end = _day_bounds(tz)

            existing_times = session.scalars(
                select(ScheduleQueue.scheduled_for)
                .where(ScheduleQueue.x_account_id == account.id)
                .where(ScheduleQueue.status == "scheduled")
                .where(ScheduleQueue.scheduled_for >= day_start)
                .where(ScheduleQueue.scheduled_for < day_end)
            ).all()

            posted_times = session.scalars(
                select(Post.posted_at)
                .where(Post.x_account_id == account.id)
                .where(Post.posted_at >= day_start)
                .where(Post.posted_at < day_end)
            ).all()
            existing_times.extend([t for t in posted_times if t])

            posted_count = session.scalar(
                select(func.count(Post.id))
                .where(Post.x_account_id == account.id)
                .where(Post.posted_at >= day_start)
                .where(Post.posted_at < day_end)
            ) or 0

            daily_target = _daily_target(settings)
            remaining_slots = max(0, daily_target - len(existing_times) - posted_count)
            if remaining_slots <= 0:
                continue

            candidates = _candidate_times(
                tz,
                _allowed_hours(settings),
                settings.min_spacing_hours,
                existing_times,
            )
            if not candidates:
                continue

            drafts = session.scalars(
                select(Draft)
                .where(Draft.x_account_id == account.id)
                .where(Draft.status == "approved")
            ).all()
            if not drafts:
                continue

            thread_count = 0
            link_count = 0
            scheduled_local = 0

            for scheduled_for in candidates[:remaining_slots]:
                slots_left = remaining_slots - scheduled_local
                filtered, _, _ = limit_thread_and_link_drafts(
                    drafts,
                    settings,
                    slots_left,
                    thread_count,
                    link_count,
                )
                if not filtered:
                    break

                draft = weighted_choice(filtered, settings)
                if not draft:
                    break

                if draft.is_thread:
                    thread_count += 1
                if contains_link(draft.content):
                    link_count += 1

                schedule_item = ScheduleQueue(
                    x_account_id=account.id,
                    draft_id=draft.id,
                    scheduled_for=scheduled_for,
                    status="scheduled",
                )
                session.add(schedule_item)
                draft.status = "scheduled"
                drafts.remove(draft)
                scheduled += 1
                scheduled_local += 1

            session.commit()

    logger.info("schedule_posts complete", extra={"scheduled": scheduled})
    return {"scheduled": scheduled}
