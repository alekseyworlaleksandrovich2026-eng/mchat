"""Telegram webhook — receive message, run AI, reply via Bot API."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.engine import process_message
from app.channels.telegram_adapter import TelegramAdapter
from app.models.ai_config import AIConfig
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.models.message import Message

TELEGRAM_CONTACT_PREFIX = "telegram_channel:"


def telegram_contact_info(channel_id: str) -> str:
    return f"{TELEGRAM_CONTACT_PREFIX}{channel_id}"


async def handle_telegram_webhook(
    channel: Channel,
    *,
    body: bytes,
    client_ip: str | None,
    db: AsyncSession,
) -> dict[str, Any]:
    """Process Telegram webhook update and return empty 200 (async reply via sendMessage)."""
    adapter = TelegramAdapter()
    config = channel.config or {}

    try:
        msg = await adapter.parse_message(body, {})
    except Exception as e:
        logger.error(f"Telegram parse failed: {e}", exc_info=True)
        return {"ok": True}

    if msg.msg_type == "event":
        return {"ok": True}

    content = msg.content.strip()
    if not content:
        return {"ok": True}

    customer_id = str(config.get("customer_id") or "").strip()
    if not customer_id:
        await adapter.send_reply(config, msg.sender_id,
                                "This bot is not yet linked to a customer agent. Please configure it in the admin panel.")
        return {"ok": True}

    result = await db.execute(
        select(CustomerConfig).where(
            CustomerConfig.id == customer_id,
            CustomerConfig.enabled == True,
        )
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        await adapter.send_reply(config, msg.sender_id,
                                "Linked customer config not found or disabled.")
        return {"ok": True}

    conversation = await _get_or_create_conversation(db, channel.id, msg.sender_id, customer, client_ip)

    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    await db.flush()
    conversation.updated_at = datetime.now(timezone.utc)
    conversation.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    async def _generate_reply() -> str:
        full = ""
        async for token in process_message(conversation, user_message, await _resolve_ai_config(db, customer), db,
                                           customer_config=customer):
            full += token
        return full

    try:
        full_response = await asyncio.wait_for(_generate_reply(), timeout=15.0)
        await db.commit()
    except asyncio.TimeoutError:
        logger.warning(f"Telegram reply timeout: channel={channel.id} sender={msg.sender_id}")
        await db.rollback()
        await adapter.send_reply(config, msg.sender_id, "Message received. Processing, please wait...")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram AI reply failed: {e}", exc_info=True)
        await db.rollback()
        await adapter.send_reply(config, msg.sender_id, f"Error processing message: {e}")
        return {"ok": True}

    reply_text = (full_response or "").strip() or "Sorry, I cannot reply right now."
    try:
        await adapter.send_reply(config, msg.sender_id, reply_text)
    except Exception as e:
        logger.error(f"Telegram send failed: {e}", exc_info=True)

    return {"ok": True}


async def _get_or_create_conversation(
    db: AsyncSession,
    channel_id: str,
    sender_id: str,
    customer: CustomerConfig,
    client_ip: str | None,
) -> Conversation:
    contact = telegram_contact_info(channel_id)
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.visitor_id == sender_id,
            Conversation.contact_info == contact,
            Conversation.status == "active",
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        return conversation

    conversation = Conversation(
        id=str(uuid.uuid4()),
        visitor_id=sender_id,
        client_ip=client_ip,
        ai_config_id=customer.ai_config_id,
        title=f"Telegram: {customer.name}",
        contact_info=contact,
        status="active",
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _resolve_ai_config(db: AsyncSession, customer: CustomerConfig) -> AIConfig | None:
    if customer.ai_config_id:
        result = await db.execute(select(AIConfig).where(AIConfig.id == customer.ai_config_id))
        cfg = result.scalar_one_or_none()
        if cfg is not None:
            return cfg
    result = await db.execute(select(AIConfig).where(AIConfig.is_default == True))
    return result.scalar_one_or_none()
