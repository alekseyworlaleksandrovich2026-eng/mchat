"""Base adapter interface for multi-channel message protocols."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ChannelMessage:
    """Normalized incoming message from any channel."""

    sender_id: str
    """Channel-specific sender identifier (e.g. Telegram user id, WeChat openid)."""

    content: str
    """Message text content."""

    msg_type: str = "text"
    """Message type: text, image, voice, event, etc."""

    event: str | None = None
    """Event type for non-message pushes (e.g. 'subscribe', 'member_joined')."""

    raw: dict[str, Any] | None = None
    """Original parsed payload for channel-specific handling."""


class BaseChannelAdapter(ABC):
    """Abstract adapter for a messaging channel.

    Each channel (Telegram, WhatsApp, Slack, LINE, DingTalk) implements
    this interface to normalize webhook verification, message parsing,
    and reply sending.
    """

    @abstractmethod
    async def verify_webhook(self, query_params: dict[str, str]) -> str | None:
        """Verify webhook ownership (e.g. challenge/response).

        Returns the challenge response string, or None if no verification needed.
        Raise HTTPException on failure.
        """
        ...

    @abstractmethod
    async def parse_message(self, body: bytes, query_params: dict[str, str]) -> ChannelMessage:
        """Parse an incoming webhook payload into a normalized ChannelMessage.

        Raise ValueError or HTTPException on parse failure.
        """
        ...

    @abstractmethod
    async def send_reply(self, channel_config: dict[str, Any], sender_id: str, text: str) -> None:
        """Send a text reply to the channel user.

        Args:
            channel_config: The channel's config dict (credentials, tokens, etc.).
            sender_id: The recipient identifier from ChannelMessage.sender_id.
            text: The reply text content.
        """
        ...

    @abstractmethod
    async def validate_config(self, channel_config: dict[str, Any]) -> bool:
        """Validate that the channel config has the required credentials.

        Returns True if config is sufficient for basic operation.
        """
        ...
