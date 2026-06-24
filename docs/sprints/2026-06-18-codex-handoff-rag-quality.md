# Codex Handoff — RAG Quality Sprint (v2) — 2026-06-18

Paste the fenced block into Codex. Self-contained.

---

```text
You are the main builder for the RAG Quality (v2) sprint in the AI Lab OS repo
(local-ai-lab), a local-first Apple Silicon AI lab. This sprint improves the
Local RAG Backbone lane (retrieval), which is currently shallow: deterministic
embeddings by default, dense-only Qdrant, no reranker, no hybrid, no retrieval
eval set.

START HERE:
1. Read AGENTS.md in full — local-first rules, the §5 dependency-review gate, and
   Definition of Done are binding.
2. Read docs/sprints/2026-06-18-rag-quality-sprint.md — the plan, with locked
   scope decisions, exact files, and acceptance criteria. Execute loops R1 → R5
   IN ORDER.

LOCKED SCOPE DECISIONS (do not deviate):
- Reranker = ABSTRACTION + OPTIONAL EXTRA. Ship a Reranker protocol + a light
  identity/no-op default. The real local cross-encoder backend goes behind an
  OPTIONAL pyproject [rerank] extra, NOT installed by default (torch is heavy;
  document it in an ADR per AGENTS.md §5). No torch in the default code path.
- Embedding default STAYS `deterministic` (offline/CI-safe). Add BGE-M3 via
  Ollama as a first-class documented option + doctor guidance. DO NOT flip the
  global default.
- Citations stay source_name + chunk_index in the default response. Raw chunk
  text/scores ONLY behind an explicit opt-in local-debug flag — never in the
  default /ask response (preserve the ADR 0003 privacy narrowing).

HARD CONSTRAINTS:
- Qdrant stays the vector DB. No new DEFAULT runtime deps — reranker backend is an
  optional extra; hybrid uses a light local lexical signal (no heavy model);
  embeddings via Ollama. Any dep clears the §5 gate + ADR.
- No cloud APIs, secrets, telemetry, or model-download code.
- Keep deterministic/mock providers for tests; the unit gate runs offline with no
  model and no live Qdrant. Live RAG checks are manual smoke only — never claim a
  command passed unless actually run.
- Narrow, package-scoped changes; preserve passing tests. No architecture change
  without an ADR.

LOOP PROTOCOL (per loop):
1. Re-read AGENTS.md + the sprint doc. Inspect `git status -sb`.
2. Implement only the listed files; add/extend the listed tests.
3. Run the FULL validation gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
4. Update docs/lab-notes/ADR only where the loop specifies.
5. Commit a self-contained change (format below), then STOP and report: files
   changed, tests added, gate pass/fail lines, deviations, next recommended loop.
   Commit format:
     <scope>: <summary>

     <what changed, why, how validated, what was NOT tested>

     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
   Scopes: rag, embeddings, retrieval, docs.

THE LOOPS (full detail in the sprint doc):
R1 rag/embeddings: MEASURE FIRST. Add evals/rag-retrieval/ (SPEC + tiny labeled
   fixture set + stdlib scorer computing recall@k and MRR, runnable OFFLINE with
   deterministic/fake providers). Make BGE-M3 a first-class Ollama embedding
   option (OllamaEmbeddingProvider model="bge-m3"); add a doctor embedding-model
   check that recommends `ollama pull bge-m3`. Keep deterministic the default.
   Tests: tests/test_rag_retrieval_eval.py + extend tests/test_embeddings.py.
R2 retrieval: RERANKER ABSTRACTION. New src/local_ai_lab/rerankers/ (base.py
   Reranker protocol, identity.py default, factory.py); wire into rag/service.py
   after retrieval; settings reranker_provider (default identity). Add an OPTIONAL
   pyproject [rerank] extra for a real local cross-encoder (NOT default-installed)
   + an ADR documenting the dependency decision. Tests: tests/test_rerankers.py +
   reranker wiring in tests/test_rag_service.py. Measure via R1.
R3 retrieval: HYBRID. Add a light local lexical/BM25 sparse signal + RRF fusion
   with dense in vectorstores/qdrant.py (+base.py); hybrid path behind
   settings.retrieval_mode (dense default | hybrid) in rag/service.py + factory.
   No heavy deps. Tests extend test_vectorstore_* + test_rag_service. Measure via
   R1.
R4 rag: CITATIONS + OPT-IN INSPECTION. Render citations as source_name +
   chunk_index in the default response (keep ADR 0003 narrowing). Add an opt-in
   local-debug inspection (explicit flag/env) that surfaces retrieved chunk text +
   scores — never in the default response. Tests must prove the negative: default
   response has NO raw chunk text/paths; inspection flag surfaces them only when
   set. Files: rag/service.py, api/schemas.py, api/app.py, cli/app.py.
R5 docs: Tick docs/rag.md TODOs, add a docs/lab-notes/ entry, update ROADMAP v2.
   Truthful only — distinguish "implemented + measured on the eval set" from
   "behind an optional extra / not yet run on real corpora."

If a validation command cannot run in your environment, document the exact reason
— never claim a command passed unless it was run. Begin with R1.
```

---

## Notes for the human

- A Claude Code `/loop` integrator runs on each commit: full gate + the R1
  retrieval scorer where relevant, checks Definition-of-Done, and flags new
  DEFAULT deps (esp. torch sneaking into the default path), any raw chunk/path in
  the default `/ask` response, a flipped embedding default, cloud calls, or
  overclaiming in docs.
- **R2 is the dependency-sensitive one** — verify the `[rerank]` extra stays
  optional and the default code path imports no heavy lib.
- The optional real-corpus eval run (BGE-M3 numbers) is yours to trigger when
  ready; it's what proves the retrieval lane.
```
