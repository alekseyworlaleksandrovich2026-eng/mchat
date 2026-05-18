"""RAG service - retrieve and augment prompts with knowledge."""

from __future__ import annotations

from loguru import logger

from app.knowledge.embedder import embedder
from app.knowledge.milvus_client import milvus_client
from app.schemas.knowledge import SearchResponse, SearchResult


class RagService:
    """Retrieval-Augmented Generation service."""

    async def search(
        self,
        query: str,
        user_id: str | None = None,
        knowledge_base_id: str | None = None,
        top_k: int = 5,
    ) -> SearchResponse:
        """Search for relevant document chunks.

        Steps:
        1. Try Milvus vector search (when available)
        2. Fall back to keyword search (for dev/no-Milvus environments)
        3. Return results
        """
        try:
            if milvus_client._connected:
                # Vector search via Milvus
                query_embedding = await embedder.embed_query(query)
                hits = await milvus_client.search(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    user_id=user_id,
                    kb_id=knowledge_base_id,
                )
                results = []
                for hit in hits:
                    results.append(
                        SearchResult(
                            document_id=hit.get("document_id", ""),
                            title=f"Chunk {hit.get('chunk_index', 0)}",
                            content=hit.get("content", ""),
                            score=float(hit.get("distance", 0)),
                            knowledge_base_id=hit.get("kb_id", ""),
                        )
                    )
                return SearchResponse(results=results, total=len(results))
            else:
                # Fallback: simple keyword matching from SQL
                return await self._keyword_search(
                    query=query,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    top_k=top_k,
                )
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return SearchResponse(results=[], total=0)

    async def _keyword_search(
        self,
        query: str,
        user_id: str | None = None,
        knowledge_base_id: str | None = None,
        top_k: int = 5,
    ) -> SearchResponse:
        """Simple keyword-based search fallback for dev environments."""
        from app.core.database import async_session_factory
        from app.models.knowledge import Document
        from sqlalchemy import select, or_

        try:
            async with async_session_factory() as db:
                stmt = select(Document).where(Document.status == "indexed")
                if knowledge_base_id:
                    stmt = stmt.where(
                        Document.knowledge_base_id == knowledge_base_id
                    )
                if user_id:
                    # Join through KnowledgeBase
                    from app.models.knowledge import KnowledgeBase
                    stmt = (
                        select(Document)
                        .join(KnowledgeBase)
                        .where(
                            Document.status == "indexed",
                            KnowledgeBase.user_id == user_id,
                        )
                    )
                    if knowledge_base_id:
                        stmt = stmt.where(
                            Document.knowledge_base_id == knowledge_base_id
                        )

                result = await db.execute(stmt)
                docs = result.scalars().all()

                # Score by keyword overlap
                query_terms = set(query.lower().split())
                scored = []
                for doc in docs:
                    content_lower = (doc.content or "").lower()
                    title_lower = (doc.title or "").lower()
                    # Simple overlap score
                    hits = sum(
                        1 for t in query_terms
                        if t in content_lower or t in title_lower
                    )
                    if hits > 0:
                        # Normalize score
                        score = hits / max(len(query_terms), 1)
                        scored.append((score, doc))

                # Sort by score and take top_k
                scored.sort(key=lambda x: x[0], reverse=True)
                results = []
                for score, doc in scored[:top_k]:
                    results.append(
                        SearchResult(
                            document_id=doc.id,
                            title=doc.title or "Untitled",
                            content=doc.content or "",
                            score=score,
                            knowledge_base_id=doc.knowledge_base_id,
                        )
                    )

                return SearchResponse(results=results, total=len(results))
        except Exception as e:
            logger.error(f"Keyword search fallback failed: {e}")
            return SearchResponse(results=[], total=0)

    async def augment_prompt(
        self,
        query: str,
        user_id: str | None = None,
        knowledge_base_id: str | None = None,
    ) -> str | None:
        """Build an augmented prompt with relevant context.

        Returns formatted context string, or None if no relevant context found.
        """
        search_results = await self.search(
            query=query,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            top_k=3,
        )

        if not search_results.results:
            return None

        context_parts = []
        for r in search_results.results:
            context_parts.append(
                f"[Source: {r.title}] (relevance: {r.score:.2f})\n{r.content}"
            )

        return "\n\n".join(context_parts)
