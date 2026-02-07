from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Source, XAccount
from app.routers.deps import get_current_user
from app.schemas.sources import SourceCreate, SourceResponse


router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
def list_sources(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[SourceResponse]:
    sources = db.scalars(select(Source).where(Source.workspace_id == user.workspace_id)).all()
    return [SourceResponse.model_validate(source) for source in sources]


@router.post("", response_model=SourceResponse)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> SourceResponse:
    if payload.workspace_id != str(user.workspace_id):
        raise HTTPException(status_code=403, detail="Invalid workspace")

    if payload.x_account_id:
        account = db.get(XAccount, payload.x_account_id)
        if not account or account.workspace_id != user.workspace_id:
            raise HTTPException(status_code=404, detail="Account not found")

    source = Source(
        workspace_id=user.workspace_id,
        x_account_id=payload.x_account_id,
        type=payload.type,
        url=payload.url,
        is_enabled=payload.is_enabled,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return SourceResponse.model_validate(source)
