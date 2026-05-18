"""Dashboard statistics service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.models.knowledge import Document, KnowledgeBase
from app.models.message import Message
from app.models.skill import Skill
from app.schemas.dashboard import (
    DashboardActivity,
    DashboardStatsResponse,
    DashboardTrends,
)


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self, user_id: str) -> DashboardStatsResponse:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_conv = await self._scalar_count(
            select(func.count()).select_from(Conversation).where(
                Conversation.user_id == user_id
            )
        )
        active_conv = await self._scalar_count(
            select(func.count()).select_from(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.status == "active",
            )
        )
        total_agents = await self._scalar_count(
            select(func.count()).select_from(CustomerConfig).where(
                CustomerConfig.user_id == user_id
            )
        )
        total_docs = await self._scalar_count(
            select(func.count())
            .select_from(Document)
            .join(KnowledgeBase)
            .where(KnowledgeBase.user_id == user_id)
        )
        total_skills = await self._scalar_count(
            select(func.count()).select_from(Skill).where(Skill.user_id == user_id)
        )
        messages_today = await self._scalar_count(
            select(func.count())
            .select_from(Message)
            .join(Conversation)
            .where(
                Conversation.user_id == user_id,
                Message.created_at >= today_start,
            )
        )

        return DashboardStatsResponse(
            total_conversations=total_conv,
            active_conversations=active_conv,
            total_agents=total_agents,
            total_documents=total_docs,
            total_skills=total_skills,
            messages_today=messages_today,
            avg_response_time=0,
            satisfaction_rate=0,
            trends=DashboardTrends(),
        )

    async def get_activities(self, user_id: str, limit: int = 10) -> list[DashboardActivity]:
        activities: list[DashboardActivity] = []

        conv_result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        for conv in conv_result.scalars().all():
            title = conv.title or "新对话"
            activities.append(
                DashboardActivity(
                    id=conv.id,
                    type="conversation",
                    description=f"对话：{title}",
                    timestamp=conv.updated_at,
                )
            )

        doc_result = await self.db.execute(
            select(Document)
            .join(KnowledgeBase)
            .where(KnowledgeBase.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        for doc in doc_result.scalars().all():
            activities.append(
                DashboardActivity(
                    id=doc.id,
                    type="document",
                    description=f"文档：{doc.title}",
                    timestamp=doc.created_at,
                )
            )

        activities.sort(key=lambda a: a.timestamp, reverse=True)
        return activities[:limit]

    async def _scalar_count(self, stmt) -> int:
        result = await self.db.execute(stmt)
        return int(result.scalar() or 0)
