# Goal — RAG Quality (R1–R5)

- **Branch:** `codex/rag-quality`
- **Area:** `src/local_ai_lab/`, new `evals/rag-retrieval/`
- **Reserved ADRs:** 0007–0008
- Full plan: [../sprints/2026-06-18-rag-quality-sprint.md](../sprints/2026-06-18-rag-quality-sprint.md)

```text
GOAL: Execute the RAG Quality sprint (retrieval) for the local-ai-lab repo.

BRANCH: work on codex/rag-quality. AREA: src/local_ai_lab/ and a new
evals/rag-retrieval/. Do NOT touch apps/model-dashboard (another agent owns it).
Reserve ADR numbers 0007 and 0008. In pyproject.toml edit ONLY
[project.optional-dependencies].

START HERE:
1. Read AGENTS.md in full (local-first rules, §5 dependency gate, DoD are binding).
2. Read docs/sprints/2026-06-18-rag-quality-sprint.md and
   docs/sprints/2026-06-18-codex-handoff-rag-quality.md — the full plan. Execute
   loops R1 -> R5 IN ORDER.

LOCKED DECISIONS (do not deviate):
- Reranker = abstraction + a light identity default; the real local cross-encoder
  goes behind an OPTIONAL pyproject [rerank] extra, NOT default-installed (no torch
  in the default code path). Document it in ADR 0007.
- Embedding default STAYS `deterministic` (offline/CI-safe). Add BGE-M3 via Ollama
  as a first-class documented option + doctor guidance. DO NOT flip the default.
- Citations stay source_name + chunk_index in the default /ask response. Raw chunk
  text/scores ONLY behind an explicit opt-in local-debug flag (preserve ADR 0003).

LOOP PROTOCOL (per loop R1..R5):
1. Inspect `git status -sb`. Implement only the files the sprint doc lists; add the
   listed tests (offline, with deterministic/fake providers — no model, no live
   Qdrant).
2. Run the FULL gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
3. Commit self-contained (scope: rag/embeddings/retrieval/docs), then STOP and
   report (files, tests, gate lines, next loop).

Never claim a command passed unless it was actually run. Begin with R1.
```
