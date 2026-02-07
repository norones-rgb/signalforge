from __future__ import annotations

from celery import Celery

from app.core.config import settings


celery_client = Celery(
    "signalforge_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


def trigger_pipeline() -> dict:
    task_names = [
        "ingest_sources",
        "score_ideas",
        "generate_drafts",
        "guardrails_check",
        "schedule_posts",
        "publish_post",
    ]
    results = {}
    for name in task_names:
        results[name] = celery_client.send_task(name).id
    return results
