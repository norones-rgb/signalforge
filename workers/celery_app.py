from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

from app.core.logging import setup_logging


setup_logging()

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "signalforge",
    broker=redis_url,
    backend=redis_url,
    include=["tasks"],
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.timezone = "UTC"
celery_app.conf.task_acks_late = True

celery_app.conf.beat_schedule = {
    "ingest_sources_hourly": {
        "task": "ingest_sources",
        "schedule": 60 * 60,
    },
    "score_ideas_hourly": {
        "task": "score_ideas",
        "schedule": 60 * 60,
    },
    "generate_drafts_2h": {
        "task": "generate_drafts",
        "schedule": 60 * 60 * 2,
    },
    "schedule_posts_hourly": {
        "task": "schedule_posts",
        "schedule": 60 * 60,
    },
    "pull_analytics_daily": {
        "task": "pull_analytics",
        "schedule": crontab(hour=1, minute=0),
    },
    "learn_templates_daily": {
        "task": "learn_templates",
        "schedule": crontab(hour=2, minute=0),
    },
}
