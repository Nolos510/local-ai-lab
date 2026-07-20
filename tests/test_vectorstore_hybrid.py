from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from local_ai_lab.vectorstores.base import (
    RetrievedChunk,
    VectorStoreConfigurationError,
    lexical_rank_chunks,
    reciprocal_rank_fuse,
    validate_retrieval_mode,
)
from local_ai_lab.vectorstores.qdrant import QdrantVectorStore


@dataclass(frozen=True)
class FakePoint:
    id: str
    score: float | None
    payload: dict[str, Any]


class FakeQueryResponse:
    def __init__(self, points: list[FakePoint]) -> None:
        self.points = points


class FakeQdrantClient:
    def __init__(self) -> None:
        self.scroll_calls = 0

    def collection_exists(self, *, collection_name: str) -> bool:
        assert collection_name == "chunks"
        return True

    def get_collection(self, *, collection_name: str):
        assert collection_name == "chunks"
        return SimpleNamespace(
            config=SimpleNamespace(
                params=SimpleNamespace(vectors=SimpleNamespace(size=2))
            )
        )

    def query_points(
        self,
        *,
        collection_name: str,
        query: list[float],
        limit: int,
        with_payload: bool,
    ) -> FakeQueryResponse:
        assert collection_name == "chunks"
        assert query == [0.1, 0.2]
        assert with_payload is True
        return FakeQueryResponse(
            [
                _point("dense-only", 0.99, "apple silicon vector retrieval"),
                _point("shared", 0.88, "privacy citations source names"),
            ][:limit]
        )

    def scroll(
        self,
        *,
        collection_name: str,
        limit: int,
        offset: Any | None,
        with_payload: bool,
        with_vectors: bool,
    ) -> tuple[list[FakePoint], Any | None]:
        del limit
        assert collection_name == "chunks"
        assert offset is None
        assert with_payload is True
        assert with_vectors is False
        self.scroll_calls += 1
        return (
            [
                _point("dense-only", None, "apple silicon vector retrieval"),
                _point("shared", None, "privacy citations source names"),
                _point("lexical-only", None, "privacy citations citations"),
            ],
            None,
        )


def test_lexical_rank_chunks_prefers_term_matches() -> None:
    chunks = [
        _chunk("a", "apple silicon vector retrieval"),
        _chunk("b", "privacy citations source names"),
        _chunk("c", "privacy citations citations"),
    ]

    ranked = lexical_rank_chunks("privacy citations", chunks, limit=2)

    assert [chunk.id for chunk in ranked] == ["c", "b"]
    assert ranked[0].metadata["lexical_score"] > ranked[1].metadata["lexical_score"]


def test_reciprocal_rank_fuse_combines_dense_and_lexical_rankings() -> None:
    dense = [_chunk("dense-only", "dense text"), _chunk("shared", "shared text")]
    lexical = [_chunk("lexical-only", "lexical text"), _chunk("shared", "shared text")]

    fused = reciprocal_rank_fuse([dense, lexical], limit=2)

    assert [chunk.id for chunk in fused] == ["shared", "dense-only"]
    assert fused[0].metadata["rrf_score"] > fused[1].metadata["rrf_score"]


def test_qdrant_dense_mode_does_not_scroll_for_lexical_candidates() -> None:
    store = _store_with_fake_client()

    results = store.search([0.1, 0.2], top_k=1)

    assert [chunk.id for chunk in results] == ["dense-only"]
    assert store.client.scroll_calls == 0


def test_qdrant_hybrid_mode_uses_rrf_with_local_lexical_candidates() -> None:
    store = _store_with_fake_client()

    results = store.search(
        [0.1, 0.2],
        top_k=3,
        query_text="privacy citations",
        retrieval_mode="hybrid",
    )

    assert [chunk.id for chunk in results] == ["shared", "dense-only", "lexical-only"]
    assert store.client.scroll_calls == 1


def test_validate_retrieval_mode_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unsupported retrieval mode"):
        validate_retrieval_mode("graph")


def test_qdrant_rejects_existing_collection_with_different_vector_size() -> None:
    store = _store_with_fake_client()
    store.vector_size = 1024

    with pytest.raises(VectorStoreConfigurationError) as exc_info:
        store.ensure_collection()

    message = str(exc_info.value)
    assert "existing collection uses 2 dimensions" in message
    assert "configured embedding provider uses 1024" in message
    assert "LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_chunks_reindexed_1024" in message
    assert "uv run local-ai-lab doctor" in message


def _store_with_fake_client() -> QdrantVectorStore:
    store = QdrantVectorStore(url="http://localhost:6333", collection_name="chunks", vector_size=2)
    store.client = FakeQdrantClient()
    return store


def _chunk(chunk_id: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        text=text,
        score=1.0,
        metadata={"source_name": "sample.md", "chunk_index": 0},
    )


def _point(chunk_id: str, score: float | None, text: str) -> FakePoint:
    return FakePoint(
        id=chunk_id,
        score=score,
        payload={"text": text, "source_name": "sample.md", "chunk_index": 0},
    )
