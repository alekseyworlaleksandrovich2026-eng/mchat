"""Verify 9235.net SSO JWT and optional Redis share token."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from loguru import logger

from app.core.config import settings

PROVIDER = "patent9235"


def sso_login_url(*, redirect_after: str | None = None) -> str:
    """Build 9235 login URL with product SSO (same pattern as trade.9235.net)."""
    base = settings.patent9235_sso_login_url.rstrip("/")
    params = (
        f"sso=1&productId={settings.patent9235_sso_product_id}"
    )
    if redirect_after:
        from urllib.parse import quote

        params += f"&redirect_to={quote(redirect_after, safe='')}"
    return f"{base}?{params}"


def mchat_callback_url(origin: str) -> str:
    return f"{origin.rstrip('/')}/auth/9235"


def verify_xtk(xtk: str) -> dict[str, Any]:
    """
    Verify JWT from 9235 product auth redirect (?xtk=...).
    Returns claims: account (phone/email), optional uniqueKey.
    """
    secret = settings.patent9235_jwt_secret.strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="9235 SSO not configured (PATENT9235_JWT_SECRET)",
        )
    try:
        payload = jwt.decode(
            xtk,
            secret,
            algorithms=["HS512"],
            options={"verify_exp": True},
        )
    except JWTError as e:
        logger.warning("9235 JWT verify failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SSO token",
        ) from e
    account = payload.get("sub")
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SSO token subject",
        )
    return {
        "account": str(account),
        "unique_key": payload.get("uniqueKey"),
    }


async def fetch_9235_profile(account: str) -> dict[str, Any] | None:
    """
    Optional: load user profile from 9235 (requires future introspection API).
    For now returns minimal dict from JWT account only.
    """
    _ = account
    return None
