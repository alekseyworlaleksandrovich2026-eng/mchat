"""WeChat Official Account webhook — message in, AI reply out."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.engine import process_message
from app.channels.wechat_adapter import (
    build_text_reply,
    encrypt_reply_xml,
    parse_incoming,
    verify_signature,
)
from app.models.ai_config import AIConfig
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.models.message import Message

WECHAT_CONTACT_PREFIX = "wechat_channel:"


def wechat_contact_info(channel_id: str) -> str:
    return f"{WECHAT_CONTACT_PREFIX}{channel_id}"


async def handle_wechat_webhook(
    channel: Channel,
    *,
    body: bytes,
    signature: str,
    timestamp: str,
    nonce: str,
    encrypt_type: str | None,
    msg_signature: str | None,
    db: AsyncSession,
) -> str:
    """Process WeChat push and return XML response body (plaintext or encrypted)."""
    config = channel.config or {}
    token = str(config.get("token") or "")
    app_id = str(config.get("app_id") or "")
    encoding_aes_key = str(config.get("encoding_aes_key") or "")

    if not verify_signature(token, timestamp, nonce, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        parsed = parse_incoming(
            body,
            token=token,
            app_id=app_id,
            encoding_aes_key=encoding_aes_key,
            encrypt_type=encrypt_type,
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
        )
    except Exception as e:
        logger.error(f"WeChat parse failed: {e}", exc_info=True)
        return "success"

    to_user = parsed.get("from_user", "")
    from_user = parsed.get("to_user", "")
    msg_type = parsed.get("msg_type", "")

    if not to_user or not from_user:
        logger.warning(f"WeChat message missing addresses: {parsed}")
        return "success"

    reply_text = await _dispatch_message(
        channel, parsed, db, openid=to_user
    )

    if not reply_text:
        return "success"

    return _wrap_reply(
        channel,
        parsed_fallback_to=to_user,
        to_user=to_user,
        from_user=from_user,
        content=reply_text,
        encrypt_type=encrypt_type,
        encoding_aes_key=encoding_aes_key,
        app_id=app_id,
        token=token,
        timestamp=timestamp,
        nonce=nonce,
    )


def _wrap_reply(
    channel: Channel,
    *,
    parsed_fallback_to: str,
    to_user: str,
    from_user: str,
    content: str,
    encrypt_type: str | None,
    encoding_aes_key: str,
    app_id: str,
    token: str,
    timestamp: str,
    nonce: str,
) -> str:
    if not to_user and parsed_fallback_to:
        to_user = parsed_fallback_to
    reply_xml = build_text_reply(to_user, from_user, content)
    if encrypt_type == "aes" and encoding_aes_key and app_id:
        return encrypt_reply_xml(
            reply_xml,
            token=token,
            encoding_aes_key=encoding_aes_key,
            app_id=app_id,
            timestamp=timestamp,
            nonce=nonce,
        )
    return reply_xml


async def _dispatch_message(
    channel: Channel,
    parsed: dict[str, str],
    db: AsyncSession,
    *,
    openid: str,
) -> str:
    msg_type = parsed.get("msg_type", "")
    config = channel.config or {}
    customer_id = str(config.get("customer_id") or "").strip()

    if msg_type == "event":
        event = (parsed.get("event") or "").lower()
        if event == "subscribe":
            welcome = await _welcome_for_customer(customer_id, db)
            return welcome or "欢迎关注！直接发送文字即可开始对话。"
        return ""

    if msg_type == "text":
        text = (parsed.get("content") or "").strip()
        if not text:
            return ""
        return await _process_text_message(
            channel, customer_id, openid, text, db
        )

    if msg_type in ("image", "voice", "video", "shortvideo", "location", "link"):
        return "暂仅支持文字消息，请直接输入您的问题。"

    return ""


async def _welcome_for_customer(
    customer_id: str, db: AsyncSession
) -> str | None:
    if not customer_id:
        return None
    result = await db.execute(
        select(CustomerConfig).where(CustomerConfig.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if customer and customer.welcome_message:
        return customer.welcome_message.strip()
    return None


async def _process_text_message(
    channel: Channel,
    customer_id: str,
    openid: str,
    text: str,
    db: AsyncSession,
) -> str:
    if not customer_id:
        return (
            "公众号尚未绑定客服 Agent。请在 mchat 管理后台 → 频道管理 → "
            "编辑此微信公众号，选择「客服配置（Agent）」。"
        )

    result = await db.execute(
        select(CustomerConfig).where(
            CustomerConfig.id == customer_id,
            CustomerConfig.enabled == True,
        )
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        return "绑定的客服配置不存在或已禁用，请联系管理员。"

    if customer.user_id != channel.user_id:
        return "客服配置与频道不属于同一账号，请重新绑定。"

    conversation = await _get_or_create_conversation(
        db,
        channel_id=channel.id,
        openid=openid,
        customer=customer,
    )

    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=text,
    )
    db.add(user_message)
    await db.flush()

    ai_config = await _resolve_ai_config(db, customer)

    if ai_config is None:
        return "未配置 AI 模型，请在管理后台设置默认模型或绑定客服 Agent 的模型。"

    full_response = ""
    try:
        async for token in process_message(
            conversation,
            user_message,
            ai_config,
            db,
            customer_config=customer,
        ):
            full_response += token
        await db.commit()
    except Exception as e:
        logger.error(f"WeChat AI reply failed: {e}", exc_info=True)
        await db.rollback()
        return f"处理消息时出错：{e}"

    reply = (full_response or "").strip()
    if not reply:
        return "抱歉，我暂时无法回复，请稍后再试。"
    if len(reply) > 2000:
        reply = reply[:1997] + "..."
    return reply


async def _get_or_create_conversation(
    db: AsyncSession,
    *,
    channel_id: str,
    openid: str,
    customer: CustomerConfig,
) -> Conversation:
    contact = wechat_contact_info(channel_id)
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.visitor_id == openid,
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
        visitor_id=openid,
        ai_config_id=customer.ai_config_id,
        title=f"WeChat: {customer.name}",
        contact_info=contact,
        status="active",
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _resolve_ai_config(
    db: AsyncSession, customer: CustomerConfig
) -> AIConfig | None:
    if customer.ai_config_id:
        result = await db.execute(
            select(AIConfig).where(AIConfig.id == customer.ai_config_id)
        )
        cfg = result.scalar_one_or_none()
        if cfg is not None:
            return cfg
    result = await db.execute(
        select(AIConfig).where(AIConfig.is_default == True)
    )
    return result.scalar_one_or_none()
