# RAG Pipeline

The v0 RAG pipeline is intentionally simple:

```text
markdown/text source
  -> load documents
  -> chunk with metadata
  -> embed chunks
  -> index in Qdrant
  -> retrieve top-k chunks
  -> assemble prompt with citations
  -> generate answer with local model
```

## Current Capabilities

- Markdown and plain text ingestion.
- Stable chunk IDs.
- Source path, source name, source hash, and chunk index metadata.
- Deterministic embedding provider for repeatable development.
- Ollama semantic embedding provider for local real retrieval.
- Qdrant vector search.

## Embedding Providers

The default provider remains deterministic so tests and smoke runs can execute
without a live model runtime:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=deterministic
```

To use semantic local embeddings through Ollama:

```bash
ollama pull bge-m3
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3 \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
uv run local-ai-lab doctor
```

Then ingest and ask:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3 \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
uv run local-ai-lab ingest --path data/sample_docs

LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3 \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
uv run local-ai-lab ask "What is this lab for?"
```

## Reindexing

Qdrant collection vector size is fixed when the collection is created. Switching
from deterministic embeddings to BGE-M3, or switching any embedding model/vector
dimension, requires recreating the collection and reingesting documents.

Until a dedicated `local-ai-lab reindex` command exists, use this local manual
sequence:

```bash
docker compose up -d qdrant
curl -X DELETE http://localhost:6333/collections/local_ai_lab_chunks
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3 \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
uv run local-ai-lab ingest --path data/sample_docs
```

Use a different collection name instead of deleting if you need to preserve the
old deterministic index for comparison.

## TODO

- [x] Add BGE-M3-capable Ollama embedding provider.
- [ ] Add dedicated reindex command.
- [ ] Add hybrid dense/sparse retrieval.
- [ ] Add reranker abstraction.
- [ ] Add retrieval evaluation datasets.
- [ ] Add citation rendering helpers.
- [ ] Add parser version tracking.
