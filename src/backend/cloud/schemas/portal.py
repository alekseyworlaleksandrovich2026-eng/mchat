"""Portal schemas — user-facing channel rental API."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChannelTemplateResponse(BaseModel):
    """Published channel template shown in the marketplace."""

    id: str
    name: str
    description: str | None = None
    category: str
    icon: str | None = None
    price_monthly_cents: int = 0
    price_yearly_cents: int = 0
    trial_days: int = 14
    default_theme: dict | None = None
    default_welcome_message: str | None = None
    default_offline_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RentChannelRequest(BaseModel):
    """Request to provision a channel from a template."""

    template_id: str = Field(..., min_length=1)
    name: str | None = Field(None, max_length=200)


class MyChannelResponse(BaseModel):
    """User's channel summary with usage stats."""

    id: str
    name: str
    short_code: str | None = None
    channel_category: str
    template_id: str | None = None
    plan: str
    trial_ends_at: datetime | None = None
    enabled: bool
    welcome_message: str | None = None
    offline_message: str | None = None
    theme: dict | None = None
    # Usage stats
    usage_messages_month: int = 0
    usage_tokens_month: int = 0
    usage_messages_limit: int = 1000
    usage_tokens_limit: int = 100000
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MyChannelUpdate(BaseModel):
    """User-facing channel settings update."""

    name: str | None = Field(None, max_length=200)
    welcome_message: str | None = None
    offline_message: str | None = None
    theme: dict | None = None
    enabled: bool | None = None


class EmbedCodeResponse(BaseModel):
    """Widget embed code for a channel."""

    agent_id: str
    embed_script: str
    widget_url: str


class PortalDashboardStats(BaseModel):
    """Dashboard stats for the portal."""

    total_channels: int = 0
    active_channels: int = 0
    total_conversations: int = 0
    messages_today: int = 0
    # Aggregated usage across all channels
    total_messages_month: int = 0
    total_tokens_month: int = 0
    plan: str | None = None
    trial_ends_at: datetime | None = None
