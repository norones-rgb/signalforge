from __future__ import annotations

import logging

from sqlalchemy import select

from app.models import AccountSettings, Draft
from app.services.dedupe import is_similar
from app.services.safety import contains_blocked_content, contains_link, split_thread
from app.db.session import SessionLocal
from celery_app import celery_app


logger = logging.getLogger(__name__)


def _max_len(draft: Draft) -> int:
    return 260 if draft.is_thread else 240


def _reject(draft: Draft, reason: str) -> None:
    draft.status = "rejected"
    logger.info("draft rejected", extra={"draft_id": str(draft.id), "reason": reason})


@celery_app.task(name="guardrails_check")
def guardrails_check() -> dict:
    approved = 0
    rejected = 0

    with SessionLocal() as session:
        drafts = session.scalars(select(Draft).where(Draft.status == "draft")).all()

        for draft in drafts:
            settings = None
            if draft.x_account_id:
                settings = session.scalar(
                    select(AccountSettings).where(AccountSettings.x_account_id == draft.x_account_id)
                )

            max_len = _max_len(draft)
            if draft.is_thread:
                tweets = split_thread(draft.content)
                if any(len(tweet) > max_len for tweet in tweets):
                    _reject(draft, "thread_length")
                    rejected += 1
                    continue
            else:
                if len(draft.content) > max_len:
                    _reject(draft, "length")
                    rejected += 1
                    continue

            if contains_blocked_content(draft.content):
                _reject(draft, "safety")
                rejected += 1
                continue

            if contains_link(draft.content):
                allow_links = bool(settings.allow_links) if settings else False
                ratio = float(settings.link_post_ratio) if settings else 0.0
                if not allow_links or ratio <= 0:
                    _reject(draft, "link_policy")
                    rejected += 1
                    continue

            if draft.is_thread and settings and draft.thread_count > settings.max_thread_len:
                _reject(draft, "thread_limit")
                rejected += 1
                continue

            if draft.is_thread and settings and settings.thread_ratio <= 0:
                _reject(draft, "thread_ratio")
                rejected += 1
                continue

            if draft.idea:
                source_texts = [draft.idea.summary or "", draft.idea.raw_content or ""]
                if any(is_similar(draft.content, text, threshold=0.8) for text in source_texts):
                    _reject(draft, "source_similarity")
                    rejected += 1
                    continue

            others = session.scalars(
                select(Draft)
                .where(Draft.id != draft.id)
                .where(Draft.status.in_(["draft", "approved", "scheduled", "posted"]))
            ).all()
            if any(is_similar(draft.content, other.content) for other in others):
                _reject(draft, "similarity")
                rejected += 1
                continue

            draft.status = "approved"
            approved += 1

        session.commit()

    logger.info(
        "guardrails_check complete",
        extra={"approved": approved, "rejected": rejected},
    )
    return {"approved": approved, "rejected": rejected}
