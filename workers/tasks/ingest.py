from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Idea, Source, XAccount
from celery_app import celery_app
from shared.utils.hashing import sha256_text
from shared.utils.text import normalize_text


logger = logging.getLogger(__name__)


def _entry_published(entry) -> datetime | None:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return None
    return datetime(*published[:6], tzinfo=timezone.utc)


def _entry_summary(entry) -> str | None:
    summary = entry.get("summary") or entry.get("description")
    if summary:
        return summary
    content = entry.get("content") or []
    if content:
        return content[0].get("value")
    return None


def _entry_raw(entry) -> str | None:
    content = entry.get("content") or []
    if content:
        return content[0].get("value")
    return None


def _fingerprint(*parts: str | None) -> str:
    normalized = normalize_text("|".join([part or "" for part in parts]))
    return sha256_text(normalized)


@celery_app.task(name="ingest_sources")
def ingest_sources() -> dict:
    inserted = 0
    skipped = 0
    failed = 0

    with SessionLocal() as session:
        sources = session.scalars(select(Source).where(Source.is_enabled.is_(True))).all()

        for source in sources:
            if source.x_account_id:
                account = session.get(XAccount, source.x_account_id)
                if not account or not account.is_enabled:
                    continue

            try:
                feed = feedparser.parse(source.url)
            except Exception as exc:
                failed += 1
                logger.error("Feed parse error", extra={"url": source.url, "error": str(exc)})
                continue

            if getattr(feed, "bozo", False):
                logger.warning("Feed parse warning", extra={"url": source.url})

            for entry in feed.entries:
                title = entry.get("title")
                url = entry.get("link") or entry.get("id")
                summary = _entry_summary(entry)
                fingerprint = _fingerprint(title, url, summary)

                exists = session.scalar(select(Idea.id).where(Idea.fingerprint == fingerprint))
                if exists:
                    skipped += 1
                    continue

                idea = Idea(
                    workspace_id=source.workspace_id,
                    x_account_id=source.x_account_id,
                    source_id=source.id,
                    title=title,
                    summary=summary,
                    url=url,
                    published_at=_entry_published(entry),
                    raw_content=_entry_raw(entry),
                    fingerprint=fingerprint,
                    score=0.0,
                    status="new",
                )
                session.add(idea)
                inserted += 1

            source.last_ingested_at = datetime.now(timezone.utc)

        session.commit()

    logger.info(
        "ingest_sources complete",
        extra={"inserted": inserted, "skipped": skipped, "failed": failed},
    )
    return {"inserted": inserted, "skipped": skipped, "failed": failed}
