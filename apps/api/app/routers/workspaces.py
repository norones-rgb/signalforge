from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Workspace
from app.routers.deps import get_current_user
from app.schemas.workspaces import WorkspaceCreate, WorkspaceResponse


router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[WorkspaceResponse]:
    workspaces = db.scalars(select(Workspace).where(Workspace.id == user.workspace_id)).all()
    return [WorkspaceResponse.model_validate(ws) for ws in workspaces]


@router.post("", response_model=WorkspaceResponse)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> WorkspaceResponse:
    workspace = Workspace(name=payload.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return WorkspaceResponse.model_validate(workspace)
