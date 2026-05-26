"""Tests for GET /uploads proxy."""

from pathlib import Path

import pytest
from httpx import AsyncClient

from app.utils.upload_tokens import signed_upload_url


@pytest.mark.asyncio
async def test_get_upload_with_valid_signature(client: AsyncClient, monkeypatch, tmp_path):
    root = tmp_path / "uploads"
    (root / "chat").mkdir(parents=True)
    (root / "chat" / "photo.png").write_bytes(b"\x89PNG")

    monkeypatch.setattr(
        "app.utils.upload_paths.resolve_upload_root",
        lambda raw=None: root,
    )

    url = signed_upload_url("chat/photo.png", ttl_seconds=3600)
    response = await client.get(url)
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_get_upload_rejects_invalid_signature(client: AsyncClient, monkeypatch, tmp_path):
    root = tmp_path / "uploads"
    (root / "chat").mkdir(parents=True)
    (root / "chat" / "photo.png").write_bytes(b"data")

    monkeypatch.setattr(
        "app.utils.upload_paths.resolve_upload_root",
        lambda raw=None: root,
    )

    response = await client.get("/uploads/chat/photo.png?exp=9999999999&sig=bad")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_upload_blocks_traversal(client: AsyncClient):
    response = await client.get("/uploads/../etc/passwd")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_upload_legacy_tokenless_allowed(client: AsyncClient, monkeypatch, tmp_path):
    root = tmp_path / "uploads"
    (root / "chat").mkdir(parents=True)
    (root / "chat" / "legacy.txt").write_bytes(b"legacy")

    monkeypatch.setattr(
        "app.utils.upload_paths.resolve_upload_root",
        lambda raw=None: root,
    )

    response = await client.get("/uploads/chat/legacy.txt")
    assert response.status_code == 200
    assert response.text == "legacy"
