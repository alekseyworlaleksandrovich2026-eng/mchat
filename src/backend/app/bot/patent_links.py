"""Post-process assistant text: turn plain CN patent IDs into Markdown links."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_TEMPLATE = "https://www.9235.net/patent/{patent_id}.html"

# 中国发明专利公开号常见形态
_PATENT_ID_RE = re.compile(r"\b(CN\d{6,}[A-Z0-9]{0,3})\b")

# 已是 Markdown 链接的片段，避免重复包裹
_MD_LINK_CHUNK_RE = re.compile(r"(\[[^\]]+\]\([^)]+\))")


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def patent_link_settings_from_skills(tool_skills: list[Any]) -> dict[str, Any]:
    """Read link settings from patent-search skill secrets / config."""
    for skill in tool_skills:
        if (getattr(skill, "name", None) or "") != "patent-search":
            continue
        config = getattr(skill, "config", None) or {}
        secrets = config.get("secrets") or config.get("env") or {}
        if not isinstance(secrets, dict):
            secrets = {}
        enabled = _coerce_bool(
            secrets.get("show_external_patent_url")
            or config.get("show_external_patent_url")
        )
        template = (
            secrets.get("patent_portal_url_template")
            or config.get("patent_portal_url_template")
            or DEFAULT_TEMPLATE
        )
        return {"enabled": enabled, "template": str(template)}
    return {"enabled": False, "template": DEFAULT_TEMPLATE}


def _portal_url(patent_id: str, template: str) -> str:
    return template.replace("{patent_id}", patent_id).replace("{patentId}", patent_id)


def linkify_patent_ids(text: str, *, enabled: bool, template: str) -> str:
    if not enabled or not text:
        return text

    def _link_plain(segment: str) -> str:
        def repl(match: re.Match[str]) -> str:
            pid = match.group(1)
            return f"[{pid}]({_portal_url(pid, template)})"

        return _PATENT_ID_RE.sub(repl, segment)

    parts = _MD_LINK_CHUNK_RE.split(text)
    return "".join(
        part if _MD_LINK_CHUNK_RE.fullmatch(part) else _link_plain(part)
        for part in parts
    )
