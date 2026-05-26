"""Tests for storage_service fetch/save helpers."""

from app.services.storage_service import storage_service


def test_save_and_fetch_local_bytes(monkeypatch, tmp_path):
    root = tmp_path / "uploads"

    def fake_root(raw=None):
        return root

    monkeypatch.setattr("app.utils.upload_paths.resolve_upload_root", fake_root)
    monkeypatch.setattr("app.services.storage_service.resolve_upload_root", fake_root)
    monkeypatch.setattr(
        "app.services.storage_service.settings.storage_backend",
        "local",
    )

    stored = storage_service.save_bytes(
        b"hello",
        filename="note.txt",
        content_type="text/plain",
        prefix="chat",
    )
    assert stored.key.startswith("chat/")
    assert stored.url.startswith("/uploads/chat/")
    assert "sig=" in stored.url

    fetched = storage_service.fetch_bytes(stored.key)
    assert fetched is not None
    data, mime = fetched
    assert data == b"hello"
    assert mime == "text/plain"


def test_fetch_bytes_missing_returns_none(monkeypatch, tmp_path):
    root = tmp_path / "uploads"
    root.mkdir()

    def fake_root(raw=None):
        return root

    monkeypatch.setattr("app.utils.upload_paths.resolve_upload_root", fake_root)
    monkeypatch.setattr("app.services.storage_service.resolve_upload_root", fake_root)
    assert storage_service.fetch_bytes("chat/missing.txt") is None
