"""Embedding service - API, Ollama, and locally uploaded models."""

from __future__ import annotations

import asyncio
import hashlib

import httpx
from loguru import logger
from openai import AsyncOpenAI

from app.core.config import settings
from app.knowledge.rag_config import EmbeddingConfig


class EmbeddingService:
    """Generates embeddings using configured provider."""

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self._config = config or EmbeddingConfig()
        self.provider = self._config.resolved_provider()
        self.model = self._config.resolved_model()
        self.api_base = self._config.resolved_api_base()
        self.dimension = self._config.resolved_dimension()
        self._client: AsyncOpenAI | None = None

    def _cache_key(self, text: str) -> str:
        raw = f"{self.provider}:{self.model}:{self.api_base}:{text}"
        return hashlib.md5(raw.encode()).hexdigest()

    async def _get_client(self) -> AsyncOpenAI:
        if self._client is not None:
            return self._client

        provider = self.provider
        if provider in ("openai", "openai-compatible", "compatible"):
            kwargs: dict = {}
            if self.api_base:
                kwargs["base_url"] = self.api_base
            self._client = AsyncOpenAI(**kwargs)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

        return self._client

    async def embed_query(self, text: str) -> list[float]:
        return await self._embed(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "local":
            from app.knowledge.local_embedder import embed_texts

            return await embed_texts(self.model, texts)
        if self.provider == "ollama":
            return [await self._embed_ollama(t) for t in texts]
        return [await self._embed(t) for t in texts]

    async def _embed(self, text: str) -> list[float]:
        if self.provider == "local":
            from app.knowledge.local_embedder import embed_text

            return await embed_text(self.model, text)
        if self.provider == "ollama":
            return await self._embed_ollama(text)

        cache_key = self._cache_key(text)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            client = await self._get_client()
            response = await client.embeddings.create(
                input=text.replace("\n", " "),
                model=self.model,
            )
            embedding = list(response.data[0].embedding)
            self._set_cache(cache_key, embedding)
            return embedding
        except Exception as e:
            logger.error(f"Embedding failed ({self.provider}/{self.model}): {e}")
            return [0.0] * self.dimension

    async def _embed_ollama(self, text: str) -> list[float]:
        base = (self.api_base or "http://localhost:11434").rstrip("/")
        url = f"{base}/api/embeddings"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json={"model": self.model, "prompt": text.replace("\n", " ")},
                )
                response.raise_for_status()
                data = response.json()
                embedding = list(data.get("embedding") or [])
                if embedding:
                    return embedding
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
        return [0.0] * self.dimension

    _cache: dict[str, list[float]] = {}

    def _get_cached(self, key: str) -> list[float] | None:
        return self._cache.get(key)

    def _set_cache(self, key: str, value: list[float]) -> None:
        if len(self._cache) > 1000:
            self._cache.clear()
        self._cache[key] = value


def embedder_for_config(config: EmbeddingConfig | None = None) -> EmbeddingService:
    return EmbeddingService(config)


embedder = EmbeddingService()
