"""Runtime Milvus connection settings (env defaults + DB overrides)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass
class MilvusRuntimeConfig:
    enabled: bool
    host: str
    port: int


_runtime = MilvusRuntimeConfig(
    enabled=settings.milvus_enabled,
    host=settings.milvus_host,
    port=settings.milvus_port,
)


def get_milvus_runtime() -> MilvusRuntimeConfig:
    return _runtime


def apply_milvus_runtime(*, enabled: bool, host: str, port: int) -> None:
    global _runtime
    _runtime = MilvusRuntimeConfig(
        enabled=enabled,
        host=host.strip() or settings.milvus_host,
        port=int(port),
    )
