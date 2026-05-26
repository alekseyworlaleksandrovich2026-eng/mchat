"""Serve uploads from MinIO/S3 or local disk via same-origin /uploads URLs."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import Response
from loguru import logger

from app.core.config import settings
from app.exceptions import NotFoundError, PermissionDeniedError
from app.services.storage_service import storage_service
from app.utils.upload_paths import safe_upload_file_path
from app.utils.upload_tokens import verify_upload_token

router = APIRouter(tags=["Uploads"])


@router.get("/uploads/{file_path:path}")
async def get_upload(
    file_path: str,
    exp: int | None = Query(None),
    sig: str | None = Query(None),
) -> Response:
    key = (file_path or "").strip().lstrip("/")
    if not key or safe_upload_file_path(key) is None:
        raise NotFoundError("Not found")

    if exp is not None and sig:
        if not verify_upload_token(key, exp, sig):
            raise PermissionDeniedError("Invalid or expired upload token")
    elif settings.uploads_require_signed_access:
        raise PermissionDeniedError("Upload token required")
    elif not exp and not sig:
        logger.debug("Serving legacy tokenless upload: {}", key)

    result = await asyncio.to_thread(storage_service.fetch_bytes, key)
    if result is None:
        raise NotFoundError("Not found")

    data, media_type = result
    return Response(
        content=data,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )
