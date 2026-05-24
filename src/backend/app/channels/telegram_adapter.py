"""Telegram Bot API — webhook verification, message parsing, reply sending."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.channels.base_adapter import BaseChannelAdapter, ChannelMessage


class TelegramAdapter(BaseChannelAdapter):
    """Adapter for Telegram Bot API webhooks."""

    async def verify_webhook(self, query_params: dict[str, str]) -> str | None:
        """No Telegram-specific verification needed at webhook level.
        Bot token is validated on send, not on receive."""
        return None

    async def parse_message(self, body: bytes, query_params: dict[str, str]) -> ChannelMessage:
        payload = json.loads(body)

        if "message" in payload:
            msg = payload["message"]
            chat = msg.get("chat", {})
            sender_id = str(chat.get("id", ""))
            text = msg.get("text") or msg.get("caption") or ""
            return ChannelMessage(
                sender_id=sender_id,
                content=text,
                msg_type="text",
                raw=payload,
            )

        if "callback_query" in payload:
            cb = payload["callback_query"]
            sender_id = str(cb.get("from", {}).get("id", ""))
            data = cb.get("data", "")
            return ChannelMessage(
                sender_id=sender_id,
                content=data,
                msg_type="callback",
                raw=payload,
            )

        if "my_chat_member" in payload:
            chat = payload["my_chat_member"].get("chat", {})
            return ChannelMessage(
                sender_id=str(chat.get("id", "")),
                content="",
                msg_type="event",
                event=payload["my_chat_member"].get("new_chat_member", {}).get("status", ""),
                raw=payload,
            )

        raise ValueError(f"Unsupported Telegram update type: {list(payload.keys())}")

    async def send_reply(self, channel_config: dict[str, Any], sender_id: str, text: str) -> None:
        token = (channel_config.get("bot_token") or "").strip()
        if not token:
            raise ValueError("Telegram bot_token is required")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "chat_id": sender_id,
                "text": text[:4096],
                "parse_mode": "Markdown",
            })
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Telegram sendMessage failed: {data.get('description')}")

    async def validate_config(self, channel_config: dict[str, Any]) -> bool:
        token = (channel_config.get("bot_token") or "").strip()
        return bool(token)
