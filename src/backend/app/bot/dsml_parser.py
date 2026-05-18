"""Parse DeepSeek V3.2+ DSML tool calls embedded in message content."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

# DeepSeek uses fullwidth vertical bar ｜ in DSML tags.
_INVOKE_RE = re.compile(
    r'<｜(?:DSML｜)?invoke\s+name="([^"]+)"\s*>(.*?)(?=</｜(?:DSML｜)?invoke>|<｜(?:DSML｜)?invoke|$)',
    re.DOTALL,
)
_PARAM_RE = re.compile(
    r'<｜(?:DSML｜)?parameter\s+name="([^"]+)"\s+string="(true|false)"\s*>'
    r"(.*?)(?=</｜(?:DSML｜)?parameter>|<｜|$)",
    re.DOTALL,
)
_DSML_MARKERS = ("｜DSML｜", "｜invoke", "｜tool_calls", "｜function_calls", "｜parameter")


def contains_dsml(text: str) -> bool:
    if not text:
        return False
    return any(m in text for m in _DSML_MARKERS)


def _coerce_param(value: str, string_type: str) -> Any:
    value = (value or "").strip()
    if value.lower() == "null":
        return None
    if string_type == "true":
        return value
    if value.isdigit():
        return int(value)
    try:
        if "." in value:
            return float(value)
    except ValueError:
        pass
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _parse_invoke_params(invoke_body: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for name, string_type, raw in _PARAM_RE.findall(invoke_body):
        params[name] = _coerce_param(raw, string_type)
    return params


def parse_dsml_tool_calls(text: str) -> list[dict[str, Any]]:
    """Extract OpenAI-style tool calls from DSML text in model content."""
    if not contains_dsml(text):
        return []

    calls: list[dict[str, Any]] = []
    for idx, (name, body) in enumerate(_INVOKE_RE.findall(text)):
        arguments = _parse_invoke_params(body)
        calls.append(
            {
                "id": f"call_dsml_{idx}_{uuid.uuid4().hex[:8]}",
                "name": name.strip(),
                "arguments": arguments,
            }
        )
    return calls


def strip_dsml_blocks(text: str) -> str:
    """Remove DSML tool-call markup, keeping any leading natural-language text."""
    if not text or not contains_dsml(text):
        return text

    start = len(text)
    for marker in (
        "<｜DSML｜function_calls>",
        "<｜DSML｜tool_calls>",
        "<｜tool_calls>",
        "<｜function_calls>",
        "<｜DSML｜invoke",
        "<｜invoke",
    ):
        idx = text.find(marker)
        if idx != -1:
            start = min(start, idx)

    cleaned = text[:start].strip() if start < len(text) else ""
    if cleaned:
        return cleaned
    return ""
