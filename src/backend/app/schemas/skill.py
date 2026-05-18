"""Skill-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SkillResponse(BaseModel):
    """Skill response schema."""
    id: str
    name: str
    description: str | None = None
    skill_type: str
    path: str | None = None
    config: dict | None = None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillUpdate(BaseModel):
    """Request body for updating a skill."""
    enabled: bool | None = None
    config: dict | None = None
    name: str | None = Field(None, max_length=100)
    description: str | None = None
