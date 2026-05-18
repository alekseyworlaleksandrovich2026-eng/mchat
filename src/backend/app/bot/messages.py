"""Helpers to build OpenAI-compatible chat message lists."""

from __future__ import annotations

import json
from typing import Any


def sanitize_history_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep only roles/content safe for chat completion replay."""
    safe: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "system":
            if content is not None and str(content).strip():
                safe.append({"role": "system", "content": str(content)})
        elif role == "user":
            if content is not None and str(content).strip():
                safe.append({"role": "user", "content": str(content)})
        elif role == "assistant":
            if content is not None and str(content).strip():
                safe.append({"role": "assistant", "content": str(content)})
    return safe


def build_assistant_tool_call_message(
    content: str,
    tool_calls: list[dict[str, Any]],
    reasoning_content: str | None = None,
) -> dict[str, Any]:
    """Build assistant message that precedes tool result messages.

    DeepSeek thinking mode requires ``reasoning_content`` on assistant messages
    that include ``tool_calls`` when sent back on the next API turn.
    """
    api_tool_calls = []
    for tc in tool_calls:
        args = tc.get("arguments") or {}
        if isinstance(args, str):
            args_str = args
        else:
            args_str = json.dumps(args, ensure_ascii=False)
        api_tool_calls.append(
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": args_str,
                },
            }
        )
    msg: dict[str, Any] = {
        "role": "assistant",
        "content": content or "",
        "tool_calls": api_tool_calls,
    }
    if reasoning_content is not None and str(reasoning_content).strip():
        msg["reasoning_content"] = str(reasoning_content)
    return msg


def build_tool_result_message(tool_call_id: str, result: Any) -> dict[str, Any]:
    """Build a tool role message for the OpenAI API."""
    if isinstance(result, str):
        content = result
    else:
        content = json.dumps(result, ensure_ascii=False, default=str)
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }
