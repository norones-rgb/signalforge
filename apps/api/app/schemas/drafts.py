from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    x_account_id: UUID | None
    idea_id: UUID | None
    content: str
    format: str
    is_thread: bool
    thread_count: int
    score: float
    status: str
    created_at: datetime
