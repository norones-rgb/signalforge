from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Draft, Idea
from app.services.llm_client import get_llm, load_prompt, render_prompt
from celery_app import celery_app
from shared.utils.hashing import sha256_text
from shared.utils.text import normalize_text


logger = logging.getLogger(__name__)


def _formats_path() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "shared" / "templates" / "formats.json"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("formats.json not found")


def _load_formats() -> dict:
    return json.loads(_formats_path().read_text(encoding="utf-8"))


def _content_fingerprint(text: str) -> str:
    return sha256_text(normalize_text(text))


@celery_app.task(name="generate_drafts")
def generate_drafts() -> dict:
    llm = get_llm()
    formats = _load_formats()
    created = 0
    skipped = 0

    with SessionLocal() as session:
        ideas = session.scalars(select(Idea).where(Idea.status == "scored")).all()

        for idea in ideas:
            existing = session.scalar(select(Draft.id).where(Draft.idea_id == idea.id))
            if existing:
                skipped += 1
                continue

            format_key = "tweet_single"
            format_cfg = formats[format_key]
            prompt = load_prompt(format_cfg["prompt"])
            rendered = render_prompt(
                prompt,
                title=idea.title or "",
                summary=idea.summary or "",
                url=idea.url or "",
            )

            content = llm.generate(rendered, max_chars=int(format_cfg["max_chars"]))
            if not content:
                skipped += 1
                continue

            fingerprint = _content_fingerprint(content)
            exists = session.scalar(select(Draft.id).where(Draft.content_fingerprint == fingerprint))
            if exists:
                skipped += 1
                continue

            draft = Draft(
                workspace_id=idea.workspace_id,
                x_account_id=idea.x_account_id,
                idea_id=idea.id,
                content=content,
                content_fingerprint=fingerprint,
                format=format_key,
                is_thread=bool(format_cfg.get("is_thread", False)),
                thread_count=int(format_cfg.get("thread_count", 1)),
                score=idea.score,
                status="draft",
            )
            session.add(draft)
            idea.status = "drafted"
            created += 1

        session.commit()

    logger.info(
        "generate_drafts complete",
        extra={"created": created, "skipped": skipped},
    )
    return {"created": created, "skipped": skipped}
