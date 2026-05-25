"""Align knowledge base embedding settings with global Milvus dimension."""

from __future__ import annotations

from loguru import logger

from app.core.config import settings
from app.knowledge.milvus_client import milvus_client
from app.models.knowledge import KnowledgeBase

_OPENAI_DEFAULT_DIM = 1536


def milvus_target_dimension() -> int:
    """Dimension used by the shared Milvus collection."""
    return int(milvus_client.dimension)


def align_kb_embedding_to_milvus(kb: KnowledgeBase) -> bool:
    """
    Force KB embedding fields to match runtime Milvus / global settings.

    MChat uses one Milvus collection; all KBs must share the same vector dimension.
    Returns True if any field was changed.
    """
    target_dim = milvus_target_dimension()
    changed = False

    provider = (settings.embedding_provider or "ollama").strip().lower()
    model = settings.embedding_model or "nomic-embed-text"
    if target_dim != _OPENAI_DEFAULT_DIM and provider in (
        "openai",
        "openai-compatible",
        "compatible",
    ):
        logger.warning(
            "EMBEDDING_DIMENSION={} is incompatible with {}; using ollama for KB {}",
            target_dim,
            provider,
            kb.id,
        )
        provider = "ollama"
        if model.startswith("text-embedding") or model.startswith("gpt-"):
            model = "nomic-embed-text"

    if kb.embedding_provider != provider:
        kb.embedding_provider = provider
        changed = True
    if kb.embedding_model != model:
        kb.embedding_model = model
        changed = True
    api_base = settings.embedding_api_base or None
    if (kb.embedding_api_base or None) != api_base:
        kb.embedding_api_base = api_base
        changed = True
    if int(kb.embedding_dimension or 0) != target_dim:
        kb.embedding_dimension = target_dim
        changed = True

    return changed
