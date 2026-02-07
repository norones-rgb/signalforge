from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Draft
from app.routers.deps import get_current_user
from app.schemas.drafts import DraftResponse


router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.get("", response_model=list[DraftResponse])
def list_drafts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[DraftResponse]:
    drafts = db.scalars(select(Draft).where(Draft.workspace_id == user.workspace_id)).all()
    return [DraftResponse.model_validate(draft) for draft in drafts]
