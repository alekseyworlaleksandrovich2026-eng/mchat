"""Slack Events API — webhook verification, message parsing, reply sending."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.channels.base_adapter import BaseChannelAdapter, ChannelMessage


class SlackAdapter(BaseChannelAdapter):
    """Adapter for Slack Events API webhooks."""

    async def verify_webhook(self, query_params: dict[str, str]) -> str | None:
        return None

    async def parse_message(self, body: bytes, query_params: dict[str, str]) -> ChannelMessage:
        payload = json.loads(body)

        # URL verification challenge
        if payload.get("type") == "url_verification":
            return ChannelMessage(
                sender_id="",
                content="",
                msg_type="event",
                event="url_verification",
                raw=payload,
            )

        # Event callback
        event = payload.get("event", {})
        event_type = event.get("type", "")

        if event_type == "message" and event.get("subtype") != "bot_message":
            sender_id = event.get("user", "")
            channel_id = event.get("channel", "")
            text = event.get("text", "")
            return ChannelMessage(
                sender_id=json.dumps({"user": sender_id, "channel": channel_id}),
                content=text,
                msg_type="text",
                raw=payload,
            )

        if event_type == "app_mention":
            sender_id = event.get("user", "")
            channel_id = event.get("channel", "")
            text = event.get("text", "")
            return ChannelMessage(
                sender_id=json.dumps({"user": sender_id, "channel": channel_id}),
                content=text,
                msg_type="text",
                raw=payload,
            )

        raise ValueError(f"Unsupported Slack event: {event_type}")

    async def send_reply(self, channel_config: dict[str, Any], sender_id: str, text: str) -> None:
        bot_token = (channel_config.get("bot_token") or "").strip()
        if not bot_token:
            raise ValueError("Slack bot_token is required")

        try:
            ids = json.loads(sender_id)
            channel = ids.get("channel", sender_id)
        except (json.JSONDecodeError, TypeError):
            channel = sender_id

        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {bot_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "channel": channel,
                "text": text[:40000],
            }, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack postMessage failed: {data.get('error')}")

    async def validate_config(self, channel_config: dict[str, Any]) -> bool:
        token = (channel_config.get("bot_token") or "").strip()
        return bool(token)
