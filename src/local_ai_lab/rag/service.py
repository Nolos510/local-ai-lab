from dataclasses import dataclass
from pathlib import Path
from typing import Any

from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.base import EmbeddingProvider
from local_ai_lab.ingestion.chunking import chunk_documents
from local_ai_lab.ingestion.documents import load_documents
from local_ai_lab.llms.base import ChatProvider
from local_ai_lab.prompts.templates import SYSTEM_PROMPT, build_rag_prompt
from local_ai_lab.rerankers.base import Reranker
from local_ai_lab.rerankers.identity import IdentityReranker
from local_ai_lab.vectorstores.base import RetrievedChunk


@dataclass(frozen=True)
class Citation:
    source_name: str
    chunk_index: int | str


@dataclass(frozen=True)
class RetrievalInspection:
    chunk_id: str
    source_name: str
    chunk_index: int | str
    score: float
    text: str


@dataclass(frozen=True)
class AskResult:
    answer: str
    citations: list[Citation]
    retrieval_inspection: list[RetrievalInspection] | None = None


class RAGService:
    def __init__(
        self,
        *,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
        vector_store: Any,
        chat_provider: ChatProvider,
        reranker: Reranker | None = None,
    ) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.chat_provider = chat_provider
        self.reranker = reranker or IdentityReranker()

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

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> AskResult:
        query_vector = self.embedding_provider.embed(question)
        retrieved = self.vector_store.search(
            query_vector,
            top_k=top_k or self.settings.top_k,
            query_text=question,
            retrieval_mode=self.settings.retrieval_mode,
        )
        reranked = self.reranker.rerank(question, retrieved)
        prompt = build_rag_prompt(question, reranked)
        answer = self.chat_provider.generate(prompt, system_prompt=SYSTEM_PROMPT)
        return AskResult(
            answer=answer,
            citations=[_to_citation(chunk) for chunk in reranked],
            retrieval_inspection=[_to_inspection(chunk) for chunk in reranked]
            if inspect_retrieval
            else None,
        )


def _to_citation(chunk: RetrievedChunk) -> Citation:
    return Citation(
        source_name=str(chunk.metadata.get("source_name", "")),
        chunk_index=chunk.metadata.get("chunk_index", "?"),
    )


def _to_inspection(chunk: RetrievedChunk) -> RetrievalInspection:
    return RetrievalInspection(
        chunk_id=chunk.id,
        source_name=str(chunk.metadata.get("source_name", "")),
        chunk_index=chunk.metadata.get("chunk_index", "?"),
        score=chunk.score,
        text=chunk.text,
    )
