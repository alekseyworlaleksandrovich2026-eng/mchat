from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import has_global_scope
from app.models.skill_workflow import SkillWorkflow
from app.models.user import User
from app.schemas.workflow_entitlements import WorkflowEntitlementsResponse


async def get_workflow_entitlements(
    db: AsyncSession, current_user: User
) -> WorkflowEntitlementsResponse:
    is_admin = await has_global_scope(current_user, db)
    return WorkflowEntitlementsResponse(
        can_create=True,
        can_save_dag=is_admin,
        can_run=True,
        max_workflows=0 if is_admin else 50,
        max_active_runs=0 if is_admin else 10,
    )


async def _workflow_count(db: AsyncSession, user: User) -> int:
    result = await db.scalar(
        select(func.count()).select_from(SkillWorkflow).where(SkillWorkflow.user_id == user.id)
    )
    return result or 0


async def ensure_can_create_workflow(db: AsyncSession, user: User) -> None:
    if await has_global_scope(user, db):
        return
    count = await _workflow_count(db, user)
    if count >= 50:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workflow limit reached",
        )


async def ensure_can_save_dag(db: AsyncSession, user: User) -> None:
    if await has_global_scope(user, db):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="DAG editing requires an upgraded plan",
    )


async def ensure_can_run_workflow(db: AsyncSession, user: User) -> None:
    if await has_global_scope(user, db):
        return
