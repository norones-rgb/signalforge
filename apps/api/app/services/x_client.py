from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.models import XAccount


@dataclass
class XPostResponse:
    post_id: str
    url: str


class XClient(Protocol):
    def post_tweet(self, text: str, reply_to_id: str | None = None) -> XPostResponse:
        ...

    def fetch_metrics(self, post_id: str) -> dict:
        ...


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


class StubXClient:
    def __init__(self, account: XAccount | None = None) -> None:
        self.account = account

    def post_tweet(self, text: str, reply_to_id: str | None = None) -> XPostResponse:
        handle = self.account.handle if self.account else "signalforge"
        post_id = f"stub_{handle}_{_now_stamp()}"
        url = f"https://x.com/{handle}/status/{post_id}"
        return XPostResponse(post_id=post_id, url=url)

    def fetch_metrics(self, post_id: str) -> dict:
        return {
            "impressions": 0,
            "likes": 0,
            "reposts": 0,
            "replies": 0,
            "bookmarks": 0,
            "clicks": 0,
        }


def get_x_client(account: XAccount | None = None) -> XClient:
    if os.getenv("X_API_MODE", "stub").lower() == "stub":
        return StubXClient(account)
    # Placeholder for real implementation
    return StubXClient(account)
