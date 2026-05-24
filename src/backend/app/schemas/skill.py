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


class SkillInstallUrlRequest(BaseModel):
    """Request body for installing a skill from URL."""
    url: str = Field(..., min_length=8, max_length=2000)
    name: str | None = Field(None, max_length=100)


class SkillCreate(BaseModel):
    """Request body for creating a new skill."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    skill_type: str = Field(default="tool", pattern=r"^(tool|function|webhook)$")


class SkillCatalogItem(BaseModel):
    """Remote skill catalog item."""
    name: str
    title: str
    description: str | None = None
    source: str = "clawhub"
    homepage: str | None = None
    download_url: str | None = None


class SkillCatalogResponse(BaseModel):
    """Catalog list response."""
    source: str = "clawhub"
    items: list[SkillCatalogItem]
