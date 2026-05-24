"""Slack Events API webhook — receive event, run AI, reply via chat.postMessage."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.engine import process_message
from app.channels.slack_adapter import SlackAdapter
from app.models.ai_config import AIConfig
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.models.message import Message

SLACK_CONTACT_PREFIX = "slack_channel:"


def slack_contact_info(channel_id: str) -> str:
    return f"{SLACK_CONTACT_PREFIX}{channel_id}"


async def handle_slack_webhook(
    channel: Channel,
    *,
    body: bytes,
    client_ip: str | None,
    db: AsyncSession,
) -> dict[str, Any]:
    """Process Slack event and reply via chat.postMessage."""
    adapter = SlackAdapter()
    config = channel.config or {}

    try:
        msg = await adapter.parse_message(body, {})
    except Exception as e:
        logger.error(f"Slack parse failed: {e}", exc_info=True)
        return {"ok": True}

    # Handle URL verification challenge
    if msg.msg_type == "event" and msg.event == "url_verification":
        return {"challenge": msg.raw.get("challenge", "")}

    if not msg.content.strip():
        return {"ok": True}

    customer_id = str(config.get("customer_id") or "").strip()
    if not customer_id:
        await adapter.send_reply(config, msg.sender_id,
                                "This bot is not yet linked to a customer agent.")
        return {"ok": True}

    result = await db.execute(
        select(CustomerConfig).where(CustomerConfig.id == customer_id, CustomerConfig.enabled == True)
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        await adapter.send_reply(config, msg.sender_id, "Linked customer config not found.")
        return {"ok": True}

    import json
    try:
        ids = json.loads(msg.sender_id)
        sender_user = ids.get("user", msg.sender_id)
    except (json.JSONDecodeError, TypeError):
        sender_user = msg.sender_id

    conversation = await _get_or_create_conversation(db, channel.id, sender_user, customer, client_ip)

    user_message = Message(
        id=str(uuid.uuid4()), conversation_id=conversation.id, role="user", content=msg.content,
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
        await db.rollback()
        await adapter.send_reply(config, msg.sender_id, "Message received. Processing...")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Slack AI reply failed: {e}", exc_info=True)
        await db.rollback()
        return {"ok": True}

    reply = (full_response or "").strip() or "Sorry, I cannot reply right now."
    try:
        await adapter.send_reply(config, msg.sender_id, reply)
    except Exception as e:
        logger.error(f"Slack send failed: {e}", exc_info=True)
    return {"ok": True}


async def _get_or_create_conversation(
    db: AsyncSession, channel_id: str, sender_id: str, customer: CustomerConfig, client_ip: str | None
) -> Conversation:
    contact = slack_contact_info(channel_id)
    result = await db.execute(
        select(Conversation)
        .where(Conversation.visitor_id == sender_id, Conversation.contact_info == contact,
               Conversation.status == "active")
        .order_by(Conversation.updated_at.desc()).limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        return conversation

    conversation = Conversation(
        id=str(uuid.uuid4()), visitor_id=sender_id, client_ip=client_ip,
        ai_config_id=customer.ai_config_id, title=f"Slack: {customer.name}",
        contact_info=contact, status="active",
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
