"""Tests for retrieval observability."""

import pytest

from app.models.retrieval_log import RetrievalLog
from app.services.retrieval_log_service import RetrievalLogService


@pytest.mark.asyncio
async def test_record_and_stats(db_session):
    service = RetrievalLogService(db_session)
    await service.record(
        query="如何安装",
        knowledge_base_id="kb-1",
        user_id="user-1",
        retrieval_mode="hybrid",
        hit_count=0,
        duration_ms=42,
        hits=[],
        source="admin",
    )
    await service.record(
        query="如何安装",
        knowledge_base_id="kb-1",
        user_id="user-1",
        retrieval_mode="hybrid",
        hit_count=2,
        duration_ms=80,
        hits=[],
        source="chat",
    )
    await db_session.flush()

    stats = await service.get_stats(user_id="user-1", days=7)
    assert stats["total_searches"] == 2
    assert stats["zero_result_count"] == 1
    assert stats["zero_result_rate"] == 0.5
    assert stats["avg_duration_ms"] == 61.0
    assert stats["top_zero_result_queries"][0]["query"] == "如何安装"
