from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Idea
from app.routers.deps import get_current_user
from app.schemas.ideas import IdeaResponse


router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("", response_model=list[IdeaResponse])
def list_ideas(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[IdeaResponse]:
    ideas = db.scalars(select(Idea).where(Idea.workspace_id == user.workspace_id)).all()
    return [IdeaResponse.model_validate(idea) for idea in ideas]
