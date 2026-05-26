"""Persist and aggregate RAG retrieval logs."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.rerank import RankedChunk
from app.models.retrieval_log import RetrievalLog


def _hits_summary(chunks: list[RankedChunk], *, limit: int = 10) -> list[dict]:
    out: list[dict] = []
    for c in chunks[:limit]:
        out.append(
            {
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "title": c.title,
                "vector_score": round(c.vector_score, 4),
                "keyword_score": round(c.keyword_score, 4),
                "fused_score": round(c.fused_score, 4),
                "rerank_score": round(c.rerank_score, 4),
                "final_score": round(c.final_score, 4),
            }
        )
    return out


class RetrievalLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record(
        self,
        *,
        query: str,
        knowledge_base_id: str | None,
        user_id: str | None,
        retrieval_mode: str,
        hit_count: int,
        duration_ms: int,
        hits: list[RankedChunk],
        query_variant_count: int = 1,
        conversation_id: str | None = None,
        source: str = "chat",
    ) -> None:
        row = RetrievalLog(
            query=(query or "")[:4000],
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            conversation_id=conversation_id,
            source=source,
            query_variant_count=max(1, query_variant_count),
            retrieval_mode=retrieval_mode or "hybrid",
            hit_count=hit_count,
            zero_result=hit_count <= 0,
            duration_ms=max(0, duration_ms),
            hits_summary=_hits_summary(hits) if hits else [],
        )
        self.db.add(row)
        await self.db.flush()

    async def get_stats(
        self, *, user_id: str | None = None, days: int = 7
    ) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 90)))
        filters = [RetrievalLog.created_at >= since]
        if user_id:
            filters.append(RetrievalLog.user_id == user_id)

        total = (
            await self.db.execute(
                select(func.count()).select_from(RetrievalLog).where(*filters)
            )
        ).scalar() or 0
        zero_count = (
            await self.db.execute(
                select(func.count())
                .select_from(RetrievalLog)
                .where(*filters, RetrievalLog.zero_result == True)  # noqa: E712
            )
        ).scalar() or 0
        avg_ms = (
            await self.db.execute(
                select(func.avg(RetrievalLog.duration_ms)).where(*filters)
            )
        ).scalar() or 0

        top_zero = await self.db.execute(
            select(RetrievalLog.query, func.count())
            .where(*filters, RetrievalLog.zero_result == True)  # noqa: E712
            .group_by(RetrievalLog.query)
            .order_by(func.count().desc())
            .limit(10)
        )
        zero_queries = [
            {"query": (q or "")[:200], "count": int(c)}
            for q, c in top_zero.all()
        ]

        return {
            "period_days": days,
            "total_searches": int(total),
            "zero_result_count": int(zero_count),
            "zero_result_rate": round(zero_count / total, 4) if total else 0.0,
            "avg_duration_ms": round(float(avg_ms), 1),
            "top_zero_result_queries": zero_queries,
        }


class RetrievalTimer:
    """Simple wall-clock timer for retrieval logging."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    @property
    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)
