"""LINE Messaging API — webhook verification, message parsing, reply sending."""

from __future__ import annotations

import hashlib
import hmac
import json
from base64 import b64decode
from typing import Any

import httpx

from app.channels.base_adapter import BaseChannelAdapter, ChannelMessage


class LineAdapter(BaseChannelAdapter):
    """Adapter for LINE Messaging API webhooks."""

    def _verify_signature(self, body: bytes, channel_secret: str, signature_header: str) -> bool:
        if not channel_secret or not signature_header:
            return False
        mac = hmac.new(
            channel_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        )
        digest = b64decode(signature_header)
        return hmac.compare_digest(mac.digest(), digest)

    async def verify_webhook(self, query_params: dict[str, str]) -> str | None:
        return None

    async def parse_message(self, body: bytes, query_params: dict[str, str]) -> ChannelMessage:
        payload = json.loads(body)

        events = payload.get("events", [])
        if not events:
            raise ValueError("No events in LINE payload")

        event = events[0]
        event_type = event.get("type", "")

        if event_type == "message":
            msg = event.get("message", {})
            msg_type = msg.get("type", "text")
            content = msg.get("text", "")
            return ChannelMessage(
                sender_id=event.get("replyToken", ""),
                content=content,
                msg_type=msg_type,
                raw=payload,
            )

        if event_type == "follow":
            return ChannelMessage(
                sender_id=event.get("replyToken", ""),
                content="",
                msg_type="event",
                event="follow",
                raw=payload,
            )

        if event_type == "unfollow":
            return ChannelMessage(
                sender_id="",
                content="",
                msg_type="event",
                event="unfollow",
                raw=payload,
            )

        raise ValueError(f"Unsupported LINE event: {event_type}")

    async def send_reply(self, channel_config: dict[str, Any], sender_id: str, text: str) -> None:
        channel_access_token = (channel_config.get("channel_access_token") or "").strip()
        if not channel_access_token:
            raise ValueError("LINE channel_access_token is required")

        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Authorization": f"Bearer {channel_access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "replyToken": sender_id,
                "messages": [{"type": "text", "text": text[:5000]}],
            }, headers=headers)
            resp.raise_for_status()

    async def validate_config(self, channel_config: dict[str, Any]) -> bool:
        token = (channel_config.get("channel_access_token") or "").strip()
        secret = (channel_config.get("channel_secret") or "").strip()
        return bool(token and secret)
