"""Channel management Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    """Create a new channel."""
    name: str = Field(..., min_length=1, max_length=100)
    channel_type: str = Field(
        ..., pattern=r"^(web_widget|wechat|dingtalk|whatsapp|telegram|slack|line|custom)$"
    )
    config: dict | None = None
    enabled: bool = False


class ChannelUpdate(BaseModel):
    """Update an existing channel."""
    name: str | None = Field(None, min_length=1, max_length=100)
    config: dict | None = None
    enabled: bool | None = None


class ChannelResponse(BaseModel):
    """Channel response."""
    id: str
    user_id: str
    name: str
    channel_type: str
    config: dict | None = None
    enabled: bool
    is_connected: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChannelTestRequest(BaseModel):
    """Test a channel connection."""
    channel_type: str
    config: dict
