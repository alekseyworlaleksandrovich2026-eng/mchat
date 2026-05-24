"""Schemas for uploaded local embedding models."""

from datetime import datetime

from pydantic import BaseModel, Field


class EmbeddingModelResponse(BaseModel):
    id: str
    user_id: str
    name: str
    status: str
    dimension: int
    file_size: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmbeddingModelUploadResponse(BaseModel):
    model: EmbeddingModelResponse
    message: str = ""
