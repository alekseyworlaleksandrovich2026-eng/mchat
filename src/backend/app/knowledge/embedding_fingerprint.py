"""Track which embedding config was used for last successful index."""

from __future__ import annotations

from app.knowledge.rag_config import KnowledgeBaseRagSettings, rag_settings_from_kb
from app.models.knowledge import KnowledgeBase


def embedding_fingerprint_from_settings(settings: KnowledgeBaseRagSettings) -> str:
    emb = settings.embedding_config()
    base = emb.resolved_api_base() or ""
    return (
        f"{emb.resolved_provider()}|{emb.resolved_model()}|"
        f"{emb.resolved_dimension()}|{base}"
    )


def embedding_fingerprint(kb: KnowledgeBase) -> str:
    return embedding_fingerprint_from_settings(rag_settings_from_kb(kb))


def needs_reindex(kb: KnowledgeBase) -> bool:
    """True when KB embedding config differs from last indexed fingerprint."""
    current = embedding_fingerprint(kb)
    stored = (getattr(kb, "indexed_embedding_key", None) or "").strip()
    if not stored:
        return False
    return stored != current
