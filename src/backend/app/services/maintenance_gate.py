"""Public API maintenance gate (settings.maintenance_mode)."""

from __future__ import annotations

from app.core.config import settings

_PUBLIC_MESSAGE_ZH = "系统维护中，请稍后再试。"
_PUBLIC_MESSAGE_EN = "System is under maintenance. Please try again later."


def maintenance_blocks_public() -> bool:
    return bool(getattr(settings, "maintenance_mode", False))


def maintenance_public_message(language: str | None = None) -> str:
    lang = (language or getattr(settings, "language", "") or "zh-CN").lower()
    if lang.startswith("en"):
        return _PUBLIC_MESSAGE_EN
    return _PUBLIC_MESSAGE_ZH


def ensure_public_api_available(language: str | None = None) -> None:
    """Raise HTTPException 503 when maintenance blocks tenant-facing APIs."""
    if not maintenance_blocks_public():
        return
    from fastapi import HTTPException

    raise HTTPException(
        status_code=503,
        detail={
            "message": maintenance_public_message(language),
            "maintenance": True,
        },
    )
