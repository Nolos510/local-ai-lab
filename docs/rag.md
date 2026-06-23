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

## No-Model Smoke Check

The deterministic embedding provider plus mock chat provider can verify the RAG
path without a live Ollama or LM Studio model. Qdrant is still required because
the smoke path exercises indexing, retrieval, prompt assembly, and citations.

Use a dedicated smoke collection so the sample docs do not overwrite or collide
with a personal collection that may have been created with a different vector
size:

```bash
docker compose up -d qdrant
curl -fsS -X DELETE http://localhost:6333/collections/local_ai_lab_quickstart_smoke || true
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab doctor
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

If `docker compose up -d qdrant` reports that `local-ai-lab-qdrant` already
exists, another checkout or previous run owns the fixed container name. Continue
only when the existing loopback service is reachable:

```bash
curl -fsS http://localhost:6333/collections
```

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

## Ask API Response

The FastAPI `/ask` endpoint returns the answer plus privacy-narrow citations:

```json
{
  "answer": "The lab is for local-first AI workflows.",
  "citations": [
    {
      "chunk_id": "sample-doc-0001",
      "source_name": "sample.md",
      "chunk_index": 0
    }
  ]
}
```

The default response does not include raw retrieved chunks, chunk previews, or
private source paths. `top_k` is capped at 20. See
`docs/adr/0003-privacy-narrow-ask-response.md` for the privacy decision record.

## Reindexing

Qdrant collection vector size is fixed when the collection is created. Switching
from deterministic embeddings to BGE-M3, or switching any embedding model/vector
dimension, requires recreating the collection and reingesting documents.

The common failure looks like this:

```text
Vector dimension error: expected dim: 384, got 1024
```

That means the current settings are writing vectors with a different dimension
than the existing collection. Use a new collection name for smoke work, or delete
only the collection you intentionally want to rebuild.

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
