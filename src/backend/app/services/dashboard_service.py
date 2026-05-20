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

    async def get_stats(self, user_id: str | None = None) -> DashboardStatsResponse:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_conv_stmt = select(func.count()).select_from(Conversation)
        active_conv_stmt = select(func.count()).select_from(Conversation).where(
            Conversation.status == "active"
        )
        total_agents_stmt = select(func.count()).select_from(CustomerConfig)
        total_docs_stmt = select(func.count()).select_from(Document).join(KnowledgeBase)
        total_skills_stmt = select(func.count()).select_from(Skill)
        messages_today_stmt = (
            select(func.count())
            .select_from(Message)
            .join(Conversation)
            .where(Message.created_at >= today_start)
        )

        if user_id is not None:
            total_conv_stmt = total_conv_stmt.where(Conversation.user_id == user_id)
            active_conv_stmt = active_conv_stmt.where(Conversation.user_id == user_id)
            total_agents_stmt = total_agents_stmt.where(CustomerConfig.user_id == user_id)
            total_docs_stmt = total_docs_stmt.where(KnowledgeBase.user_id == user_id)
            total_skills_stmt = total_skills_stmt.where(Skill.user_id == user_id)
            messages_today_stmt = messages_today_stmt.where(Conversation.user_id == user_id)

        total_conv = await self._scalar_count(total_conv_stmt)
        active_conv = await self._scalar_count(active_conv_stmt)
        total_agents = await self._scalar_count(total_agents_stmt)
        total_docs = await self._scalar_count(total_docs_stmt)
        total_skills = await self._scalar_count(total_skills_stmt)
        messages_today = await self._scalar_count(messages_today_stmt)

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

    async def get_activities(
        self, user_id: str | None = None, limit: int = 10
    ) -> list[DashboardActivity]:
        activities: list[DashboardActivity] = []

        conv_stmt = select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
        if user_id is not None:
            conv_stmt = conv_stmt.where(Conversation.user_id == user_id)
        conv_result = await self.db.execute(conv_stmt)
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

        doc_stmt = (
            select(Document)
            .join(KnowledgeBase)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        if user_id is not None:
            doc_stmt = doc_stmt.where(KnowledgeBase.user_id == user_id)
        doc_result = await self.db.execute(doc_stmt)
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
