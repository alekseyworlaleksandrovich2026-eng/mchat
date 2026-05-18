"""User model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="agent"
    )  # admin, agent
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    ai_configs = relationship(
        "AIConfig", back_populates="user", lazy="selectin"
    )
    conversations = relationship(
        "Conversation", back_populates="user", lazy="selectin"
    )
    messages = relationship("Message", back_populates="user", lazy="selectin")
    skills = relationship("Skill", back_populates="user", lazy="selectin")
    knowledge_bases = relationship(
        "KnowledgeBase", back_populates="user", lazy="selectin"
    )
    customer_configs = relationship(
        "CustomerConfig", back_populates="user", lazy="selectin"
    )
    webhook_configs = relationship(
        "WebhookConfig", back_populates="user", lazy="selectin"
    )
    channels = relationship(
        "Channel", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
