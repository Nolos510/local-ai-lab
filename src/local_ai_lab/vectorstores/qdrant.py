from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from local_ai_lab.ingestion.chunking import DocumentChunk
from local_ai_lab.vectorstores.base import (
    RetrievedChunk,
    VectorStoreConfigurationError,
    lexical_rank_chunks,
    reciprocal_rank_fuse,
    validate_retrieval_mode,
)

HYBRID_CANDIDATE_MULTIPLIER = 4
SCROLL_PAGE_SIZE = 256


class QdrantVectorStore:
    def __init__(self, *, url: str, collection_name: str, vector_size: int) -> None:
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        if self.client.collection_exists(collection_name=self.collection_name):
            info = self.client.get_collection(collection_name=self.collection_name)
            existing_size = _collection_vector_size(info)
            if existing_size is not None and existing_size != self.vector_size:
                raise VectorStoreConfigurationError(
                    "Qdrant collection dimension mismatch: the existing collection uses "
                    f"{existing_size} dimensions but the configured embedding provider uses "
                    f"{self.vector_size}. Set "
                    "LOCAL_AI_LAB_QDRANT_COLLECTION="
                    f"local_ai_lab_chunks_reindexed_{self.vector_size} "
                    "to create a separate index, then run `uv run local-ai-lab doctor`."
                )
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )

    def upsert_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            msg = "chunks and vectors must have the same length"
            raise ValueError(msg)

        self.ensure_collection()
        self._delete_existing_sources(chunks)
        points = [
            PointStruct(
                id=chunk.id,
                vector=vector,
                payload={
                    "text": chunk.text,
                    **_json_safe_payload(chunk.metadata),
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )

    def search(
        self,
        vector: list[float],
        *,
        top_k: int,
        query_text: str | None = None,
        retrieval_mode: str = "dense",
    ) -> list[RetrievedChunk]:
        mode = validate_retrieval_mode(retrieval_mode)
        if mode == "dense":
            return self._search_dense(vector, top_k=top_k)
        if not query_text:
            return self._search_dense(vector, top_k=top_k)

        candidate_limit = max(top_k, top_k * HYBRID_CANDIDATE_MULTIPLIER)
        dense_results = self._search_dense(vector, top_k=candidate_limit)
        lexical_results = lexical_rank_chunks(
            query_text,
            self._scroll_all_chunks(),
            limit=candidate_limit,
        )
        return reciprocal_rank_fuse([dense_results, lexical_results], limit=top_k)

    def _search_dense(self, vector: list[float], *, top_k: int) -> list[RetrievedChunk]:
        self.ensure_collection()
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        results = []
        for point in response.points:
            results.append(_point_to_retrieved_chunk(point))
        return results

    def _scroll_all_chunks(self) -> list[RetrievedChunk]:
        self.ensure_collection()
        chunks: list[RetrievedChunk] = []
        offset: Any | None = None
        while True:
            records, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=SCROLL_PAGE_SIZE,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            chunks.extend(
                _point_to_retrieved_chunk(record, default_score=0.0) for record in records
            )
            if offset is None:
                return chunks

    def _delete_existing_sources(self, chunks: list[DocumentChunk]) -> None:
        source_hashes = {
            str(chunk.metadata["source_hash"])
            for chunk in chunks
            if chunk.metadata.get("source_hash") is not None
        }
        for source_hash in source_hashes:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source_hash",
                            match=MatchValue(value=source_hash),
                        )
                    ]
                ),
                wait=True,
            )


def _json_safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: str(value)
        if not isinstance(value, (str, int, float, bool, list, dict, type(None)))
        else value
        for key, value in payload.items()
    }


def _collection_vector_size(info: Any) -> int | None:
    try:
        vectors = info.config.params.vectors
    except AttributeError:
        return None
    if isinstance(vectors, dict):
        sizes = {
            int(value.size)
            for value in vectors.values()
            if getattr(value, "size", None) is not None
        }
        return sizes.pop() if len(sizes) == 1 else None
    size = getattr(vectors, "size", None)
    return int(size) if size is not None else None


def _point_to_retrieved_chunk(point: Any, *, default_score: float | None = None) -> RetrievedChunk:
    payload = point.payload or {}
    text = str(payload.get("text", ""))
    metadata = {key: value for key, value in payload.items() if key != "text"}
    raw_score = getattr(point, "score", default_score)
    score = float(raw_score) if raw_score is not None else 0.0
    return RetrievedChunk(
        id=str(point.id),
        text=text,
        score=score,
        metadata=metadata,
    )
