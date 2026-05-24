"""DingTalk Open API — webhook verification, message parsing, reply sending."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from base64 import b64decode, b64encode
from typing import Any
from urllib.parse import quote

import httpx

from app.channels.base_adapter import BaseChannelAdapter, ChannelMessage


class DingTalkAdapter(BaseChannelAdapter):
    """Adapter for DingTalk robot webhooks (outgoing message pattern)."""

    async def verify_webhook(self, query_params: dict[str, str]) -> str | None:
        return None

    async def parse_message(
        self, body: bytes, query_params: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> ChannelMessage:
        payload = json.loads(body)

        sender_id = payload.get("senderId") or payload.get("senderStaffId") or ""
        content = payload.get("text", {}).get("content", "") if isinstance(payload.get("text"), dict) else ""

        conversation_type = payload.get("conversationType", "")
        conversation_id = payload.get("conversationId") or payload.get("conversationTitle", "")

        return ChannelMessage(
            sender_id=json.dumps({
                "sender": str(sender_id),
                "conversation": str(conversation_id),
                "type": conversation_type,
                "sessionWebhook": payload.get("sessionWebhook", ""),
            }),
            content=content,
            msg_type="text",
            raw=payload,
        )

    async def send_reply(self, channel_config: dict[str, Any], sender_id: str, text: str) -> None:
        try:
            ids = json.loads(sender_id)
            session_webhook = ids.get("sessionWebhook", "")
        except (json.JSONDecodeError, TypeError):
            session_webhook = ""

        if not session_webhook:
            webhook_url = (channel_config.get("webhook_url") or "").strip()
        else:
            webhook_url = session_webhook

        if not webhook_url:
            raise ValueError("DingTalk webhook_url is required")

        payload = {
            "msgtype": "text",
            "text": {"content": text[:20000]},
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode", -1) != 0:
                raise RuntimeError(f"DingTalk send failed: {data.get('errmsg')}")

    async def validate_config(self, channel_config: dict[str, Any]) -> bool:
        webhook = (channel_config.get("webhook_url") or "").strip()
        return bool(webhook)
