"""Filesystem paths for uploaded embedding models."""

from pathlib import Path

from app.core.config import settings


def embedding_models_root() -> Path:
    root = settings.upload_path / "embedding_models"
    root.mkdir(parents=True, exist_ok=True)
    return root


def embedding_model_storage_path(model_id: str) -> Path:
    return embedding_models_root() / model_id
