from __future__ import annotations

import os
import re

from shared.utils.text import normalize_text


DEFAULT_BLOCKLIST = [
    "kill yourself",
    "go die",
    "subhuman",
    "vermin",
    "exterminate",
    "genocide",
]


def get_blocklist() -> list[str]:
    extra = os.getenv("SAFETY_BLOCKLIST", "")
    terms = [term.strip().lower() for term in extra.split(",") if term.strip()]
    return sorted(set(DEFAULT_BLOCKLIST + terms))


def contains_blocked_content(text: str) -> bool:
    normalized = normalize_text(text)
    for term in get_blocklist():
        if not term:
            continue
        pattern = re.escape(term)
        if re.search(rf"\b{pattern}\b", normalized):
            return True
    return False


def contains_link(text: str) -> bool:
    return bool(re.search(r"https?://", text, flags=re.IGNORECASE))


def split_thread(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) <= 1:
        return [text.strip()]

    tweets: list[str] = []
    for line in lines:
        cleaned = re.sub(r"^\d+[\.)\-:\s]+", "", line).strip()
        if cleaned:
            tweets.append(cleaned)
    return tweets or [text.strip()]
