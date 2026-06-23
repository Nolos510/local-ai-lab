# ADR 0008: Hybrid dense and local lexical retrieval

## Status

Accepted

## Context

The v0 RAG retrieval path is dense-only Qdrant vector search. RAG Quality R1
added an offline retrieval scorer, and R2 added a reranking stage after
retrieval. Dense retrieval remains useful, but short exact terms, identifiers,
and local project vocabulary can be missed by vector similarity alone.

The sprint requires a hybrid retrieval mode behind a setting while preserving
the default dense path. The local-first constraints rule out hidden cloud APIs,
model downloads, telemetry, or heavy default dependencies.

## Decision

- Keep `LOCAL_AI_LAB_RETRIEVAL_MODE=dense` as the default.
- Add `LOCAL_AI_LAB_RETRIEVAL_MODE=hybrid` as an explicit opt-in.
- For hybrid mode, combine:
  - dense Qdrant vector results;
  - a small local BM25-style lexical ranking over chunk text; and
  - reciprocal-rank fusion to produce the final candidate order.
- Implement the lexical signal with Python stdlib only. Do not add BM25
  packages, sparse-vector services, model downloads, API clients, or cloud
  calls.
- Keep Qdrant as the v0 vector database. Hybrid mode still uses Qdrant as the
  chunk store and dense retrieval source.
- Keep reranking separate: hybrid retrieval selects/fuses candidate chunks,
  then the configured reranker runs afterward.

## Consequences

- Default retrieval behavior remains unchanged unless the operator opts into
  hybrid mode.
- Hybrid mode can improve exact-term and identifier recall for local corpora
  without new runtime dependencies.
- The lexical pass scrolls local chunk payloads from Qdrant when hybrid mode is
  selected. This is acceptable for the v0 local lab but should be revisited if
  corpus size grows substantially.
- Raw chunk text remains internal retrieval state. Default `/ask` responses must
  still preserve the ADR 0003 privacy narrowing until R4 adds explicit local
  inspection controls.

## Validation

R3 must pass the standard offline gate:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

R3 should also run the R1 retrieval scorer so the offline measurement path stays
working. Live Qdrant/BGE-M3 hybrid retrieval is a separate manual smoke step and
must not be claimed unless explicitly run.
