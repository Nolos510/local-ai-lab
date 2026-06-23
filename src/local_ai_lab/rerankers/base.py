from typing import Protocol

from local_ai_lab.vectorstores.base import RetrievedChunk


class Reranker(Protocol):
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Return chunks ordered for prompt assembly."""
