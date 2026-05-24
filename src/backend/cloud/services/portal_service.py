"""Portal service — user-facing channel rental business logic."""

from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel_template import ChannelTemplate
from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.models.message import Message
from app.models.user import User
from cloud.schemas.portal import (
    ChannelTemplateResponse,
    EmbedCodeResponse,
    MyChannelResponse,
    MyChannelUpdate,
    PortalDashboardStats,
    RentChannelRequest,
)


class PortalService:
    """Handles user-facing channel rental and management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Templates ───────────────────────────────────────────────────

    async def list_published_templates(self) -> list[ChannelTemplateResponse]:
        result = await self.db.execute(
            select(ChannelTemplate)
            .where(ChannelTemplate.is_published == True)
            .order_by(ChannelTemplate.sort_order, ChannelTemplate.created_at.desc())
        )
        return [ChannelTemplateResponse.model_validate(t) for t in result.scalars().all()]

    async def get_template(self, template_id: str) -> ChannelTemplateResponse:
        result = await self.db.execute(
            select(ChannelTemplate).where(
                ChannelTemplate.id == template_id,
                ChannelTemplate.is_published == True,
            )
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        return ChannelTemplateResponse.model_validate(template)

    # ── Channel rental ──────────────────────────────────────────────

    async def rent_channel(
        self, user: User, request: RentChannelRequest
    ) -> MyChannelResponse:
        result = await self.db.execute(
            select(ChannelTemplate).where(
                ChannelTemplate.id == request.template_id,
                ChannelTemplate.is_published == True,
            )
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")

        trial_end = (
            datetime.now(timezone.utc) + timedelta(days=template.trial_days)
            if template.trial_days > 0
            else None
        )

        config = CustomerConfig(
            name=request.name or template.name,
            user_id=user.id,
            template_id=template.id,
            channel_category=template.category,
            plan="free_trial" if template.trial_days > 0 else "free",
            trial_ends_at=trial_end,
            welcome_message=template.default_welcome_message,
            offline_message=template.default_offline_message,
            theme=template.default_theme or {},
            skill_ids=template.default_skill_ids or [],
            position="right",
            enabled=True,
            widget_session_ttl_hours=24,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return MyChannelResponse.model_validate(config)

    # ── My channels ─────────────────────────────────────────────────

    async def list_my_channels(self, user: User) -> list[MyChannelResponse]:
        result = await self.db.execute(
            select(CustomerConfig)
            .where(CustomerConfig.user_id == user.id)
            .order_by(CustomerConfig.created_at.desc())
        )
        return [MyChannelResponse.model_validate(c) for c in result.scalars().all()]

    async def get_my_channel(self, user: User, channel_id: str) -> MyChannelResponse:
        result = await self.db.execute(
            select(CustomerConfig).where(
                CustomerConfig.id == channel_id,
                CustomerConfig.user_id == user.id,
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="Channel not found")
        return MyChannelResponse.model_validate(config)

    async def update_my_channel(
        self, user: User, channel_id: str, data: MyChannelUpdate
    ) -> MyChannelResponse:
        result = await self.db.execute(
            select(CustomerConfig).where(
                CustomerConfig.id == channel_id,
                CustomerConfig.user_id == user.id,
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="Channel not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
        await self.db.flush()
        await self.db.refresh(config)
        return MyChannelResponse.model_validate(config)

    async def delete_my_channel(self, user: User, channel_id: str) -> None:
        result = await self.db.execute(
            select(CustomerConfig).where(
                CustomerConfig.id == channel_id,
                CustomerConfig.user_id == user.id,
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="Channel not found")
        await self.db.delete(config)
        await self.db.flush()

    async def get_embed_code(
        self, user: User, channel_id: str
    ) -> EmbedCodeResponse:
        channel = await self.get_my_channel(user, channel_id)
        position = "right"
        if channel.theme:
            position = channel.theme.get("position", "right")
        embed = (
            '<script\n'
            '  src="/widget-loader.js"\n'
            '  data-mchat-url="/api"\n'
            f'  data-agent-id="{channel.id}"\n'
            f'  data-position="{position}"\n'
            '></script>'
        )
        return EmbedCodeResponse(
            agent_id=channel.id,
            embed_script=embed,
            widget_url=f"/widget?agentId={channel.id}",
        )

    # ── Dashboard ───────────────────────────────────────────────────

    async def get_dashboard_stats(self, user: User) -> PortalDashboardStats:
        result = await self.db.execute(
            select(func.count(CustomerConfig.id)).where(CustomerConfig.user_id == user.id)
        )
        total_channels = result.scalar() or 0

        result = await self.db.execute(
            select(func.count(CustomerConfig.id)).where(
                CustomerConfig.user_id == user.id, CustomerConfig.enabled == True
            )
        )
        active_channels = result.scalar() or 0

        result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user.id)
        )
        total_conversations = result.scalar() or 0

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.user_id == user.id, Message.created_at >= today_start
            )
        )
        messages_today = result.scalar() or 0

        # Aggregated usage across all user's channels
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(CustomerConfig.usage_messages_month), 0),
                func.coalesce(func.sum(CustomerConfig.usage_tokens_month), 0),
            ).where(CustomerConfig.user_id == user.id)
        )
        row = result.one_or_none()
        total_msgs, total_tokens = row if row else (0, 0)

        return PortalDashboardStats(
            total_channels=total_channels,
            active_channels=active_channels,
            total_conversations=total_conversations,
            messages_today=messages_today,
            total_messages_month=int(total_msgs),
            total_tokens_month=int(total_tokens),
        )
