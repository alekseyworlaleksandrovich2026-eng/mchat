"""Resolve upload directory consistently for storage and HTTP serving."""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def resolve_upload_root(raw: str | None = None) -> Path:
    """Return absolute upload root (relative paths are resolved from process cwd)."""
    value = (raw if raw is not None else settings.upload_dir or "").strip()
    if not value:
        value = "../../uploads"
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()
    return path


def safe_upload_file_path(key: str, *, root: Path | None = None) -> Path | None:
    """Map storage key to a path under upload root; None if traversal attempted."""
    root_dir = root or resolve_upload_root()
    key = (key or "").strip().lstrip("/")
    if not key or ".." in key.split("/"):
        return None
    full = (root_dir / key).resolve()
    try:
        full.relative_to(root_dir)
    except ValueError:
        return None
    return full
