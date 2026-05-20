"""Dashboard API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardActivity, DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    user_scope = None if current_user.role == "admin" else current_user.id
    return await service.get_stats(user_id=user_scope)


@router.get("/activities", response_model=list[DashboardActivity])
async def get_dashboard_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    user_scope = None if current_user.role == "admin" else current_user.id
    return await service.get_activities(user_id=user_scope)
