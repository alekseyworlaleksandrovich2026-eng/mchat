"""Server-side ops skills: global switch, allowlist, admin-only."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.skill import Skill
from app.models.user import User

SCOPE_SERVER_OPS = "server_ops"


def skill_scope(skill: Skill) -> str:
    """tenant (default) | server_ops."""
    cfg = skill.config or {}
    raw = str(cfg.get("scope") or "tenant").strip().lower()
    return raw or "tenant"


def is_server_ops_skill(skill: Skill) -> bool:
    return skill_scope(skill) == SCOPE_SERVER_OPS


def _parse_allowlist(raw: Any) -> list[str] | None:
    """None = no allowlist (all server_ops names); [] = allow none."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            return [p.strip() for p in text.split(",") if p.strip()]
    return None


async def server_ops_enabled_for_user(
    db: AsyncSession,
    user_id: str,
) -> bool:
    """Global switch ON and user is admin."""
    if not getattr(settings, "server_ops_skills_enabled", False):
        return False
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return False
    role = (user.role or "").strip().lower()
    return role == "admin"


def filter_skills_by_ops_policy(
    skills: list[Skill],
    *,
    allow_server_ops: bool,
    allowlist: list[str] | None,
) -> list[Skill]:
    """Drop server_ops skills when disabled; optional name allowlist."""
    out: list[Skill] = []
    for skill in skills:
        if not is_server_ops_skill(skill):
            out.append(skill)
            continue
        if not allow_server_ops:
            continue
        if allowlist is not None and len(allowlist) > 0:
            if skill.name not in allowlist:
                continue
        out.append(skill)
    return out


def sync_server_ops_settings_from_db(
    *,
    enabled: bool,
    allowlist: list[str] | None,
) -> None:
    settings.server_ops_skills_enabled = enabled
    settings.server_ops_skill_allowlist = allowlist
