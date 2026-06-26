# RAG Quality Retrieval Sprint

## Summary

The RAG Quality retrieval sprint added measurable, configurable retrieval
improvements while preserving the local-first defaults.

Implemented:

- Offline retrieval eval fixtures and a stdlib scorer for `recall@k` and `MRR`
  under `evals/rag-retrieval/`.
- BGE-M3 as the documented Ollama embedding option, with deterministic
  embeddings still the default.
- Reranker protocol, identity default, and optional `[rerank]` extra for a
  future reviewed local cross-encoder backend.
- Opt-in hybrid retrieval that fuses dense Qdrant candidates with a local
  BM25-style lexical signal.
- Default `/ask` citations narrowed to `source_name` plus `chunk_index`.
- Explicit local-debug retrieval inspection for chunk text, scores, and chunk
  IDs.
- Source-aware repo-docs retrieval corpus with a BGE-M3 local retrieval run.
- RAG answer/citation eval scaffold and offline scorer.
- Optional local cross-encoder reranker backend gated behind `[rerank]` plus an
  explicit local model path.

## Validation

The sprint loops used the standard gate:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

The retrieval scorer fixture command also remained runnable:

```bash
python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/fixtures/labels.json \
  --results evals/rag-retrieval/fixtures/deterministic-results.jsonl \
  --k 2
```

Fixture result: `recall@2 = 0.5`, `MRR = 0.5`.

The repo-docs BGE-M3 retrieval evidence was also recorded:

```bash
python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.1/labels.json \
  --results evals/rag-retrieval/corpora/repo-docs-v0.1/bge-m3-results.jsonl \
  --k 5
```

Result: `query_count = 4`, `recall@5 = 1.0`, `MRR = 1.0`.

Environment note: `docker compose up -d qdrant` reported that the fixed
`local-ai-lab-qdrant` container name was already in use. The existing loopback
Qdrant service was healthy and served the retrieval smoke.

## Safety Posture

- No cloud APIs, telemetry, secrets, model downloads, or model execution were
  added.
- Qdrant remains the v0 vector database.
- Default embedding provider remains `deterministic`.
- Default retrieval mode remains `dense`.
- Default reranker remains `identity`.
- The optional `[rerank]` extra is not default-installed and cross-encoder
  reranking requires an explicit local model path.
- Raw chunk text, scores, and chunk IDs are visible only through explicit local
  inspection.

## Not Yet Done

- Reindex remains a documented manual sequence rather than a dedicated command.
