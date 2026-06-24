# AI Lab OS — RAG Quality Sprint (v2) — 2026-06-18

Brings the **Local RAG Backbone** lane up to the maturity of the dashboard/eval
lane. Today retrieval is shallow: deterministic (hash-based) embeddings by
default, dense-only Qdrant, no reranker, no hybrid retrieval, no retrieval-eval
set. This sprint makes retrieval **measurable** and then **better**, while
respecting the project's lean/local-first posture.

## Scope decisions (locked with the user)

- **Reranker = abstraction + optional extra.** Ship a `Reranker` protocol + a
  light default (identity/no-op). The real local cross-encoder backend lives
  behind an optional `[rerank]` extra that is **NOT installed by default** (torch
  is heavy — it must clear the AGENTS.md dependency gate via ADR). Tested with
  fakes.
- **Embedding default stays `deterministic`** (offline/CI-safe). Add **BGE-M3 via
  Ollama** as a first-class, documented option with doctor guidance. **Do not
  flip the global default** — that stays a one-line config choice the user makes
  later (`LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama`).
- **Citations stay `source_name` + `chunk_index` in the default response.** Raw
  chunk text / scores are surfaced **only** behind an explicit opt-in local-debug
  flag — never in the default `/ask` response (preserves ADR 0003 privacy
  narrowing).

## Hard constraints (binding)

- Qdrant remains the v0 vector DB. Provider/reranker abstractions stay small,
  explicit, testable.
- **No new *default* runtime dependencies.** The reranker backend is an optional
  extra only; hybrid retrieval uses a light local lexical signal (no heavy model
  / no torch in the default path); real embeddings go through Ollama (no new dep).
  Any dependency must clear the AGENTS.md §5 gate and be documented in an ADR.
- No cloud APIs, secrets, telemetry, or model downloads in code.
- Keep deterministic/mock providers for tests; the unit gate must run offline
  with no model and no live Qdrant.
- Default `/ask` response stays privacy-narrow (no raw chunks/paths).
- Narrow, package-scoped changes; preserve passing tests. No architecture
  direction change without an ADR in `docs/adr/`.

### Validation gate (run all, every loop)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Live RAG checks (Qdrant + indexed docs + a real embedding model) are **manual
smoke steps**, not part of the unit gate — document results in the loop report,
don't claim them unless actually run. Commit convention as in prior sprints.
Scopes: `rag`, `embeddings`, `retrieval`, `docs`.

---

## R1 — Measure first: retrieval-eval harness + BGE-M3 option

**Objective.** You cannot credibly improve retrieval without measuring it. Build
a small retrieval-eval harness, and make BGE-M3 a first-class embedding option.

**Files.**
- New: `evals/rag-retrieval/SPEC.md` + a tiny labeled fixture set (queries →
  relevant doc/chunk ids) + a stdlib scorer computing **recall@k** and **MRR**.
- Edit: `src/local_ai_lab/embeddings/` — ensure BGE-M3 works as an Ollama
  embedding model (`OllamaEmbeddingProvider` with `model="bge-m3"`); add any
  config/validation needed. Keep `deterministic` the default.
- Edit: `src/local_ai_lab/cli/doctor.py` — add an embedding-model check that, when
  the ollama embedding provider is selected, verifies the model is installed and
  recommends `ollama pull bge-m3` (mirror the existing actionable model check).
- Edit: `docs/rag.md`, `README.md`.
- Tests: `tests/test_rag_retrieval_eval.py` (scorer runs offline with
  deterministic/fake providers), extend `tests/test_embeddings.py`.

**Definition of Done.** A retrieval-eval set + scorer produce recall@k/MRR offline
with fake/deterministic providers; BGE-M3 is documented + doctor-guided as the
recommended real backend; deterministic stays default; gate green.

---

## R2 — Reranker abstraction (light default, optional local backend)

**Objective.** Add a reranking stage after retrieval, measured by R1.

**Files.**
- New: `src/local_ai_lab/rerankers/base.py` (`Reranker` protocol),
  `identity.py` (no-op/deterministic default), `factory.py`.
- Edit: `src/local_ai_lab/rag/service.py` — apply the reranker to retrieved
  chunks before prompt assembly.
- Edit: `src/local_ai_lab/config/settings.py` — `reranker_provider` (default
  `identity`).
- Edit: `pyproject.toml` — add an **optional** `[project.optional-dependencies]`
  `rerank` extra (e.g. a local cross-encoder lib); do NOT add to the default
  install.
- New ADR: `docs/adr/` — reranker abstraction + the optional-extra dependency
  decision (document the missing stdlib capability, import location, transitive
  risk, removal plan, per AGENTS.md §5).
- Tests: `tests/test_rerankers.py` (identity + a fake cross-encoder), reranker
  wiring in `tests/test_rag_service.py`.

**Definition of Done.** Reranker protocol + identity default wired into the RAG
service; optional local backend behind the `[rerank]` extra (not installed by
default); behavior measured against the R1 eval; ADR committed; gate green offline
(no torch in the default path).

---

## R3 — Hybrid dense + lexical retrieval

**Objective.** Combine dense vectors with a light local lexical (BM25-style)
signal via reciprocal-rank fusion, behind a setting. Measured by R1.

**Files.**
- Edit: `src/local_ai_lab/vectorstores/qdrant.py` + `base.py` — add a
  lexical/sparse signal (computed locally, **no heavy model**) and RRF fusion with
  dense results.
- Edit: `src/local_ai_lab/rag/service.py` + `factory.py` — hybrid path behind
  `retrieval_mode` (`dense` default | `hybrid`).
- Edit: `src/local_ai_lab/config/settings.py`.
- Tests: extend `tests/test_vectorstore_*` + `tests/test_rag_service.py` (hybrid
  path with fakes); show recall@k/MRR via R1.

**Definition of Done.** Hybrid retrieval behind a setting (dense stays default);
RRF fusion; measured (or documented) effect via R1; no heavy deps; gate green.

---

## R4 — Citations + opt-in retrieval inspection

**Objective.** Clean source-aware citations by default; raw retrieval visible only
behind an explicit local-debug opt-in.

**Files.**
- Edit: `src/local_ai_lab/rag/service.py`, `api/schemas.py`, `api/app.py`,
  `cli/app.py` — render citations as `source_name` + `chunk_index` in the default
  response (keep ADR 0003 narrowing). Add an **opt-in** inspection mode (explicit
  flag/env) that surfaces retrieved chunk text + scores for local debugging —
  never in the default response.
- Tests: `tests/test_api.py` / `tests/test_rag_service.py` — assert the **default
  response contains no raw chunk text/paths**, and that the inspection flag
  surfaces them only when explicitly set.

**Definition of Done.** Source-aware citations by default; opt-in inspection
behind an explicit flag; privacy default proven by tests (negative case); gate
green.

---

## R5 — Docs, ADR consolidation, roadmap

**Objective.** Make the docs reflect the new retrieval capabilities truthfully.

- Tick the completed `docs/rag.md` TODOs; add a `docs/lab-notes/` entry; update
  `ROADMAP.md` v2 progress. Ensure the reranker/hybrid ADRs (from R2/R3) are
  coherent. Truthful + locally verifiable only — distinguish "implemented +
  measured on the eval set" from "available behind an optional extra / not yet
  benchmarked on real corpora."

**Definition of Done.** Docs/roadmap reflect actual state; no overclaiming; gate
green.

---

## Sequence & rationale

1. **R1** first — measurement unblocks honest evaluation of R2/R3.
2. **R2 → R3** — reranking, then hybrid; each measured against R1.
3. **R4** — citation/inspection UX.
4. **R5** — consolidate docs.

Optional, user-driven milestone (not a Codex loop): ingest a real local corpus and
run the R1 eval with **BGE-M3 embeddings** to get real recall@k/MRR numbers — the
thing that proves the retrieval lane is genuinely useful.
