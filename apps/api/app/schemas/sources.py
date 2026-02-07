from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceCreate(BaseModel):
    workspace_id: UUID
    x_account_id: UUID | None = None
    type: str = "rss"
    url: str
    is_enabled: bool = True


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    x_account_id: UUID | None
    type: str
    url: str
    is_enabled: bool
    last_ingested_at: datetime | None
