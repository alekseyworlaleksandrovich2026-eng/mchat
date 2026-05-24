"""LLM-based query rewriting for multi-recall retrieval."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from loguru import logger

ChatFn = Callable[[str], Awaitable[str]]


class QueryRewriter:
    """Generate alternative search queries to improve retrieval recall."""

    def __init__(self, chat_fn: ChatFn | None = None) -> None:
        self._chat_fn = chat_fn

    async def rewrite(self, query: str, count: int = 3) -> list[str]:
        """Return original query + up to count-1 rewritten variants."""
        if not self._chat_fn or count <= 1:
            return [query]

        prompt = (
            "You are a search query rewriter. Given a user's question, "
            f"generate {count - 1} alternative search queries that capture "
            "different phrasings, synonyms, or perspectives. "
            "Return one query per line, no numbering, no explanations.\n\n"
            f"Original question: {query}"
        )

        try:
            response = await self._chat_fn(prompt)
            alternatives = [
                line.strip().strip('"').strip("'")
                for line in response.strip().split("\n")
                if line.strip()
            ]
            all_queries = [query] + alternatives[: count - 1]
            seen: set[str] = set()
            unique = []
            for q in all_queries:
                q_clean = q.strip()
                if q_clean and q_clean not in seen:
                    seen.add(q_clean)
                    unique.append(q_clean)
            return unique
        except Exception as e:
            logger.warning(f"Query rewriting failed: {e}")
            return [query]
