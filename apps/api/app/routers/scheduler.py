from __future__ import annotations

from fastapi import APIRouter, Depends

from app.routers.deps import get_current_user
from app.services.celery_client import trigger_pipeline


router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.post("/run")
def run_scheduler(user=Depends(get_current_user)) -> dict:
    return {"triggered": trigger_pipeline()}
