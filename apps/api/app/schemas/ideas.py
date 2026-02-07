from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    x_account_id: UUID | None
    source_id: UUID | None
    title: str | None
    summary: str | None
    url: str | None
    published_at: datetime | None
    score: float
    status: str
    created_at: datetime
