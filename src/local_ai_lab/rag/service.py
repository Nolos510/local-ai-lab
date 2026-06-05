from dataclasses import dataclass
from pathlib import Path
from typing import Any

from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.base import EmbeddingProvider
from local_ai_lab.ingestion.chunking import chunk_documents
from local_ai_lab.ingestion.documents import load_documents
from local_ai_lab.llms.base import ChatProvider
from local_ai_lab.prompts.templates import SYSTEM_PROMPT, build_rag_prompt
from local_ai_lab.vectorstores.base import RetrievedChunk


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    source_path: str
    source_name: str
    chunk_index: int | str
    score: float
    preview: str


@dataclass(frozen=True)
class AskResult:
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[dict[str, Any]]


class RAGService:
    def __init__(
        self,
        *,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
        vector_store: Any,
        chat_provider: ChatProvider,
    ) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.chat_provider = chat_provider

    def ingest_path(self, path: Path) -> dict[str, int]:
        documents = load_documents(path)
        chunks = chunk_documents(
            documents,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        vectors = self.embedding_provider.embed_many([chunk.text for chunk in chunks])
        self.vector_store.upsert_chunks(chunks, vectors)
        return {"documents": len(documents), "chunks": len(chunks)}

    def ask(self, question: str, *, top_k: int | None = None) -> AskResult:
        query_vector = self.embedding_provider.embed(question)
        retrieved = self.vector_store.search(query_vector, top_k=top_k or self.settings.top_k)
        prompt = build_rag_prompt(question, retrieved)
        answer = self.chat_provider.generate(prompt, system_prompt=SYSTEM_PROMPT)
        return AskResult(
            answer=answer,
            citations=[_to_citation(chunk) for chunk in retrieved],
            retrieved_chunks=[_to_retrieved_payload(chunk) for chunk in retrieved],
        )


def _to_citation(chunk: RetrievedChunk) -> Citation:
    return Citation(
        chunk_id=chunk.id,
        source_path=str(chunk.metadata.get("source_path", "")),
        source_name=str(chunk.metadata.get("source_name", "")),
        chunk_index=chunk.metadata.get("chunk_index", "?"),
        score=chunk.score,
        preview=" ".join(chunk.text.split())[:240],
    )


def _to_retrieved_payload(chunk: RetrievedChunk) -> dict[str, Any]:
    return {
        "id": chunk.id,
        "score": chunk.score,
        "text": chunk.text,
        "metadata": chunk.metadata,
    }
