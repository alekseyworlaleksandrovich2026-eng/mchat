"""Skill management API router."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_admin
from app.models.user import User
from app.schemas.skill import (
    SkillCatalogResponse,
    SkillInstallUrlRequest,
    SkillResponse,
    SkillUpdate,
)
from app.services.skill_service import SkillService

router = APIRouter()


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all skills for current user."""
    service = SkillService(db)
    return await service.list_skills(user_id=admin.id)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    request: SkillUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a skill, or update its config."""
    service = SkillService(db)
    skill = await service.update_skill(
        skill_id=skill_id, user_id=admin.id, data=request
    )
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    return skill


@router.post("/reload")
async def reload_skills(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reload skills from filesystem."""
    service = SkillService(db)
    count = await service.reload_skills(user_id=admin.id)
    return {"reloaded": count, "message": f"Reloaded {count} skills"}


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a skill."""
    service = SkillService(db)
    success = await service.delete_skill(
        skill_id=skill_id, user_id=admin.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    return None


@router.post("/upload")
async def upload_skill(
    file: UploadFile,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new skill (zip file)."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip files are supported",
        )
    service = SkillService(db)
    try:
        return await service.upload_skill(
            user_id=admin.id, file=file
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {e}",
        ) from e


@router.post("/install-url", response_model=SkillResponse)
async def install_skill_from_url(
    request: SkillInstallUrlRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install a skill package from direct URL or ClawHub skill name."""
    service = SkillService(db)
    source = request.url.strip()
    if source.startswith(("http://", "https://")):
        return await service.install_skill_from_url(
            user_id=admin.id,
            url=source,
            name_hint=request.name,
        )
    return await service.install_skill_by_name(
        user_id=admin.id,
        name=source,
    )


@router.get("/catalog", response_model=SkillCatalogResponse)
async def list_skill_catalog(
    query: str | None = None,
    limit: int = 24,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Browse remote skill catalog (best-effort ClawHub integration)."""
    service = SkillService(db)
    items = await service.fetch_clawhub_catalog(query=query, limit=limit)
    return SkillCatalogResponse(source="clawhub", items=items)
