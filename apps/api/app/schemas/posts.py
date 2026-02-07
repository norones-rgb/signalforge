from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    x_account_id: UUID
    draft_id: UUID | None
    x_post_id: str | None
    x_post_url: str | None
    posted_at: datetime | None
    is_thread: bool
    status: str
    created_at: datetime
