"""System settings and widget configuration API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_admin
from app.models.user import User
from app.models.customer import CustomerConfig
from app.schemas.agent import (
    CustomerConfigCreate,
    CustomerConfigResponse,
)
from pydantic import BaseModel, Field

from app.schemas.settings import AppLogResponse, AppSettingsResponse, AppSettingsUpdate
from app.services.settings_service import SettingsService
from app.services.agent_service import AgentService

router = APIRouter()

# ─── System Settings ───────────────────────────────────────────

@router.get("", response_model=AppSettingsResponse)
async def get_settings(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get current system settings."""
    service = SettingsService(db)
    return await service.get_settings()


@router.put("", response_model=AppSettingsResponse)
async def update_settings(
    request: AppSettingsUpdate,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update system settings."""
    service = SettingsService(db)
    return await service.update_settings(request)


class MilvusTestRequest(BaseModel):
    milvus_enabled: bool = False
    milvus_host: str = "localhost"
    milvus_port: int = Field(19530, ge=1, le=65535)


@router.post("/milvus/test")
async def test_milvus_settings(
    request: MilvusTestRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test Milvus connection with provided settings."""
    service = SettingsService(db)
    return await service.test_milvus_connection(
        enabled=request.milvus_enabled,
        host=request.milvus_host,
        port=request.milvus_port,
    )


@router.get("/logs", response_model=AppLogResponse)
async def get_backend_logs(
    source: str = "app",
    lines: int = 200,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get backend log tail for admin troubleshooting."""
    source = source if source in ("app", "error") else "app"
    service = SettingsService(db)
    result = await service.get_log_tail(source=source, lines=lines)
    return AppLogResponse(**result)


# ─── Widget / Customer Config ──────────────────────────────────

@router.get("/widget", response_model=CustomerConfigResponse)
async def get_widget_settings(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get the first customer (widget) config for the current user."""
    agent_service = AgentService(db)
    configs = await agent_service.list_customer_configs(user_id=admin.id)
    if not configs:
        # Return a default stub
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No widget config found. Please create one first.",
        )
    return configs[0]


@router.put("/widget", response_model=CustomerConfigResponse)
async def update_widget_settings(
    request: CustomerConfigCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create or update the first widget config for the current user."""
    agent_service = AgentService(db)
    configs = await agent_service.list_customer_configs(user_id=admin.id)

    if configs:
        # Update existing
        updated = await agent_service.update_customer_config(
            config_id=configs[0].id,
            user_id=admin.id,
            data=request,
        )
        return updated or configs[0]
    else:
        # Create new
        return await agent_service.create_customer_config(
            user_id=admin.id, data=request
        )
