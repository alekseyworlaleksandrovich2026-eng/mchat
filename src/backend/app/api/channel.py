"""Channel management API router."""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse, Response
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_admin
from app.models.user import User
from app.schemas.channel import (
    ChannelCreate,
    ChannelResponse,
    ChannelTestRequest,
    ChannelUpdate,
)
from app.services.channel_service import ChannelService
from app.utils.request import extract_client_ip

router = APIRouter()


def _wechat_webhook_url(request: Request, channel_id: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/channels/webhook/wechat/{channel_id}"


@router.get("/webhook/wechat/{channel_id}")
async def wechat_webhook_verify(
    channel_id: str,
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WeChat server URL verification (configure this URL in 微信公众平台)."""
    from app.models.channel import Channel

    result = await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.channel_type == "wechat")
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="WeChat channel not found")

    token = (channel.config or {}).get("token", "")
    check = hashlib.sha1(
        "".join(sorted([token, timestamp, nonce])).encode()
    ).hexdigest()
    if check != signature:
        raise HTTPException(status_code=403, detail="Invalid signature")
    return int(echostr) if echostr.isdigit() else echostr


@router.post("/webhook/wechat/{channel_id}")
async def wechat_webhook_receive(
    channel_id: str,
    request: Request,
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    msg_signature: str | None = Query(None, alias="msg_signature"),
    encrypt_type: str | None = Query(None, alias="encrypt_type"),
    db: AsyncSession = Depends(get_db),
):
    """Receive WeChat user messages and return passive XML reply."""
    from app.models.channel import Channel
    from app.services.wechat_channel_service import handle_wechat_webhook

    result = await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.channel_type == "wechat")
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="WeChat channel not found")
    if not channel.enabled:
        raise HTTPException(status_code=403, detail="Channel disabled")

    body = await request.body()
    try:
        reply_body = await handle_wechat_webhook(
            channel,
            body=body,
            signature=signature,
            timestamp=timestamp,
            nonce=nonce,
            encrypt_type=encrypt_type,
            msg_signature=msg_signature,
            client_ip=extract_client_ip(request),
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WeChat webhook error: {e}", exc_info=True)
        return PlainTextResponse("success")

    if reply_body == "success":
        return PlainTextResponse("success")
    return Response(content=reply_body, media_type="application/xml")


@router.get("/{channel_id}/webhook-info")
async def get_channel_webhook_info(
    channel_id: str,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return callback URL for channel types that need external webhook configuration."""
    service = ChannelService(db)
    channel = await service.get_channel(channel_id=channel_id, user_id=admin.id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel.channel_type == "wechat":
        url = _wechat_webhook_url(request, channel_id)
        return {
            "channel_type": "wechat",
            "webhook_url": url,
            "hint": (
                "在微信公众号后台 → 开发 → 基本配置 → 服务器配置，填入此 URL；"
                "Token、EncodingAESKey 与本页一致，并务必选择「客服配置（Agent）」"
            ),
        }
    return {"channel_type": channel.channel_type, "webhook_url": None, "hint": None}


@router.get("", response_model=list[ChannelResponse])
async def list_channels(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all channels."""
    service = ChannelService(db)
    return await service.list_channels(user_id=admin.id)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a channel."""
    service = ChannelService(db)
    channel = await service.get_channel(
        channel_id=channel_id, user_id=admin.id
    )
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    request: ChannelCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new channel."""
    service = ChannelService(db)
    return await service.create_channel(
        user_id=admin.id, data=request
    )


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    request: ChannelUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a channel."""
    service = ChannelService(db)
    channel = await service.update_channel(
        channel_id=channel_id, user_id=admin.id, data=request
    )
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a channel."""
    service = ChannelService(db)
    success = await service.delete_channel(
        channel_id=channel_id, user_id=admin.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found")
    return None


@router.post("/test", response_model=dict)
async def test_channel(
    request: ChannelTestRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test a channel connection."""
    service = ChannelService(db)
    return await service.test_channel(
        user_id=admin.id,
        channel_type=request.channel_type,
        config=request.config,
    )
