"""Tests for OpenAI-compatible message builders."""

from app.bot.messages import build_assistant_tool_call_message


def test_assistant_tool_message_includes_reasoning_content():
    msg = build_assistant_tool_call_message(
        "I'll search patents.",
        [{"id": "call_1", "name": "patent-search", "arguments": {"command": "search"}}],
        reasoning_content="Let me call the patent API.",
    )
    assert msg["role"] == "assistant"
    assert msg["reasoning_content"] == "Let me call the patent API."
    assert len(msg["tool_calls"]) == 1


def test_assistant_tool_message_omits_empty_reasoning():
    msg = build_assistant_tool_call_message(
        "hi",
        [{"id": "call_1", "name": "x", "arguments": {}}],
        reasoning_content="   ",
    )
    assert "reasoning_content" not in msg
