from typing import Any

from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.deterministic import DeterministicEmbeddingProvider
from local_ai_lab.llms.mock import MockChatProvider
from local_ai_lab.rag.service import RAGService
from local_ai_lab.vectorstores.base import RetrievedChunk


class FakeVectorStore:
    def search(self, vector: list[float], *, top_k: int) -> list[RetrievedChunk]:
        del vector
        assert top_k == 1
        return [
            RetrievedChunk(
                id="chunk-1",
                text="The lab runs local RAG on Apple Silicon.",
                score=0.9,
                metadata={"source_path": "sample.md", "source_name": "sample.md", "chunk_index": 0},
            )
        ]

    def upsert_chunks(self, chunks: list[Any], vectors: list[list[float]]) -> None:
        del chunks, vectors


def test_rag_service_ask_returns_answer_and_citations() -> None:
    service = RAGService(
        settings=Settings(llm_provider="mock", top_k=1),
        embedding_provider=DeterministicEmbeddingProvider(vector_size=32),
        vector_store=FakeVectorStore(),
        chat_provider=MockChatProvider(),
    )

    result = service.ask("What does the lab run?", top_k=1)

    assert "Mock local answer" in result.answer
    assert result.citations[0].source_name == "sample.md"
    assert result.retrieved_chunks[0]["id"] == "chunk-1"
