"""Dashboard API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, has_global_scope, require_permission, Permission
from app.models.user import User
from app.schemas.dashboard import (
    AgentStatsResponse,
    DashboardActivity,
    DashboardStatsResponse,
    RetrievalStatsResponse,
    StatsOverviewResponse,
    TrendsResponse,
)
from app.services.dashboard_service import DashboardService
from app.services.retrieval_log_service import RetrievalLogService

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    user_scope = None if await has_global_scope(current_user, db) else current_user.id
    return await service.get_stats(user_id=user_scope)


@router.get("/overview", response_model=StatsOverviewResponse)
async def get_stats_overview(
    period: int = Query(30, ge=7, le=365, description="Period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive stats overview with computed KPIs (FRT, ART, resolution rate)."""
    service = DashboardService(db)
    user_scope = None if await has_global_scope(current_user, db) else current_user.id
    return await service.get_overview(user_id=user_scope, period_days=period)


@router.get("/trends", response_model=TrendsResponse)
async def get_stats_trends(
    metric: str = Query("messages", pattern=r"^(messages|conversations|documents)$"),
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily time-series data for the specified metric."""
    service = DashboardService(db)
    user_scope = None if await has_global_scope(current_user, db) else current_user.id
    return await service.get_trends(user_id=user_scope, metric=metric, days=days)


@router.get("/agents", response_model=AgentStatsResponse)
async def get_agent_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get per-agent (customer config) performance stats."""
    service = DashboardService(db)
    user_scope = None if await has_global_scope(current_user, db) else current_user.id
    return await service.get_agent_stats(user_id=user_scope)


@router.get("/retrieval-stats", response_model=RetrievalStatsResponse)
async def get_retrieval_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_permission(Permission.DASHBOARD_READ)),
    db: AsyncSession = Depends(get_db),
):
    """RAG retrieval observability: zero-result rate and slow queries."""
    user_scope = None if await has_global_scope(current_user, db) else current_user.id
    stats = await RetrievalLogService(db).get_stats(user_id=user_scope, days=days)
    return RetrievalStatsResponse(**stats)


@router.get("/activities", response_model=list[DashboardActivity])
async def get_dashboard_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    user_scope = None if await has_global_scope(current_user, db) else current_user.id
    return await service.get_activities(user_id=user_scope)
