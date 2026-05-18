"""Skill service - business logic for skill management."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.skill import Skill
from app.schemas.skill import SkillResponse, SkillUpdate
from app.skill.loader import SkillLoader
from app.skill.zip_utils import extract_skill_zip, read_skill_meta_from_zip


class SkillService:
    """Handles skill management business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _skills_root() -> Path:
        return Path(settings.skills_dir).resolve()

    @staticmethod
    def _skill_directory(skill: Skill) -> Path | None:
        if not skill.path:
            return None
        skill_md = Path(skill.path).resolve()
        if skill_md.is_file() and skill_md.name.lower() == "skill.md":
            return skill_md.parent
        if skill_md.is_dir():
            return skill_md
        return None

    def _is_managed_skill_dir(self, directory: Path) -> bool:
        """Only delete directories inside the configured skills folder."""
        try:
            directory.resolve().relative_to(self._skills_root())
            return True
        except ValueError:
            return False

    def _remove_skill_directory(self, skill: Skill) -> None:
        directory = self._skill_directory(skill)
        if directory is None or not directory.exists():
            return
        if not self._is_managed_skill_dir(directory):
            logger.warning(f"Skip deleting skill dir outside skills root: {directory}")
            return
        shutil.rmtree(directory)
        logger.info(f"Removed skill directory: {directory}")

    async def list_skills(self, user_id: str) -> list[SkillResponse]:
        """List all skills for a user."""
        result = await self.db.execute(
            select(Skill)
            .where(Skill.user_id == user_id)
            .order_by(Skill.created_at.desc())
        )
        skills = result.scalars().all()
        return [SkillResponse.model_validate(s) for s in skills]

    async def update_skill(
        self, skill_id: str, user_id: str, data: SkillUpdate
    ) -> SkillResponse | None:
        """Update a skill (enable/disable or config changes)."""
        result = await self.db.execute(
            select(Skill).where(
                Skill.id == skill_id, Skill.user_id == user_id
            )
        )
        skill = result.scalar_one_or_none()
        if skill is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(skill, key, value)

        await self.db.flush()
        await self.db.refresh(skill)
        return SkillResponse.model_validate(skill)

    async def delete_skill(
        self, skill_id: str, user_id: str
    ) -> bool:
        """Delete a skill from DB and remove its directory under skills/."""
        result = await self.db.execute(
            select(Skill).where(
                Skill.id == skill_id, Skill.user_id == user_id
            )
        )
        skill = result.scalar_one_or_none()
        if skill is None:
            return False
        if skill.skill_type == "builtin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete built-in skills",
            )
        self._remove_skill_directory(skill)
        await self.db.delete(skill)
        await self.db.flush()
        return True

    async def _prune_stale_filesystem_skills(self, user_id: str) -> int:
        """Remove DB rows whose SKILL.md path no longer exists on disk."""
        removed = 0
        result = await self.db.execute(
            select(Skill).where(Skill.user_id == user_id)
        )
        for skill in result.scalars().all():
            if skill.skill_type == "builtin" or not skill.path:
                continue
            skill_md = Path(skill.path)
            if not skill_md.is_file():
                await self.db.delete(skill)
                removed += 1
        if removed:
            await self.db.flush()
        return removed

    async def reload_skills(self, user_id: str) -> int:
        """Sync DB with skills/ on disk: update existing, add new, drop stale."""
        await self._prune_stale_filesystem_skills(user_id)

        loader = SkillLoader()
        skills = loader.scan_skills()
        count = 0
        for skill_data in skills:
            result = await self.db.execute(
                select(Skill).where(
                    Skill.user_id == user_id,
                    Skill.name == skill_data["name"],
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.description = skill_data.get("description")
                existing.skill_type = skill_data.get("type", "tool")
                existing.path = skill_data.get("path")
                merged = dict(existing.config or {})
                disk_cfg = skill_data.get("config") or {}
                merged.update(
                    {
                        k: v
                        for k, v in disk_cfg.items()
                        if k not in ("secrets", "env")
                    }
                )
                existing.config = merged
                existing.enabled = True
            else:
                skill = Skill(
                    user_id=user_id,
                    name=skill_data["name"],
                    description=skill_data.get("description"),
                    skill_type=skill_data.get("type", "tool"),
                    path=skill_data.get("path"),
                    config=skill_data.get("config"),
                    enabled=True,
                )
                self.db.add(skill)
            count += 1

        if count > 0:
            await self.db.flush()
        return count

    async def upload_skill(
        self, user_id: str, file: UploadFile
    ) -> SkillResponse:
        """Upload a skill zip; overwrites same-name skill directory on disk."""
        content = await file.read()
        skills_dir = self._skills_root()
        skills_dir.mkdir(parents=True, exist_ok=True)

        try:
            meta = read_skill_meta_from_zip(content)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        skill_name = meta.get("name") or Path(file.filename or "skill").stem
        zip_stem = Path(file.filename or "skill").stem

        result = await self.db.execute(
            select(Skill).where(
                Skill.user_id == user_id,
                Skill.name == skill_name,
            )
        )
        existing = result.scalar_one_or_none()

        if existing and existing.path:
            extract_path = self._skill_directory(existing) or (skills_dir / zip_stem)
        else:
            extract_path = skills_dir / zip_stem

        extract_path = extract_path.resolve()
        if not str(extract_path).startswith(str(skills_dir)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid skill install path",
            )

        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True, exist_ok=True)

        try:
            extract_skill_zip(content, extract_path)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        await self.reload_skills(user_id)

        result = await self.db.execute(
            select(Skill).where(
                Skill.user_id == user_id,
                Skill.name == skill_name,
            )
        )
        skill = result.scalar_one_or_none()
        if skill is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Skill extracted to {extract_path.name} but not registered. "
                    f"Check SKILL.md frontmatter name (expected: {skill_name})"
                ),
            )
        return SkillResponse.model_validate(skill)
