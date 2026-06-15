"""Write report artifacts under MCHAT_UPLOAD_DIR (works in MChat backend and sidecar)."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


def sanitize_filename(name: str, *, default: str = "patent-report") -> str:
    text = (name or "").strip()
    text = re.sub(r'[\\/:*?"<>|]+', "-", text)
    text = re.sub(r"\s+", "-", text).strip("-._")
    return text or default


def _resolve_upload_root() -> Path:
    """Platform upload root (served by GET /uploads). Do not use tenant workspace uploads."""
    try:
        from app.utils.upload_paths import resolve_upload_root as platform_root

        root = platform_root()
        root.mkdir(parents=True, exist_ok=True)
        return root
    except ImportError:
        pass
    raw = (os.environ.get("UPLOAD_DIR") or os.environ.get("MCHAT_UPLOAD_DIR") or "").strip()
    if raw:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    fallback = Path.cwd() / "uploads"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback.resolve()


def _signed_upload_url(key: str) -> str:
    try:
        from app.utils.upload_tokens import signed_upload_url

        return signed_upload_url(key)
    except ImportError:
        pass
    secret = (
        os.environ.get("MCHAT_JWT_SECRET")
        or os.environ.get("JWT_SECRET")
        or ""
    ).strip()
    if secret:
        exp = int(time.time()) + 86400 * 365
        payload = f"{key}\n{exp}"
        sig = hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        params = urlencode({"exp": exp, "sig": sig})
        return f"/uploads/{key}?{params}"
    return f"/uploads/{key}"


def report_output_dir(prefix: str | None = None) -> tuple[Path, str]:
    upload_root = _resolve_upload_root()
    subdir = sanitize_filename(prefix or "", default=str(uuid.uuid4())[:8])
    key_prefix = f"workflow_reports/{subdir}"
    out_dir = upload_root / key_prefix
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir, key_prefix


def file_artifact(path: Path, key: str, *, fmt: str) -> dict[str, Any]:
    return {
        "format": fmt,
        "filename": path.name,
        "path": str(path),
        "key": key,
        "url": _signed_upload_url(key),
    }
