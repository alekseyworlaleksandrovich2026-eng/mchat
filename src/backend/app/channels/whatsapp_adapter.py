"""WhatsApp Cloud API — webhook verification, message parsing, reply sending."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.channels.base_adapter import BaseChannelAdapter, ChannelMessage


class WhatsAppAdapter(BaseChannelAdapter):
    """Adapter for WhatsApp Cloud API (Meta) webhooks."""

    async def verify_webhook(self, query_params: dict[str, str]) -> str | None:
        mode = query_params.get("hub.mode", "")
        token = query_params.get("hub.verify_token", "")
        challenge = query_params.get("hub.challenge", "")

        if mode == "subscribe":
            return challenge
        return None

    async def parse_message(self, body: bytes, query_params: dict[str, str]) -> ChannelMessage:
        payload = json.loads(body)

        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})

                if "messages" in value:
                    msgs = value["messages"]
                    if msgs:
                        msg = msgs[0]
                        sender_id = msg.get("from", "")
                        msg_type = msg.get("type", "text")
                        content = ""
                        if msg_type == "text":
                            content = msg.get("text", {}).get("body", "")
                        elif msg_type == "interactive":
                            interactive = msg.get("interactive", {})
                            content = interactive.get("button_reply", {}).get("id", "")
                            if not content:
                                content = interactive.get("list_reply", {}).get("id", "")

                        return ChannelMessage(
                            sender_id=sender_id,
                            content=content,
                            msg_type=msg_type,
                            raw=payload,
                        )

                if "statuses" in value:
                    return ChannelMessage(
                        sender_id="",
                        content="",
                        msg_type="status",
                        raw=payload,
                    )

        raise ValueError(f"Unsupported WhatsApp payload: {payload}")

    async def send_reply(self, channel_config: dict[str, Any], sender_id: str, text: str) -> None:
        phone_number_id = (channel_config.get("phone_number_id") or "").strip()
        access_token = (channel_config.get("access_token") or "").strip()

        if not phone_number_id or not access_token:
            raise ValueError("WhatsApp phone_number_id and access_token are required")

        url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "messaging_product": "whatsapp",
                "to": sender_id,
                "type": "text",
                "text": {"body": text[:4096]},
            }, headers=headers)
            resp.raise_for_status()

    async def validate_config(self, channel_config: dict[str, Any]) -> bool:
        phone = (channel_config.get("phone_number_id") or "").strip()
        token = (channel_config.get("access_token") or "").strip()
        return bool(phone and token)
