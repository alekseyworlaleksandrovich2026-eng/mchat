"""Portal service — user-facing channel rental business logic."""

from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import AIConfig
from app.services.llm_credentials import is_usable_api_key, resolve_api_key
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

        # Prevent duplicate channels from the same template
        dup_result = await self.db.execute(
            select(CustomerConfig).where(
                CustomerConfig.user_id == user.id,
                CustomerConfig.template_id == request.template_id,
            )
        )
        if dup_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="You already have a channel from this template",
            )

        trial_end = (
            datetime.now(timezone.utc) + timedelta(days=template.trial_days)
            if template.trial_days > 0
            else None
        )

        # Use template's referenced AI config, or create from spec
        ai_config_id = None
        if template.default_ai_config_id:
            # Verify the referenced config exists
            result = await self.db.execute(
                select(AIConfig).where(AIConfig.id == template.default_ai_config_id)
            )
            if result.scalar_one_or_none() is not None:
                ai_config_id = template.default_ai_config_id
        if ai_config_id is None:
            default_result = await self.db.execute(
                select(AIConfig).where(AIConfig.is_default == True)
            )
            platform_default = default_result.scalar_one_or_none()
            if platform_default is not None:
                key = resolve_api_key(
                    platform_default.provider, platform_default.api_key
                )
                if is_usable_api_key(key):
                    ai_config = AIConfig(
                        name=f"{template.name} AI",
                        user_id=user.id,
                        provider=platform_default.provider,
                        model=platform_default.model,
                        api_key=key,
                        api_base=platform_default.api_base,
                        system_prompt=(
                            platform_default.system_prompt
                            or (template.default_ai_config_spec or {}).get(
                                "system_prompt", ""
                            )
                        ),
                        temperature=platform_default.temperature,
                        max_tokens=platform_default.max_tokens,
                    )
                    self.db.add(ai_config)
                    await self.db.flush()
                    ai_config_id = ai_config.id

        if ai_config_id is None:
            ai_spec = template.default_ai_config_spec or {}
            if ai_spec:
                ai_config = AIConfig(
                    name=f"{template.name} AI",
                    user_id=user.id,
                    provider=ai_spec.get("provider", "openai"),
                    model=ai_spec.get("model", "gpt-4o-mini"),
                    api_key=ai_spec.get("api_key", ""),
                    system_prompt=ai_spec.get("system_prompt", ""),
                    temperature=ai_spec.get("temperature", 0.7),
                    max_tokens=ai_spec.get("max_tokens", 2048),
                )
                self.db.add(ai_config)
                await self.db.flush()
                ai_config_id = ai_config.id

        knowledge_base_ids: list[str] = []
        if template.default_knowledge_base_ids:
            knowledge_base_ids.extend(
                [str(k) for k in template.default_knowledge_base_ids if k]
            )
        if not knowledge_base_ids:
            kb_id = await self._create_kb_from_spec(
                user, template.default_knowledge_base_spec or {}
            )
            if kb_id:
                knowledge_base_ids.append(kb_id)

        config = CustomerConfig(
            name=request.name or template.name,
            user_id=user.id,
            template_id=template.id,
            ai_config_id=ai_config_id,
            channel_category=template.category,
            plan="free_trial" if template.trial_days > 0 else "free",
            trial_ends_at=trial_end,
            welcome_message=template.default_welcome_message,
            offline_message=template.default_offline_message,
            theme=template.default_theme or {},
            skill_ids=template.default_skill_ids or [],
            knowledge_base_ids=knowledge_base_ids or None,
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

    async def _get_owned_channel(
        self, user: User, channel_id: str
    ) -> CustomerConfig:
        result = await self.db.execute(
            select(CustomerConfig).where(
                CustomerConfig.id == channel_id,
                CustomerConfig.user_id == user.id,
            )
        )
        channel = result.scalar_one_or_none()
        if channel is None:
            raise HTTPException(status_code=404, detail="Channel not found")
        return channel

    async def _create_kb_from_spec(
        self, user: User, spec: dict
    ) -> str | None:
        """Create a knowledge base from template spec; returns kb id or None."""
        if not spec or not spec.get("name"):
            return None
        from app.schemas.knowledge import KnowledgeBaseCreate
        from app.services.knowledge_service import KnowledgeService

        field_names = set(KnowledgeBaseCreate.model_fields.keys())
        extra = {
            k: v
            for k, v in spec.items()
            if k in field_names and k not in ("name", "description", "enabled")
        }
        kb = await KnowledgeService(self.db).create_knowledge_base(
            user.id,
            KnowledgeBaseCreate(
                name=str(spec["name"]),
                description=spec.get("description"),
                enabled=bool(spec.get("enabled", True)),
                **extra,
            ),
        )
        return kb.id

    async def list_channel_knowledge_bases(
        self, user: User, channel_id: str
    ) -> list[dict]:
        from app.models.knowledge import Document, KnowledgeBase

        channel = await self._get_owned_channel(user, channel_id)
        kb_ids = list(channel.knowledge_base_ids or [])
        if not kb_ids:
            return []
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id.in_(kb_ids))
        )
        kb_by_id = {kb.id: kb for kb in result.scalars().all()}
        items = []
        for kb_id in kb_ids:
            kb = kb_by_id.get(kb_id)
            if kb is None:
                continue
            doc_count_result = await self.db.execute(
                select(func.count(Document.id)).where(
                    Document.knowledge_base_id == kb.id
                )
            )
            doc_count = doc_count_result.scalar() or 0
            is_owned = kb.user_id == user.id
            items.append(
                {
                    "id": kb.id,
                    "name": kb.name,
                    "description": kb.description,
                    "enabled": kb.enabled,
                    "document_count": int(doc_count),
                    "source": "owned" if is_owned else "system",
                    "can_upload": is_owned,
                    "can_delete": True,
                }
            )
        return items

    async def create_channel_knowledge_base(
        self, user: User, channel_id: str, data: dict
    ) -> dict:
        from app.schemas.knowledge import KnowledgeBaseCreate
        from app.services.knowledge_service import KnowledgeService

        channel = await self._get_owned_channel(user, channel_id)
        kb = await KnowledgeService(self.db).create_knowledge_base(
            user.id,
            KnowledgeBaseCreate(
                name=data.get("name") or f"{channel.name} 知识库",
                description=data.get("description"),
                enabled=data.get("enabled", True),
            ),
        )
        ids = list(channel.knowledge_base_ids or [])
        if kb.id not in ids:
            ids.append(kb.id)
        channel.knowledge_base_ids = ids
        await self.db.flush()
        return {"id": kb.id, "name": kb.name}

    async def import_channel_document(
        self,
        user: User,
        channel_id: str,
        kb_id: str,
        file,
    ):
        from app.models.knowledge import KnowledgeBase
        from app.services.knowledge_service import KnowledgeService

        channel = await self._get_owned_channel(user, channel_id)
        kb_ids = list(channel.knowledge_base_ids or [])
        if kb_id not in kb_ids:
            raise HTTPException(
                status_code=403,
                detail="Knowledge base not linked to this channel",
            )
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if kb.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="System knowledge bases are read-only",
            )
        return await KnowledgeService(self.db).import_file(
            kb_id=kb_id,
            user_id=user.id,
            file=file,
        )

    async def remove_channel_knowledge_base(
        self, user: User, channel_id: str, kb_id: str
    ) -> dict:
        """Unlink KB from channel; delete the KB only when owned by the user."""
        from app.models.knowledge import KnowledgeBase
        from app.services.knowledge_service import KnowledgeService

        channel = await self._get_owned_channel(user, channel_id)
        kb_ids = list(channel.knowledge_base_ids or [])
        if kb_id not in kb_ids:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        kb_result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            kb_ids = [x for x in kb_ids if x != kb_id]
            channel.knowledge_base_ids = kb_ids or None
            await self.db.flush()
            return {"ok": True, "deleted": False}

        kb_ids = [x for x in kb_ids if x != kb_id]
        channel.knowledge_base_ids = kb_ids or None
        deleted = False
        if kb.user_id == user.id:
            deleted = await KnowledgeService(self.db).delete_knowledge_base(
                kb_id, user.id
            )
        await self.db.flush()
        return {"ok": True, "deleted": deleted, "source": "owned" if deleted else "system"}
