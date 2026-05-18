"""Agent configuration Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AIConfigCreate(BaseModel):
    """Request body for creating an AI config."""
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field("", max_length=500)
    api_base: str | None = Field(None, max_length=500)
    system_prompt: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=131072)
    is_default: bool = False


class AIConfigUpdate(BaseModel):
    """Request body for updating an AI config."""
    name: str | None = Field(None, min_length=1, max_length=100)
    provider: str | None = Field(None, max_length=50)
    model: str | None = Field(None, min_length=1, max_length=100)
    api_key: str | None = Field(None, min_length=1, max_length=500)
    api_base: str | None = Field(None, max_length=500)
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=131072)
    is_default: bool | None = None


class AIConfigResponse(BaseModel):
    """AI config response schema."""
    id: str
    user_id: str
    name: str
    provider: str
    model: str
    api_base: str | None = None
    system_prompt: str | None = None
    temperature: float
    max_tokens: int
    is_default: bool
    created_at: datetime
    updated_at: datetime
    api_key: str  # Return full key for admin panel display

    model_config = {"from_attributes": True}


class CustomerConfigCreate(BaseModel):
    """Request body for creating a customer config."""
    name: str = Field(..., min_length=1, max_length=200)
    ai_config_id: str | None = None
    skill_ids: list[str] | None = None
    knowledge_base_ids: list[str] | None = None
    welcome_message: str | None = None
    offline_message: str | None = None
    theme: dict | None = None
    domains: str | None = None
    position: str = Field("right", pattern=r"^(left|right)$")
    enabled: bool = True
    widget_session_ttl_hours: int = Field(
        24, ge=0, le=24 * 365, description="0 = never expire by time"
    )


class ModelCatalogRequest(BaseModel):
    """Probe provider API to list models."""
    provider: str = Field(..., min_length=1, max_length=50)
    api_key: str = Field("", max_length=500)
    api_base: str | None = Field(None, max_length=500)
    config_id: str | None = None


class ModelCatalogResponse(BaseModel):
    models: list[str]


class ConnectionTestRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    api_key: str = Field("", max_length=500)
    api_base: str | None = Field(None, max_length=500)
    model: str | None = Field(None, max_length=100)
    config_id: str | None = None


class ConnectionTestResponse(BaseModel):
    ok: bool
    message: str


class CustomerConfigResponse(BaseModel):
    """Customer config response schema."""
    id: str
    name: str
    user_id: str
    ai_config_id: str | None = None
    skill_ids: list[str] | None = None
    knowledge_base_ids: list[str] | None = None
    welcome_message: str | None = None
    offline_message: str | None = None
    theme: dict | None = None
    domains: str | None = None
    position: str
    enabled: bool
    widget_session_ttl_hours: int = 24
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
