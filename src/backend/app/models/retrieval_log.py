"""Retrieval observability — per-search audit rows."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    conversation_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="chat")
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_variant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    retrieval_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="hybrid")
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zero_result: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hits_summary: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
