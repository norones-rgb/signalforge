from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.append(str(API_PATH))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import User, Workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--workspace", default="Default Workspace")
    args = parser.parse_args()

    with SessionLocal() as session:
        workspace = session.scalar(select(Workspace).where(Workspace.name == args.workspace))
        if not workspace:
            workspace = Workspace(name=args.workspace)
            session.add(workspace)
            session.flush()

        user = session.scalar(select(User).where(User.email == args.email))
        if not user:
            user = User(
                email=args.email,
                password_hash=get_password_hash(args.password),
                workspace_id=workspace.id,
                is_active=True,
            )
            session.add(user)
        else:
            user.password_hash = get_password_hash(args.password)
            user.workspace_id = workspace.id
            user.is_active = True

        session.commit()
        print("Admin user ready")


if __name__ == "__main__":
    main()
