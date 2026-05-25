"""Portal checkout orders (channel template purchase)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PortalOrder(Base):
    __tablename__ = "portal_orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    channel_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    billing_period: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )  # monthly | yearly
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | paid | failed | cancelled
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    provider_trade_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
