"""Lightweight chat callable for query rewriting."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

ChatFn = Callable[[str], Awaitable[str]]


async def create_rewrite_chat_fn(ai_config) -> ChatFn | None:
    """Create a simple chat function from an AIConfig for query rewriting."""

    try:
        from app.bot.provider import create_provider
        provider = create_provider(ai_config)

        async def _chat(prompt: str) -> str:
            parts: list[str] = []
            async for chunk in provider.stream_chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.3,
            ):
                if chunk.get("type") == "content":
                    parts.append(chunk.get("content", ""))
            return "".join(parts)

        return _chat
    except Exception:
        return None
