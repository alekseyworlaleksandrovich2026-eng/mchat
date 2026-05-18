"""Milvus client for vector storage and semantic search."""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.knowledge.milvus_runtime import get_milvus_runtime


class MilvusClient:
    """Async wrapper around Milvus vector database.

    Provides graceful fallback if Milvus is disabled or unreachable.
    """

    def __init__(self) -> None:
        self._connected = False
        self._collection_name = "document_chunks"
        self._dimension = 1536  # text-embedding-3-small default

    async def connect(self) -> bool:
        """Connect to Milvus server."""
        cfg = get_milvus_runtime()
        if not cfg.enabled:
            logger.info("Milvus is disabled, skipping connection")
            self._connected = False
            return False

        try:
            from pymilvus import connections

            if connections.has_connection("default"):
                connections.disconnect("default")

            connections.connect(
                alias="default",
                host=cfg.host,
                port=str(cfg.port),
            )
            self._connected = True
            logger.info(f"Connected to Milvus at {cfg.host}:{cfg.port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Milvus: {e}")
            self._connected = False
            return False

    async def reconnect(self) -> bool:
        """Disconnect and reconnect using current runtime settings."""
        await self.close()
        connected = await self.connect()
        if connected:
            await self.create_collection()
        return connected

    async def create_collection(self) -> bool:
        """Create the document chunks collection if it doesn't exist."""
        if not self._connected:
            return False

        try:
            from pymilvus import (
                Collection,
                CollectionSchema,
                DataType,
                FieldSchema,
                utility,
            )

            if utility.has_collection(self._collection_name):
                logger.info(
                    f"Collection '{self._collection_name}' already exists"
                )
                return True

            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True,
                ),
                FieldSchema(
                    name="document_id",
                    dtype=DataType.VARCHAR,
                    max_length=36,
                ),
                FieldSchema(
                    name="kb_id",
                    dtype=DataType.VARCHAR,
                    max_length=36,
                ),
                FieldSchema(
                    name="user_id",
                    dtype=DataType.VARCHAR,
                    max_length=36,
                ),
                FieldSchema(
                    name="chunk_index",
                    dtype=DataType.INT64,
                ),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self._dimension,
                ),
            ]

            schema = CollectionSchema(
                fields, description="Document chunks for RAG"
            )
            collection = Collection(
                name=self._collection_name, schema=schema
            )

            # Create IVF_FLAT index
            index_params = {
                "metric_type": "IP",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            collection.create_index(
                field_name="embedding", index_params=index_params
            )
            collection.load()

            logger.info(
                f"Created collection '{self._collection_name}' "
                f"with dimension {self._dimension}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create Milvus collection: {e}")
            return False

    async def insert_vectors(
        self,
        document_id: str,
        kb_id: str,
        user_id: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> int:
        """Insert document chunks with their embeddings into Milvus."""
        if not self._connected:
            return 0

        try:
            from pymilvus import Collection

            collection = Collection(self._collection_name)

            data = [
                [document_id] * len(chunks),
                [kb_id] * len(chunks),
                [user_id] * len(chunks),
                list(range(len(chunks))),
                chunks,
                embeddings,
            ]

            mr = collection.insert(data)
            collection.flush()
            logger.info(
                f"Inserted {len(chunks)} chunks for document {document_id}"
            )
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            return 0

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        user_id: str | None = None,
        kb_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks using embedding vector."""
        if not self._connected:
            return []

        try:
            from pymilvus import Collection

            collection = Collection(self._collection_name)
            collection.load()

            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10},
            }

            expr_parts: list[str] = []
            if user_id:
                expr_parts.append(f'user_id == "{user_id}"')
            if kb_id:
                expr_parts.append(f'kb_id == "{kb_id}"')
            expr = " and ".join(expr_parts) if expr_parts else None

            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=[
                    "document_id",
                    "kb_id",
                    "chunk_index",
                    "content",
                ],
            )

            hits = []
            for hits_list in results:
                for hit in hits_list:
                    hits.append(
                        {
                            "id": hit.id,
                            "distance": hit.distance,
                            "document_id": hit.entity.get("document_id"),
                            "kb_id": hit.entity.get("kb_id"),
                            "chunk_index": hit.entity.get("chunk_index"),
                            "content": hit.entity.get("content"),
                        }
                    )

            return hits
        except Exception as e:
            logger.error(f"Milvus search failed: {e}")
            return []

    async def delete_vectors(self, document_id: str) -> bool:
        """Delete all vectors for a document."""
        if not self._connected:
            return False

        try:
            from pymilvus import Collection

            collection = Collection(self._collection_name)
            collection.delete(f'document_id == "{document_id}"')
            collection.flush()
            logger.info(f"Deleted vectors for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False

    async def close(self) -> None:
        """Disconnect from Milvus."""
        if self._connected:
            try:
                from pymilvus import connections

                connections.disconnect("default")
                self._connected = False
                logger.info("Disconnected from Milvus")
            except Exception as e:
                logger.warning(f"Error disconnecting Milvus: {e}")


# Singleton instance
milvus_client = MilvusClient()
