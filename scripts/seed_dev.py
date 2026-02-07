from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.append(str(API_PATH))

from sqlalchemy import select

from app.core.security import encrypt_token, get_password_hash
from app.db.session import SessionLocal
from app.models import AccountSettings, Source, User, Workspace, XAccount


DEFAULT_SOURCES = [
    "https://feeds.feedburner.com/TechCrunch/",
    "https://www.theverge.com/rss/index.xml",
]


def get_or_create(session, model, defaults=None, **filters):
    instance = session.scalar(select(model).filter_by(**filters))
    if instance:
        return instance, False
    params = {**filters, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def main() -> None:
    with SessionLocal() as session:
        workspace, _ = get_or_create(session, Workspace, name="Default Workspace")

        admin_email = "admin@signalforge.local"
        admin_password = "admin1234"
        user, _ = get_or_create(
            session,
            User,
            email=admin_email,
            defaults={
                "workspace_id": workspace.id,
                "password_hash": get_password_hash(admin_password),
                "is_active": True,
            },
        )
        if user.workspace_id != workspace.id:
            user.workspace_id = workspace.id

        x_account, _ = get_or_create(
            session,
            XAccount,
            workspace_id=workspace.id,
            handle="signalforge_demo",
            defaults={
                "name": "SignalForge Demo",
                "is_enabled": True,
                "oauth_access_token_enc": encrypt_token("access-token"),
                "oauth_refresh_token_enc": encrypt_token("refresh-token"),
            },
        )

        settings_defaults = {
            "timezone": "UTC",
            "daily_post_min": 1,
            "daily_post_max": 3,
            "allowed_hours": [9, 11, 13, 15, 17],
            "min_spacing_hours": 2,
            "allow_links": False,
            "link_post_ratio": 0.0,
            "thread_ratio": 0.2,
            "max_thread_len": 5,
            "format_weights": {"tweet_single": 1.0, "thread_5": 0.5},
            "topic_weights": {},
        }
        get_or_create(
            session,
            AccountSettings,
            x_account_id=x_account.id,
            defaults=settings_defaults,
        )

        for url in DEFAULT_SOURCES:
            get_or_create(
                session,
                Source,
                workspace_id=workspace.id,
                url=url,
                defaults={
                    "type": "rss",
                    "is_enabled": True,
                    "x_account_id": x_account.id,
                },
            )

        session.commit()
        print("Seed data created")


if __name__ == "__main__":
    main()
