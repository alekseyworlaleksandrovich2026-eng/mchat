"""Portal API router — user-facing channel rental and management."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ConversationResponse
from app.services.chat_service import ChatService
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


@router.post(
    "/channels/{channel_id}/conversation/resume",
    response_model=ConversationResponse,
)
async def resume_channel_conversation(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Resume the user's persistent chat thread for this channel (or create once)."""
    chat_service = ChatService(db)
    channel = await PortalService(db).get_my_channel(current_user, channel_id)
    return await chat_service.get_or_resume_channel_conversation(
        user_id=current_user.id,
        channel_id=channel_id,
        title=channel.name,
    )


@router.get("/channels/{channel_id}/embed", response_model=EmbedCodeResponse)
async def get_embed_code(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmbedCodeResponse:
    """Get widget embed code for a channel."""
    return await PortalService(db).get_embed_code(current_user, channel_id)


@router.get("/channels/{channel_id}/knowledge-bases")
async def list_channel_knowledge_bases(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List knowledge bases bound to the user's channel."""
    return await PortalService(db).list_channel_knowledge_bases(
        current_user, channel_id
    )


@router.post("/channels/{channel_id}/knowledge-bases", status_code=status.HTTP_201_CREATED)
async def create_channel_knowledge_base(
    channel_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a knowledge base and attach it to the channel."""
    return await PortalService(db).create_channel_knowledge_base(
        current_user, channel_id, body
    )


@router.delete(
    "/channels/{channel_id}/knowledge-bases/{kb_id}",
    status_code=status.HTTP_200_OK,
)
async def remove_channel_knowledge_base(
    channel_id: str,
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove KB from channel; delete it only when user-owned."""
    return await PortalService(db).remove_channel_knowledge_base(
        current_user, channel_id, kb_id
    )


@router.post(
    "/channels/{channel_id}/knowledge-bases/{kb_id}/import-file",
    status_code=status.HTTP_201_CREATED,
)
async def import_channel_document(
    channel_id: str,
    kb_id: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document into a channel-bound knowledge base."""
    try:
        return await PortalService(db).import_channel_document(
            current_user, channel_id, kb_id, file
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {e}",
        ) from e
