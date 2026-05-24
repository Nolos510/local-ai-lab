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
from local_ai_lab.vectorstores.base import RetrievedChunk


class QdrantVectorStore:
    def __init__(self, *, url: str, collection_name: str, vector_size: int) -> None:
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        if self.client.collection_exists(collection_name=self.collection_name):
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

    def search(self, vector: list[float], *, top_k: int) -> list[RetrievedChunk]:
        self.ensure_collection()
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        results = []
        for point in response.points:
            payload = point.payload or {}
            text = str(payload.get("text", ""))
            metadata = {key: value for key, value in payload.items() if key != "text"}
            results.append(
                RetrievedChunk(
                    id=str(point.id),
                    text=text,
                    score=float(point.score),
                    metadata=metadata,
                )
            )
        return results

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
