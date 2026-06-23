from local_ai_lab.vectorstores.base import RetrievedChunk


class IdentityReranker:
    """Default reranker that preserves vector-store order."""

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        del query
        return list(chunks)
