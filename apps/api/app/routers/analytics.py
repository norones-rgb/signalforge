from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.deps import get_current_user
from app.services.analytics import summary_for_range


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    return {
        "last_7_days": summary_for_range(db, user.workspace_id, 7),
        "last_30_days": summary_for_range(db, user.workspace_id, 30),
    }
