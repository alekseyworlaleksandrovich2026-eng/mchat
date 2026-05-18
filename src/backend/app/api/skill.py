"""Skill management API router."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.skill import SkillResponse, SkillUpdate
from app.services.skill_service import SkillService

router = APIRouter()


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all skills for current user."""
    service = SkillService(db)
    return await service.list_skills(user_id=current_user.id)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    request: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a skill, or update its config."""
    service = SkillService(db)
    skill = await service.update_skill(
        skill_id=skill_id, user_id=current_user.id, data=request
    )
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    return skill


@router.post("/reload")
async def reload_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reload skills from filesystem."""
    service = SkillService(db)
    count = await service.reload_skills(user_id=current_user.id)
    return {"reloaded": count, "message": f"Reloaded {count} skills"}


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a skill."""
    service = SkillService(db)
    success = await service.delete_skill(
        skill_id=skill_id, user_id=current_user.id
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
    current_user: User = Depends(get_current_user),
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
            user_id=current_user.id, file=file
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {e}",
        ) from e
