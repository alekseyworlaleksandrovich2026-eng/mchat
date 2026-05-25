#!/usr/bin/env python3
"""重载 mchat skills/ 目录到数据库。

用法:
  cd /Users/xiaoxiao/dev/mchat/src/backend
  python ../../scripts/reload-patent-skills.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "src" / "backend"
sys.path.insert(0, str(BACKEND))


async def main() -> None:
    from sqlalchemy import select

    from app.core.config import settings
    from app.core.database import async_session_factory
    from app.models.skill import Skill
    from app.models.user import User
    from app.services.skill_service import SkillService

    print(f"SKILLS_DIR={Path(settings.skills_dir).resolve()}")

    async with async_session_factory() as db:
        user_result = await db.execute(
            select(User).where(User.username == settings.admin_username)
        )
        admin = user_result.scalar_one_or_none()
        if not admin:
            print("❌ 未找到 admin 用户")
            sys.exit(1)

        svc = SkillService(db)
        n = await svc.reload_skills(user_id=admin.id)
        await db.commit()
        print(f"✅ 已重载 {n} 个技能")

        result = await db.execute(
            select(Skill).where(
                Skill.user_id == admin.id,
                Skill.name.like("patent%"),
            )
        )
        for s in result.scalars().all():
            print(f"  - {s.name}: type={s.skill_type}, enabled={s.enabled}")


if __name__ == "__main__":
    asyncio.run(main())
