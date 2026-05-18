"""Knowledge management Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Request body for creating a knowledge base."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    enabled: bool = True


class KnowledgeBaseResponse(BaseModel):
    """Knowledge base response schema."""
    id: str
    user_id: str
    name: str
    description: str | None = None
    enabled: bool
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    """Document summary for list/upload responses (no full content)."""
    id: str
    knowledge_base_id: str
    title: str
    source: str | None = None
    status: str
    chunk_count: int
    file_size: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    """Request body for creating a document."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str | None = None
    source_url: str | None = None


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    knowledge_base_id: str
    title: str
    content: str
    source: str | None = None
    source_url: str | None = None
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    """Search query request."""
    query: str = Field(..., min_length=1, max_length=1000)
    knowledge_base_id: str | None = None
    top_k: int = Field(5, ge=1, le=50)


class SearchResult(BaseModel):
    """Single search result."""
    document_id: str
    title: str
    content: str
    score: float
    knowledge_base_id: str


class SearchResponse(BaseModel):
    """Search results response."""
    results: list[SearchResult]
    total: int
