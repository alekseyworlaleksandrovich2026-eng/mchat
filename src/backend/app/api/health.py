"""Health check API router."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.knowledge.milvus_client import milvus_client
from app.knowledge.milvus_runtime import get_milvus_runtime

router = APIRouter()


def _milvus_health_status() -> str:
    """Reflect admin-persisted Milvus config and live connection, not .env defaults."""
    runtime = get_milvus_runtime()
    if not runtime.enabled:
        return "disabled"
    if milvus_client._connected:
        return "connected"
    return "disconnected"


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Basic health check endpoint."""
    db_ok = False

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "milvus": _milvus_health_status(),
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
