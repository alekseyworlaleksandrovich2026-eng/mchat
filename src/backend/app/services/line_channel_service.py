"""LINE Messaging API webhook — receive message, run AI, reply via reply API."""

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
from app.channels.line_adapter import LineAdapter
from app.models.channel import Channel
from app.models.customer import CustomerConfig
from app.models.message import Message
from app.services.channel_service import (
    channel_get_or_create_conversation,
    channel_resolve_ai_config,
)

LINE_CONTACT_PREFIX = "line_channel:"


def line_contact_info(channel_id: str) -> str:
    return f"{LINE_CONTACT_PREFIX}{channel_id}"


async def handle_line_webhook(
    channel: Channel,
    *,
    body: bytes,
    signature_header: str,
    client_ip: str | None,
    db: AsyncSession,
) -> dict[str, Any]:
    """Process LINE webhook event and reply via reply API."""
    adapter = LineAdapter()
    config = channel.config or {}
    channel_secret = str(config.get("channel_secret") or "")

    if not adapter._verify_signature(body, channel_secret, signature_header):
        raise HTTPException(status_code=403, detail="Invalid LINE signature")

    try:
        msg = await adapter.parse_message(body, {})
    except Exception as e:
        logger.error(f"LINE parse failed: {e}", exc_info=True)
        return {"ok": True}

    if msg.msg_type == "event":
        if msg.event == "follow":
            customer_id = str(config.get("customer_id") or "").strip()
            welcome = await _welcome_for_customer(customer_id, db)
            reply_text = welcome or "Welcome! Send a message to start chatting."
            try:
                await adapter.send_reply(config, msg.sender_id, reply_text)
            except Exception as e:
                logger.error(f"LINE follow reply failed: {e}", exc_info=True)
        return {"ok": True}

    content = msg.content.strip()
    if not content:
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

    conversation = await channel_get_or_create_conversation(
        db, msg.sender_id, customer,
        contact_info=line_contact_info(channel.id),
        title=f"LINE: {customer.name}",
        client_ip=client_ip,
    )

    user_message = Message(
        id=str(uuid.uuid4()), conversation_id=conversation.id, role="user", content=content,
    )
    db.add(user_message)
    await db.flush()
    conversation.updated_at = datetime.now(timezone.utc)
    conversation.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    async def _generate_reply() -> str:
        full = ""
        async for token in process_message(conversation, user_message, await channel_resolve_ai_config(db, customer), db,
                                           customer_config=customer):
            full += token
        return full

    try:
        full_response = await asyncio.wait_for(_generate_reply(), timeout=10.0)
        await db.commit()
    except asyncio.TimeoutError:
        await db.rollback()
        await adapter.send_reply(config, msg.sender_id, "Message received. Processing...")
        return {"ok": True}
    except Exception as e:
        logger.error(f"LINE AI reply failed: {e}", exc_info=True)
        await db.rollback()
        return {"ok": True}

    reply = (full_response or "").strip() or "Sorry, I cannot reply right now."
    try:
        await adapter.send_reply(config, msg.sender_id, reply)
    except Exception as e:
        logger.error(f"LINE send failed: {e}", exc_info=True)

    return {"ok": True}


async def _welcome_for_customer(customer_id: str, db: AsyncSession) -> str | None:
    if not customer_id:
        return None
    result = await db.execute(select(CustomerConfig).where(CustomerConfig.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer and customer.welcome_message:
        return customer.welcome_message.strip()
    return None
