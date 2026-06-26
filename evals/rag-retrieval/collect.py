#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.factory import build_embedding_provider
from local_ai_lab.rag.factory import build_rag_service
from local_ai_lab.rerankers.factory import build_reranker
from local_ai_lab.vectorstores.factory import build_vector_store


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect source-aware RAG retrieval results without calling an LLM."
    )
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--corpus-path", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--retrieval-mode", choices=("dense", "hybrid"))
    args = parser.parse_args()

    settings = Settings(
        top_k=args.top_k,
        retrieval_mode=args.retrieval_mode or Settings().retrieval_mode,
    )
    if args.corpus_path:
        service = build_rag_service(settings)
        service.ingest_path(args.corpus_path)

    labels = _load_queries(args.labels)
    embedding_provider = build_embedding_provider(settings)
    vector_store = build_vector_store(settings)
    reranker = build_reranker(settings)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for label in labels:
            query = label["query"]
            vector = embedding_provider.embed(query)
            retrieved = vector_store.search(
                vector,
                top_k=args.top_k,
                query_text=query,
                retrieval_mode=settings.retrieval_mode,
            )
            reranked = reranker.rerank(query, retrieved)
            record = {
                "query_id": label["query_id"],
                "query": query,
                "retrieval_mode": settings.retrieval_mode,
                "retrieved": [
                    {
                        "source_name": str(chunk.metadata.get("source_name", "")),
                        "chunk_index": chunk.metadata.get("chunk_index", "?"),
                        "chunk_id": chunk.id,
                        "score": chunk.score,
                    }
                    for chunk in reranked
                ],
            }
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")
    return 0


def _load_queries(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries")
    if not isinstance(queries, list):
        raise ValueError("labels file must include a queries list")
    return [
        {"query_id": str(item["query_id"]), "query": str(item["query"])}
        for item in queries
        if isinstance(item, dict)
    ]


if __name__ == "__main__":
    raise SystemExit(main())
