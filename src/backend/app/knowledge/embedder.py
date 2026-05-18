"""Embedding service - generate embeddings for documents and queries."""

from __future__ import annotations

import hashlib
from functools import lru_cache

from loguru import logger

from app.core.config import settings


class EmbeddingService:
    """Generates embeddings using configured provider."""

    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.model = settings.embedding_model
        self._client = None

    async def _get_client(self):
        """Lazy-init the embedding client."""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI()
        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.provider}"
            )

        return self._client

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a query string."""
        return await self._embed(text)

    async def embed_documents(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        if not texts:
            return []

        embeddings = []
        for text in texts:
            emb = await self._embed(text)
            embeddings.append(emb)

        return embeddings

    async def _embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            client = await self._get_client()
            response = await client.embeddings.create(
                input=text.replace("\n", " "),
                model=self.model,
            )
            embedding = response.data[0].embedding

            # Cache the result
            self._set_cache(cache_key, embedding)

            return embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

    # Simple in-memory cache
    _cache: dict[str, list[float]] = {}

    def _get_cached(self, key: str) -> list[float] | None:
        return self._cache.get(key)

    def _set_cache(self, key: str, value: list[float]) -> None:
        if len(self._cache) > 1000:
            # Simple LRU: clear half when full
            self._cache.clear()
        self._cache[key] = value


embedder = EmbeddingService()
