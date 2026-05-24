"""Load user-uploaded embedding models via sentence-transformers."""

from __future__ import annotations

import asyncio
from pathlib import Path
from threading import Lock

from loguru import logger

from app.knowledge.model_storage import embedding_model_storage_path

_MODEL_CACHE: dict[str, object] = {}
_CACHE_LOCK = Lock()


def _require_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "本地 Embedding 需要安装 sentence-transformers："
            "pip install sentence-transformers"
        ) from exc
    return SentenceTransformer


def _load_model(model_id: str) -> object:
    with _CACHE_LOCK:
        cached = _MODEL_CACHE.get(model_id)
        if cached is not None:
            return cached

        path = embedding_model_storage_path(model_id)
        if not path.is_dir():
            raise FileNotFoundError(f"Embedding model directory not found: {model_id}")

        SentenceTransformer = _require_sentence_transformers()
        logger.info(f"Loading local embedding model from {path}")
        model = SentenceTransformer(str(path))
        _MODEL_CACHE[model_id] = model
        return model


def unload_model(model_id: str) -> None:
    with _CACHE_LOCK:
        _MODEL_CACHE.pop(model_id, None)


def probe_model_dimension(model_dir: Path) -> int:
    """Load model once to read output dimension (does not keep in cache)."""
    SentenceTransformer = _require_sentence_transformers()
    model = SentenceTransformer(str(model_dir))
    return int(model.get_sentence_embedding_dimension())


def _encode_sync(model_id: str, texts: list[str]) -> list[list[float]]:
    model = _load_model(model_id)
    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return [vec.tolist() for vec in vectors]


async def embed_texts(model_id: str, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return await asyncio.to_thread(_encode_sync, model_id, texts)


async def embed_text(model_id: str, text: str) -> list[float]:
    rows = await embed_texts(model_id, [text])
    return rows[0] if rows else []
