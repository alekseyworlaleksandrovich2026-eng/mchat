"""Dashboard API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class DashboardTrends(BaseModel):
    conversations: float = 0
    messages: float = 0
    documents: float = 0


class DashboardStatsResponse(BaseModel):
    total_conversations: int = 0
    active_conversations: int = 0
    total_agents: int = 0
    total_documents: int = 0
    total_skills: int = 0
    messages_today: int = 0
    avg_response_time: float = 0
    satisfaction_rate: float = 0
    trends: DashboardTrends = Field(default_factory=DashboardTrends)


class DashboardActivity(BaseModel):
    id: str
    type: str
    description: str
    timestamp: datetime
