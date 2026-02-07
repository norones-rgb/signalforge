from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.models import AccountSettings, Draft, Idea
from app.services.safety import contains_link
from shared.utils.time import utc_now


DEFAULT_ALLOWED_HOURS = [9, 11, 13, 15, 17]


@dataclass
class ScheduleDecision:
    scheduled_for: datetime
    draft: Draft


def _parse_timezone(value: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(value or "UTC")
    except Exception:
        return ZoneInfo("UTC")


def _allowed_hours(settings: AccountSettings | None) -> list[int]:
    hours = settings.allowed_hours if settings and settings.allowed_hours else DEFAULT_ALLOWED_HOURS
    sanitized = [h for h in hours if isinstance(h, int) and 0 <= h <= 23]
    return sanitized or DEFAULT_ALLOWED_HOURS


def _daily_target(settings: AccountSettings | None) -> int:
    if not settings:
        return 0
    low = settings.daily_post_min
    high = settings.daily_post_max
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def _candidate_times(
    tz: ZoneInfo,
    allowed_hours: list[int],
    min_spacing_hours: int,
    existing_times_utc: list[datetime],
) -> list[datetime]:
    now_local = utc_now().astimezone(tz)
    today = now_local.date()
    candidates: list[datetime] = []

    for hour in allowed_hours:
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        candidate_local = datetime.combine(today, time(hour, minute, second), tzinfo=tz)
        if candidate_local <= now_local:
            continue
        candidates.append(candidate_local.astimezone(ZoneInfo("UTC")))

    candidates.sort()

    spaced: list[datetime] = []
    min_delta = timedelta(hours=max(1, min_spacing_hours))

    for candidate in candidates:
        if any(abs(candidate - existing) < min_delta for existing in existing_times_utc):
            continue
        if spaced and abs(candidate - spaced[-1]) < min_delta:
            continue
        spaced.append(candidate)

    return spaced


def _topic_weight(settings: AccountSettings | None, idea: Idea | None) -> float:
    if not settings or not settings.topic_weights:
        return 1.0
    if idea and idea.title:
        key = idea.title.split(" ", 1)[0].lower()
        return float(settings.topic_weights.get(key, 1.0))
    return 1.0


def _format_weight(settings: AccountSettings | None, draft: Draft) -> float:
    if not settings or not settings.format_weights:
        return 1.0
    return float(settings.format_weights.get(draft.format, 1.0))


def weighted_choice(drafts: list[Draft], settings: AccountSettings | None) -> Draft | None:
    weights = []
    for draft in drafts:
        idea = draft.idea
        weight = max(draft.score, 0.01) * _format_weight(settings, draft) * _topic_weight(settings, idea)
        weights.append(max(weight, 0.01))

    total = sum(weights)
    if total <= 0:
        return None

    target = random.random() * total
    cumulative = 0.0
    for draft, weight in zip(drafts, weights):
        cumulative += weight
        if cumulative >= target:
            return draft
    return drafts[-1] if drafts else None


def limit_thread_and_link_drafts(
    drafts: list[Draft],
    settings: AccountSettings | None,
    remaining_slots: int,
    thread_count: int,
    link_count: int,
) -> tuple[list[Draft], int, int]:
    if remaining_slots <= 0:
        return [], thread_count, link_count

    thread_ratio = settings.thread_ratio if settings else 0.0
    if thread_ratio > 0 and remaining_slots > 0:
        max_threads = max(1, int(remaining_slots * thread_ratio))
    else:
        max_threads = 0

    allow_links = settings.allow_links if settings else False
    link_ratio = settings.link_post_ratio if settings else 0.0
    if allow_links and link_ratio > 0 and remaining_slots > 0:
        max_links = max(1, int(remaining_slots * link_ratio))
    else:
        max_links = 0

    filtered = []
    for draft in drafts:
        is_thread = draft.is_thread
        has_link = contains_link(draft.content)

        if is_thread and max_threads > 0 and thread_count >= max_threads:
            continue
        if has_link and (not allow_links or link_ratio <= 0):
            continue
        if has_link and max_links > 0 and link_count >= max_links:
            continue

        filtered.append(draft)

    return filtered, max_threads, max_links
