"""Filter skill id lists for tenant-facing configs (no server_ops)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.skill.ops_policy import is_server_ops_skill


async def filter_tenant_skill_ids(
    db: AsyncSession,
    user_id: str,
    skill_ids: list[str] | None,
) -> list[str]:
    """Remove server_ops skills from channel/template skill id lists."""
    if not skill_ids:
        return []
    ids = [str(x).strip() for x in skill_ids if str(x).strip()]
    if not ids:
        return []
    result = await db.execute(
        select(Skill).where(Skill.user_id == user_id, Skill.id.in_(ids))
    )
    allowed: list[str] = []
    for skill in result.scalars().all():
        if is_server_ops_skill(skill):
            continue
        allowed.append(skill.id)
    return allowed
