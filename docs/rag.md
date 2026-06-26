# RAG Pipeline

The v0 RAG pipeline is intentionally simple:

```text
markdown/text source
  -> load documents
  -> chunk with metadata
  -> embed chunks
  -> index in Qdrant
  -> retrieve top-k chunks with dense or opt-in hybrid retrieval
  -> optionally rerank retrieved chunks
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
- Offline retrieval-eval scorer with a tiny labeled fixture set.
- Reranker protocol with an identity default and optional `[rerank]`
  cross-encoder backend that requires an explicit local model path.
- Opt-in hybrid retrieval that combines dense Qdrant candidates with a local
  BM25-style lexical signal and reciprocal-rank fusion.
- Privacy-narrow default citations plus explicit local retrieval inspection for
  debugging.
- Source-aware repo-docs retrieval scoring with BGE-M3 evidence.
- Offline RAG answer/citation evaluation scaffold.

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

The FastAPI `/ask` endpoint returns the answer plus privacy-narrow citations by
default:

```json
{
  "answer": "The lab is for local-first AI workflows.",
  "citations": [
    {
      "source_name": "sample.md",
      "chunk_index": 0
    }
  ]
}
```

The default response does not include raw retrieved chunks, chunk previews,
chunk IDs, retrieval scores, or private source paths. `top_k` is capped at 20.
See `docs/adr/0003-privacy-narrow-ask-response.md` for the privacy decision
record.

For local debugging only, explicitly opt into retrieval inspection:

```bash
uv run local-ai-lab ask "What is this lab for?" --json --inspect-retrieval
```

The inspection payload includes retrieved chunk text, scores, and chunk IDs.
Treat that output as local private data and do not use it in default logs,
reports, or shared artifacts.

## Retrieval Modes

Dense retrieval remains the default:

```bash
LOCAL_AI_LAB_RETRIEVAL_MODE=dense
```

Hybrid retrieval is available as an explicit local option:

```bash
LOCAL_AI_LAB_RETRIEVAL_MODE=hybrid
```

Hybrid mode still uses Qdrant as the vector database. It fuses dense vector
results with a local stdlib BM25-style lexical ranking over chunk text using
reciprocal-rank fusion. No extra dependency, cloud API, model download, or
external service is added.

## Reranking

Reranking runs after retrieval and before prompt assembly. The default reranker
is `identity`, which preserves retrieval order:

```bash
LOCAL_AI_LAB_RERANKER_PROVIDER=identity
```

`pyproject.toml` exposes an optional `[rerank]` extra for a reviewed local
cross-encoder backend:

```bash
LOCAL_AI_LAB_RERANKER_PROVIDER=cross_encoder
LOCAL_AI_LAB_RERANKER_MODEL_PATH=/path/to/local/reranker
```

The model path must already exist locally. The backend lazy-imports the optional
dependency only when selected and requests local files only. It does not
download or resolve model IDs.

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

## Retrieval Evaluation

RAG Quality changes are measured against the offline retrieval eval before
changing ranking behavior. The initial fixture uses labeled query-to-chunk IDs
and computes `recall@k` plus `MRR` without Qdrant, Ollama, network access, or a
model runtime:

```bash
python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/fixtures/labels.json \
  --results evals/rag-retrieval/fixtures/deterministic-results.jsonl \
  --k 2
```

The fixture is deliberately small. Treat it as an offline regression harness,
not proof of real-corpus retrieval quality.

A committed repo-docs corpus also exists for source-aware real retrieval:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3:latest \
LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_1_bge_m3 \
uv run python evals/rag-retrieval/collect.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.1/labels.json \
  --corpus-path evals/rag-retrieval/corpora/repo-docs-v0.1/docs \
  --out evals/rag-retrieval/corpora/repo-docs-v0.1/bge-m3-results.jsonl \
  --top-k 5

python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.1/labels.json \
  --results evals/rag-retrieval/corpora/repo-docs-v0.1/bge-m3-results.jsonl \
  --k 5
```

Recorded result for the initial repo-docs BGE-M3 run:

```text
query_count=4
recall@5=1.0
MRR=1.0
```

## Answer/Citation Evaluation

RAG answer evaluation lives under `evals/rag-answer/`. It scores saved answer
rows offline for citation hit rate, required-term coverage, and forbidden-term
violations. It does not call an LLM or retrieval service.

## TODO

- [x] Add BGE-M3-capable Ollama embedding provider.
- [x] Add retrieval evaluation datasets.
- [x] Add hybrid dense/local lexical retrieval.
- [x] Add reranker abstraction.
- [x] Add citation rendering helpers.
- [ ] Add dedicated reindex command.
- [x] Add reviewed real local cross-encoder reranker backend.
- [ ] Add parser version tracking.
