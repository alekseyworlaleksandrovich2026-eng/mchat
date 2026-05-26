"""Tests for upload URL signing."""

import time

from app.utils.upload_tokens import (
    build_upload_token,
    signed_upload_url,
    verify_upload_token,
)


def test_signed_upload_url_round_trip():
    url = signed_upload_url("chat/abc.png", ttl_seconds=3600)
    assert url.startswith("/uploads/chat/abc.png?")
    assert "exp=" in url and "sig=" in url


def test_verify_upload_token_rejects_expired():
    key = "chat/old.png"
    exp = int(time.time()) - 10
    sig = build_upload_token(key, exp)
    assert not verify_upload_token(key, exp, sig)


def test_verify_upload_token_rejects_tampered_key():
    exp = int(time.time()) + 3600
    sig = build_upload_token("chat/a.png", exp)
    assert not verify_upload_token("chat/b.png", exp, sig)
