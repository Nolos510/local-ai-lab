from typing import Any

from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.deterministic import DeterministicEmbeddingProvider
from local_ai_lab.llms.mock import MockChatProvider
from local_ai_lab.rag.service import RAGService
from local_ai_lab.vectorstores.base import RetrievedChunk


class FakeVectorStore:
    def search(
        self,
        vector: list[float],
        *,
        top_k: int,
        query_text: str | None = None,
        retrieval_mode: str = "dense",
    ) -> list[RetrievedChunk]:
        del vector, query_text
        assert top_k == 1
        assert retrieval_mode == "dense"
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


class TwoChunkVectorStore:
    def __init__(self) -> None:
        self.seen_query_text: str | None = None
        self.seen_retrieval_mode = ""

    def search(
        self,
        vector: list[float],
        *,
        top_k: int,
        query_text: str | None = None,
        retrieval_mode: str = "dense",
    ) -> list[RetrievedChunk]:
        del vector, top_k
        self.seen_query_text = query_text
        self.seen_retrieval_mode = retrieval_mode
        return [
            RetrievedChunk(
                id="chunk-low",
                text="Low priority context.",
                score=0.2,
                metadata={"source_name": "low.md", "chunk_index": 0},
            ),
            RetrievedChunk(
                id="chunk-high",
                text="High priority context.",
                score=0.8,
                metadata={"source_name": "high.md", "chunk_index": 1},
            ),
        ]

    def upsert_chunks(self, chunks: list[Any], vectors: list[list[float]]) -> None:
        del chunks, vectors


class ReverseReranker:
    def __init__(self) -> None:
        self.seen_query: str | None = None

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        self.seen_query = query
        return list(reversed(chunks))


class RecordingChatProvider:
    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        del system_prompt
        self.prompt = prompt
        return "recorded answer"


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
    assert not hasattr(result.citations[0], "source_path")
    assert not hasattr(result, "retrieved_chunks")


def test_rag_service_applies_reranker_before_prompt_and_citations() -> None:
    reranker = ReverseReranker()
    chat_provider = RecordingChatProvider()
    vector_store = TwoChunkVectorStore()
    service = RAGService(
        settings=Settings(llm_provider="mock", top_k=2, retrieval_mode="hybrid"),
        embedding_provider=DeterministicEmbeddingProvider(vector_size=32),
        vector_store=vector_store,
        chat_provider=chat_provider,
        reranker=reranker,
    )

    result = service.ask("Which context should lead?", top_k=2)

    assert vector_store.seen_query_text == "Which context should lead?"
    assert vector_store.seen_retrieval_mode == "hybrid"
    assert reranker.seen_query == "Which context should lead?"
    assert [citation.chunk_id for citation in result.citations] == ["chunk-high", "chunk-low"]
    assert chat_provider.prompt.index("High priority context.") < chat_provider.prompt.index(
        "Low priority context."
    )
