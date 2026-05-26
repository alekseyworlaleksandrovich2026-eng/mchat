"""Signed access tokens for same-origin /uploads URLs."""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import urlencode

from app.core.config import settings

DEFAULT_UPLOAD_URL_TTL_SECONDS = 60 * 60 * 24 * 365


def _signing_key() -> bytes:
    return (settings.jwt_secret or "change-this").encode("utf-8")


def build_upload_token(key: str, exp: int) -> str:
    payload = f"{key}\n{exp}"
    return hmac.new(
        _signing_key(), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_upload_token(key: str, exp: int, sig: str) -> bool:
    if not sig or exp <= 0:
        return False
    if exp < int(time.time()):
        return False
    expected = build_upload_token(key, exp)
    return hmac.compare_digest(expected, sig)


def signed_upload_url(
    key: str,
    *,
    ttl_seconds: int | None = None,
) -> str:
    ttl = ttl_seconds if ttl_seconds is not None else settings.uploads_signed_url_ttl_seconds
    exp = int(time.time()) + max(60, int(ttl))
    sig = build_upload_token(key, exp)
    params = urlencode({"exp": exp, "sig": sig})
    return f"/uploads/{key}?{params}"
