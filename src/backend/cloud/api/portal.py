"""Portal API router — user-facing channel rental and management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from cloud.schemas.portal import (
    EmbedCodeResponse,
    MyChannelResponse,
    MyChannelUpdate,
    PortalDashboardStats,
    RentChannelRequest,
)
from cloud.services.portal_service import PortalService

router = APIRouter()


@router.get("/dashboard", response_model=PortalDashboardStats)
async def portal_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortalDashboardStats:
    """Get portal dashboard stats for the current user."""
    return await PortalService(db).get_dashboard_stats(current_user)


@router.get("/channels", response_model=list[MyChannelResponse])
async def list_my_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MyChannelResponse]:
    """List channels owned by the current user."""
    return await PortalService(db).list_my_channels(current_user)


@router.post("/channels/rent", response_model=MyChannelResponse, status_code=status.HTTP_201_CREATED)
async def rent_channel(
    request: RentChannelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MyChannelResponse:
    """Provision a new channel from a published template."""
    try:
        return await PortalService(db).rent_channel(current_user, request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create channel: {e}",
        )


@router.get("/channels/{channel_id}", response_model=MyChannelResponse)
async def get_my_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MyChannelResponse:
    """Get a specific channel owned by the user."""
    return await PortalService(db).get_my_channel(current_user, channel_id)


@router.put("/channels/{channel_id}", response_model=MyChannelResponse)
async def update_my_channel(
    channel_id: str,
    request: MyChannelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MyChannelResponse:
    """Update channel settings (user-scoped)."""
    return await PortalService(db).update_my_channel(current_user, channel_id, request)


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a channel owned by the user."""
    await PortalService(db).delete_my_channel(current_user, channel_id)


@router.get("/channels/{channel_id}/embed", response_model=EmbedCodeResponse)
async def get_embed_code(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmbedCodeResponse:
    """Get widget embed code for a channel."""
    return await PortalService(db).get_embed_code(current_user, channel_id)
