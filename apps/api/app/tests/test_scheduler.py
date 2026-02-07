from datetime import datetime, timezone

import pytest

from app.services import scheduler


class FixedRandom:
    def randint(self, a, b):
        return 0


def test_candidate_spacing(monkeypatch):
    monkeypatch.setattr(scheduler, "utc_now", lambda: datetime(2026, 2, 6, 8, 0, tzinfo=timezone.utc))
    monkeypatch.setattr(scheduler.random, "randint", FixedRandom().randint)

    tz = scheduler._parse_timezone("UTC")
    allowed_hours = [9, 11, 13]

    candidates = scheduler._candidate_times(tz, allowed_hours, 3, [])
    hours = [dt.astimezone(timezone.utc).hour for dt in candidates]
    assert hours == [9, 13]
