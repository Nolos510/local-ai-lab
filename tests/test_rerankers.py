import pytest

from local_ai_lab.config.settings import Settings
from local_ai_lab.rerankers.factory import build_reranker
from local_ai_lab.rerankers.identity import IdentityReranker
from local_ai_lab.vectorstores.base import RetrievedChunk


class FakeCrossEncoderReranker:
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        del query
        return sorted(chunks, key=lambda chunk: chunk.metadata["rank"])


def test_identity_reranker_preserves_retrieval_order_without_mutating_input() -> None:
    chunks = [
        _chunk("chunk-b", rank=2),
        _chunk("chunk-a", rank=1),
    ]

    reranked = IdentityReranker().rerank("local query", chunks)

    assert [chunk.id for chunk in reranked] == ["chunk-b", "chunk-a"]
    assert reranked is not chunks


def test_fake_cross_encoder_can_implement_reranker_protocol_offline() -> None:
    chunks = [
        _chunk("chunk-b", rank=2),
        _chunk("chunk-a", rank=1),
    ]

    reranked = FakeCrossEncoderReranker().rerank("local query", chunks)

    assert [chunk.id for chunk in reranked] == ["chunk-a", "chunk-b"]


def test_build_reranker_returns_identity_default() -> None:
    reranker = build_reranker(Settings())

    assert isinstance(reranker, IdentityReranker)


def test_build_reranker_rejects_unreviewed_provider() -> None:
    settings = Settings(reranker_provider="cross_encoder")

    with pytest.raises(ValueError, match="optional \\[rerank\\] extra"):
        build_reranker(settings)


def _chunk(chunk_id: str, *, rank: int) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        text=f"Text for {chunk_id}",
        score=float(rank),
        metadata={"source_name": "sample.md", "chunk_index": rank, "rank": rank},
    )
