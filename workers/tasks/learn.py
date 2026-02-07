from __future__ import annotations

import logging

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import AccountSettings, Draft, Post, PostMetricsDaily, TemplatePerformance
from celery_app import celery_app
from shared.utils.time import utc_now


logger = logging.getLogger(__name__)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@celery_app.task(name="learn_templates")
def learn_templates() -> dict:
    created = 0
    metric_date = utc_now().date()

    with SessionLocal() as session:
        rows = session.execute(
            select(
                Draft.format,
                Post.x_account_id,
                func.coalesce(func.avg(PostMetricsDaily.impressions), 0),
                func.coalesce(func.avg(PostMetricsDaily.likes), 0),
                func.coalesce(func.avg(PostMetricsDaily.reposts), 0),
            )
            .join(Post, Post.draft_id == Draft.id)
            .join(PostMetricsDaily, PostMetricsDaily.post_id == Post.id)
            .where(PostMetricsDaily.metric_date == metric_date)
            .group_by(Draft.format, Post.x_account_id)
        ).all()

        samples_by_account: dict[str, list[float]] = {}
        for _, account_id, impressions_avg, _, _ in rows:
            account_id_str = str(account_id)
            samples_by_account.setdefault(account_id_str, []).append(float(impressions_avg))

        overall_by_account = {
            account_id: (sum(values) / len(values)) if values else 0.0
            for account_id, values in samples_by_account.items()
        }

        for format_name, account_id, impressions_avg, likes_avg, reposts_avg in rows:
            like_rate = 0.0
            repost_rate = 0.0
            if impressions_avg and impressions_avg > 0:
                like_rate = float(likes_avg) / float(impressions_avg)
                repost_rate = float(reposts_avg) / float(impressions_avg)

            existing = session.scalar(
                select(TemplatePerformance.id)
                .where(TemplatePerformance.format == format_name)
                .where(TemplatePerformance.x_account_id == account_id)
                .where(TemplatePerformance.metric_date == metric_date)
            )
            if not existing:
                perf = TemplatePerformance(
                    x_account_id=account_id,
                    format=format_name,
                    metric_date=metric_date,
                    impressions_avg=float(impressions_avg),
                    like_rate=like_rate,
                    repost_rate=repost_rate,
                )
                session.add(perf)
                created += 1

            settings = session.scalar(
                select(AccountSettings).where(AccountSettings.x_account_id == account_id)
            )
            if settings:
                overall_avg = overall_by_account.get(str(account_id), 0.0)
                if overall_avg > 0:
                    weight = _clamp(float(impressions_avg) / overall_avg, 0.5, 2.0)
                else:
                    weight = 1.0
                weights = dict(settings.format_weights or {})
                weights[format_name] = weight
                settings.format_weights = weights

        session.commit()

    logger.info("learn_templates complete", extra={"created": created})
    return {"created": created}
