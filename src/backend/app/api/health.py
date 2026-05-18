"""Health check API router."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Basic health check endpoint."""
    db_ok = False
    milvus_ok = None

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if settings.milvus_enabled:
        try:
            from pymilvus import connections
            milvus_ok = connections.has_connection("default")
        except Exception:
            milvus_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "milvus": (
            "connected" if milvus_ok
            else ("disabled" if milvus_ok is None else "disconnected")
        ),
    }


@router.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    import sys
    import time

    return {
        "uptime": time.time(),
        "python_version": sys.version,
        "platform": sys.platform,
    }
