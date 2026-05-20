"""Chat-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Request body for sending a chat message."""
    conversation_id: str | None = Field(None, description="Existing conversation ID")
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field("user", pattern=r"^(user|assistant|system)$")
    extra_data: dict | None = Field(None, description="Optional message metadata such as attachments or outbound assets")


class MessageResponse(BaseModel):
    """Message response schema."""
    id: str
    conversation_id: str
    role: str
    content: str
    extra_data: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    id: str
    title: str | None = None
    status: str
    conversation_type: str = "chat"
    first_user_message_preview: str | None = None
    visitor_id: str | None = None
    client_ip: str | None = None
    contact_info: str | None = None
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime
    user_message_count: int = 0
    ai_message_count: int = 0
    total_message_count: int = 0
    messages: list[MessageResponse] | None = None

    model_config = {"from_attributes": True}


class ConversationList(BaseModel):
    """Paginated conversation list."""
    items: list[ConversationResponse]
    total: int


class ConversationStatsResponse(BaseModel):
    """Conversation aggregate stats."""
    total: int
    active: int
    closed: int


class InitConversationRequest(BaseModel):
    """Initialize a visitor conversation."""
    visitor_id: str | None = Field(None, max_length=100)
    title: str | None = Field(None, max_length=200)
    ai_config_id: str | None = None
    contact_info: str | None = None


class CreateConversationRequest(BaseModel):
    """Request body for creating a conversation (admin)."""
    title: str | None = Field(None, max_length=200)
    ai_config_id: str | None = None
    visitor_id: str | None = Field(None, max_length=100)
