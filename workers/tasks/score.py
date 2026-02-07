from __future__ import annotations

import logging

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Idea
from celery_app import celery_app
from shared.utils.time import utc_now


logger = logging.getLogger(__name__)


def _score_idea(idea: Idea) -> float:
    score = 0.0

    if idea.title:
        score += min(len(idea.title) / 120, 1.0) * 0.4
    if idea.summary:
        score += min(len(idea.summary) / 500, 1.0) * 0.4

    if idea.published_at:
        age_days = (utc_now() - idea.published_at).days
        recency = max(0.0, 1.0 - (age_days / 7))
        score += recency * 0.2

    return round(score, 4)


@celery_app.task(name="score_ideas")
def score_ideas() -> dict:
    updated = 0

    with SessionLocal() as session:
        ideas = session.scalars(select(Idea).where(Idea.status == "new")).all()

        for idea in ideas:
            idea.score = _score_idea(idea)
            idea.status = "scored"
            updated += 1

        session.commit()

    logger.info("score_ideas complete", extra={"updated": updated})
    return {"updated": updated}
