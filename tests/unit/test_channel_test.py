"""Tests for channel connectivity checks."""

import pytest

from app.models.customer import CustomerConfig
from app.services.channel_service import ChannelService


@pytest.mark.asyncio
async def test_telegram_requires_customer_id(db_session):
    user_id = "user-1"
    db_session.add(
        CustomerConfig(
            id="cust-1",
            name="Support",
            user_id=user_id,
            enabled=True,
        )
    )
    await db_session.flush()

    service = ChannelService(db_session)
    result = await service.test_channel(
        user_id,
        "telegram",
        {"bot_token": "fake-token", "customer_id": "cust-1"},
    )
    assert result["ok"] is False
    assert "Telegram" in result["message"]


@pytest.mark.asyncio
async def test_dingtalk_validates_binding(db_session):
    user_id = "user-1"
    db_session.add(
        CustomerConfig(
            id="cust-2",
            name="DingTalk Agent",
            user_id=user_id,
            enabled=True,
        )
    )
    await db_session.flush()

    service = ChannelService(db_session)
    result = await service.test_channel(
        user_id,
        "dingtalk",
        {
            "customer_id": "cust-2",
            "app_secret": "secret",
        },
    )
    assert result["ok"] is True
    assert "DingTalk Agent" in result["message"]
