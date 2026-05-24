"""Channel service - business logic for communication channel management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import AIConfig
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate


async def channel_get_or_create_conversation(
    db: AsyncSession,
    sender_id: str,
    customer: CustomerConfig,
    *,
    contact_info: str,
    title: str,
    client_ip: str | None = None,
) -> Conversation:
    """Find or create an active conversation for a channel message."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.visitor_id == sender_id,
            Conversation.contact_info == contact_info,
            Conversation.status == "active",
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        if not conversation.customer_id:
            conversation.customer_id = customer.id
        return conversation

    conversation = Conversation(
        id=str(uuid.uuid4()),
        visitor_id=sender_id,
        customer_id=customer.id,
        client_ip=client_ip,
        ai_config_id=customer.ai_config_id,
        title=title,
        contact_info=contact_info,
        status="active",
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def channel_resolve_ai_config(
    db: AsyncSession, customer: CustomerConfig
) -> AIConfig | None:
    """Resolve AI config from customer or fall back to default."""
    if customer.ai_config_id:
        result = await db.execute(
            select(AIConfig).where(AIConfig.id == customer.ai_config_id)
        )
        cfg = result.scalar_one_or_none()
        if cfg is not None:
            return cfg
    result = await db.execute(
        select(AIConfig).where(AIConfig.is_default == True)
    )
    return result.scalar_one_or_none()


class ChannelService:
    """Handles channel management business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_channels(self, user_id: str) -> list[ChannelResponse]:
        """List all channels for a user."""
        result = await self.db.execute(
            select(Channel)
            .where(Channel.user_id == user_id)
            .order_by(Channel.created_at.desc())
        )
        channels = result.scalars().all()
        return [ChannelResponse.model_validate(c) for c in channels]

    async def get_channel(
        self, channel_id: str, user_id: str
    ) -> ChannelResponse | None:
        """Get a specific channel."""
        result = await self.db.execute(
            select(Channel).where(
                Channel.id == channel_id, Channel.user_id == user_id
            )
        )
        channel = result.scalar_one_or_none()
        if channel is None:
            return None
        return ChannelResponse.model_validate(channel)

    async def create_channel(
        self, user_id: str, data: ChannelCreate
    ) -> ChannelResponse:
        """Create a new channel."""
        channel = Channel(
            user_id=user_id,
            name=data.name,
            channel_type=data.channel_type,
            config=data.config or {},
            enabled=data.enabled,
        )
        self.db.add(channel)
        await self.db.flush()
        await self.db.refresh(channel)
        return ChannelResponse.model_validate(channel)

    async def update_channel(
        self, channel_id: str, user_id: str, data: ChannelUpdate
    ) -> ChannelResponse | None:
        """Update a channel."""
        result = await self.db.execute(
            select(Channel).where(
                Channel.id == channel_id, Channel.user_id == user_id
            )
        )
        channel = result.scalar_one_or_none()
        if channel is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(channel, key, value)

        await self.db.flush()
        await self.db.refresh(channel)
        return ChannelResponse.model_validate(channel)

    async def delete_channel(
        self, channel_id: str, user_id: str
    ) -> bool:
        """Delete a channel."""
        result = await self.db.execute(
            select(Channel).where(
                Channel.id == channel_id, Channel.user_id == user_id
            )
        )
        channel = result.scalar_one_or_none()
        if channel is None:
            return False
        await self.db.delete(channel)
        await self.db.flush()
        return True

    async def test_channel(
        self, user_id: str, channel_type: str, config: dict | None
    ) -> dict:
        """Test a channel connection."""
        config = config or {}

        if channel_type == "web_widget":
            widget_id = (config.get("widget_id") or "").strip()
            if not widget_id:
                return {
                    "ok": False,
                    "message": "请填写 Widget ID（在「AI 与客服配置 → 客服配置」中复制 Agent ID）",
                }

            result = await self.db.execute(
                select(CustomerConfig).where(
                    CustomerConfig.id == widget_id,
                    CustomerConfig.user_id == user_id,
                )
            )
            customer = result.scalar_one_or_none()
            if customer is None:
                return {
                    "ok": False,
                    "message": f"未找到 Widget 配置 ID: {widget_id}",
                }
            if not customer.enabled:
                return {
                    "ok": False,
                    "message": f"客服配置「{customer.name}」已禁用，请先在管理后台启用",
                }

            preview_path = f"/widget.html?agentId={widget_id}"
            return {
                "ok": True,
                "message": f"Widget「{customer.name}」配置有效，可打开预览页测试",
                "widget_id": widget_id,
                "preview_url": preview_path,
                "config_api": f"/api/widget/config/{widget_id}/full",
            }

        if channel_type == "wechat":
            missing = []
            for key, label in (
                ("app_id", "App ID"),
                ("app_secret", "App Secret"),
                ("token", "Token"),
                ("customer_id", "客服配置（Agent）"),
            ):
                if not str(config.get(key) or "").strip():
                    missing.append(label)
            if missing:
                return {
                    "ok": False,
                    "message": f"请填写：{', '.join(missing)}",
                }
            try:
                import wechatpy  # noqa: F401
            except ImportError:
                aes = str(config.get("encoding_aes_key") or "").strip()
                if aes:
                    return {
                        "ok": False,
                        "message": "安全模式需安装 wechatpy：pip install wechatpy",
                    }
            try:
                from app.services.wechat_channel_service import _fetch_wechat_access_token

                await _fetch_wechat_access_token(
                    str(config.get("app_id") or "").strip(),
                    str(config.get("app_secret") or "").strip(),
                    force_refresh=True,
                )
            except Exception as e:
                return {
                    "ok": False,
                    "message": f"微信公众号配置未通过 access_token 校验：{e}",
                }
            return {
                "ok": True,
                "message": (
                    "微信公众号配置完整。当前默认使用客服消息主动下发模式"
                    "（App ID + App Secret 获取 access_token）。"
                    "请在公众平台配置服务器 URL，并确保已绑定客服 Agent。"
                ),
            }

        return {
            "ok": True,
            "message": (
                f"频道类型「{channel_type}」配置格式有效；"
                "第三方平台连通性测试尚未实现"
            ),
        }
