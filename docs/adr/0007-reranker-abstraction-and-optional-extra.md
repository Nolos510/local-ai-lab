# ADR 0007: Reranker abstraction and optional local cross-encoder extra

## Status

Accepted

## Context

The v0 RAG path retrieves dense Qdrant results and sends them directly into
prompt assembly. RAG Quality R1 added a small offline retrieval eval so ranking
changes can be measured with `recall@k` and `MRR`. The next retrieval-quality
step is a reranking stage after vector search.

Local cross-encoder rerankers are useful for semantic ordering, but common
Python implementations rely on `sentence-transformers` and transitive model
runtime dependencies such as PyTorch. Those packages are heavy, may trigger
model-loading workflows, and are inappropriate for the default offline/CI-safe
path.

AGENTS.md section 5 requires a dependency gate before adding dependencies:

- Stdlib can define the protocol, identity implementation, factory, and offline
  tests. It cannot provide transformer cross-encoder scoring.
- The dependency would be runtime code only for users who explicitly opt into
  local reranking.
- The dependency has heavy transitive risk, especially `torch`; it must not be
  imported or installed by default.
- The dashboard, benchmark harness, and R1 retrieval scorer do not need this
  dependency.

## Decision

- Add a small `Reranker` protocol with `rerank(query, chunks)`.
- Add `IdentityReranker` as the default implementation. It preserves vector
  store ordering and has no dependencies.
- Add `LOCAL_AI_LAB_RERANKER_PROVIDER`, defaulting to `identity`.
- Wire the RAG service to apply the reranker after retrieval and before prompt
  assembly/citation rendering.
- Add a `[project.optional-dependencies]` extra named `rerank` for the future
  local cross-encoder backend. The extra is not default-installed.
- Keep the default code path free of `sentence-transformers`, `torch`, model
  downloads, cloud calls, API keys, and live model execution.

The intended future import location for a reviewed cross-encoder backend is
`local_ai_lab.rerankers.cross_encoder`. That backend must lazy-import optional
dependencies only when selected and must be tested with fakes before any live
local model check.

## Consequences

- RAG service behavior is now extensible without changing prompt assembly or
  vector-store APIs.
- Offline tests can prove reranker wiring with fake rerankers and the identity
  default.
- Users do not pay the dependency cost for reranking unless they explicitly
  install the optional extra.
- The optional extra carries known transitive risk and should remain removable:
  deleting the extra and any future `cross_encoder` backend must leave
  `identity` behavior and tests intact.

## Validation

R2 must pass the standard offline gate:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Live reranking with a real cross-encoder is not part of R2 and must not be
claimed without an explicit local run.
