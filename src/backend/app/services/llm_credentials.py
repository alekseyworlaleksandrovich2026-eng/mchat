"""Resolve LLM API keys from config, environment, or fallbacks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from loguru import logger

from app.core.config import settings
from app.models.ai_config import AIConfig


def is_usable_api_key(key: str | None) -> bool:
    k = (key or "").strip()
    if len(k) < 8:
        return False
    if "*" in k:
        return False
    if k.lower() in ("not-needed", "your-api-key", "sk-xxx", "changeme"):
        return False
    return True


def provider_env_api_key(provider: str) -> str:
    p = (provider or "").lower()
    env_map = {
        "openai": settings.openai_api_key,
        "deepseek": settings.deepseek_api_key,
        "moonshot": settings.moonshot_api_key,
        "openai-compatible": settings.openai_api_key,
        "zhipu": settings.zhipu_api_key,
        "groq": settings.groq_api_key,
        "siliconflow": settings.siliconflow_api_key,
        "together": settings.together_api_key,
    }
    return (env_map.get(p) or "").strip()


def resolve_api_key(provider: str, configured: str | None) -> str:
    """Prefer DB key, then provider-specific env (e.g. DEEPSEEK_API_KEY)."""
    if is_usable_api_key(configured):
        return (configured or "").strip()
    env_key = provider_env_api_key(provider)
    if env_key:
        return env_key
    return (configured or "").strip()


async def ensure_ai_config_api_key(
    db: AsyncSession, ai_config: AIConfig
) -> AIConfig:
    """Fill missing/invalid api_key from env or another config for the same provider."""
    resolved = resolve_api_key(ai_config.provider, ai_config.api_key)
    if is_usable_api_key(resolved):
        if resolved != (ai_config.api_key or ""):
            ai_config.api_key = resolved
        return ai_config

    result = await db.execute(
        select(AIConfig)
        .where(
            AIConfig.provider == ai_config.provider,
            AIConfig.api_key != "",
            AIConfig.id != ai_config.id,
        )
        .order_by(AIConfig.is_default.desc())
    )
    for fallback in result.scalars():
        fb_key = resolve_api_key(fallback.provider, fallback.api_key)
        if is_usable_api_key(fb_key):
            logger.warning(
                f"AI config {ai_config.id} has no valid API key; "
                f"using key from config {fallback.id} ({fallback.provider})"
            )
            ai_config.api_key = fb_key
            if not ai_config.api_base and fallback.api_base:
                ai_config.api_base = fallback.api_base
            return ai_config

    default_result = await db.execute(
        select(AIConfig).where(AIConfig.is_default == True, AIConfig.api_key != "")
    )
    default_cfg = default_result.scalar_one_or_none()
    if default_cfg and default_cfg.id != ai_config.id:
        fb_key = resolve_api_key(default_cfg.provider, default_cfg.api_key)
        if is_usable_api_key(fb_key):
            logger.warning(
                f"AI config {ai_config.id} has no valid API key; "
                f"using default config {default_cfg.id} ({default_cfg.provider})"
            )
            ai_config.api_key = fb_key
            if not ai_config.api_base and default_cfg.api_base:
                ai_config.api_base = default_cfg.api_base
            return ai_config

    return ai_config
