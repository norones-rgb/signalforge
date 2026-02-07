from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountSettingsBase(BaseModel):
    timezone: str = "UTC"
    daily_post_min: int = 1
    daily_post_max: int = 3
    allowed_hours: list[int] = Field(default_factory=list)
    min_spacing_hours: int = 2
    allow_links: bool = False
    link_post_ratio: float = 0.0
    thread_ratio: float = 0.2
    max_thread_len: int = 5
    format_weights: dict = Field(default_factory=dict)
    topic_weights: dict = Field(default_factory=dict)


class AccountSettingsCreate(AccountSettingsBase):
    pass


class AccountSettingsUpdate(AccountSettingsBase):
    pass


class AccountSettingsResponse(AccountSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    x_account_id: UUID


class XAccountCreate(BaseModel):
    workspace_id: UUID
    handle: str
    name: str | None = None
    is_enabled: bool = True
    oauth_access_token: str | None = None
    oauth_refresh_token: str | None = None
    oauth_expires_at: datetime | None = None
    settings: AccountSettingsCreate | None = None


class XAccountUpdate(BaseModel):
    name: str | None = None
    handle: str | None = None
    is_enabled: bool | None = None
    oauth_access_token: str | None = None
    oauth_refresh_token: str | None = None
    oauth_expires_at: datetime | None = None
    settings: AccountSettingsUpdate | None = None


class XAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    handle: str
    name: str | None
    is_enabled: bool
    oauth_expires_at: datetime | None
    is_connected: bool = False
    settings: AccountSettingsResponse | None = None

