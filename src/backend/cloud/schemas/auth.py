"""Auth schemas for Cloud (multi-tenant SaaS layer)."""

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Request body for public user signup."""

    username: str = Field(
        ..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_]+$"
    )
    email: str | None = Field(None, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    display_name: str | None = Field(None, max_length=100)
