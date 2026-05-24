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
from app.models.channel import Channel
from app.models.customer import CustomerConfig
from app.models.message import Message
from app.services.channel_service import (
    channel_get_or_create_conversation,
    channel_resolve_ai_config,
)

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

    conversation = await channel_get_or_create_conversation(
        db, sender_user, customer,
        contact_info=slack_contact_info(channel.id),
        title=f"Slack: {customer.name}",
        client_ip=client_ip,
    )

    user_message = Message(
        id=str(uuid.uuid4()), conversation_id=conversation.id, role="user", content=msg.content,
    )
    db.add(user_message)
    await db.flush()
    conversation.updated_at = datetime.now(timezone.utc)
    conversation.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    ai_config = await channel_resolve_ai_config(db, customer)

    async def _generate_reply() -> str:
        full = ""
        async for token in process_message(
            conversation, user_message, ai_config, db, customer_config=customer
        ):
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
