# Goal — Fix & depth sprint (observed-throughput matching · harder RAG corpus)

- **Branch:** `codex/fix-and-depth`
- **Thesis:** close the one known defect from live use, then give the RAG eval
  enough difficulty to actually mean something.

```text
GOAL: Execute loops F1 -> F2 in order in local-ai-lab. Read AGENTS.md first.

STANDING CONSTRAINTS (all loops):
- Dashboard stays stdlib-only; NO new default runtime deps; NO external assets
  or <script src>; the dashboard makes NO network calls at render time.
- Render paths NEVER spawn subprocesses (delete-safety tests patch global
  subprocess.run and assert zero calls during renders).
- Reuse Midnight Neon tokens + the metric-tip pattern. Escape everything.
- Never fabricate: missing values render as em dash, estimates stay labeled
  "est.", observed values only ever come from real recorded runs.
- Your sandbox cannot write .git: do NOT attempt git commit; end each loop with
  a report (files, tests, gate lines).
- Full validation gate green before ending each loop:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .

F1 — OBSERVED THROUGHPUT ON MY MODELS (known defect)
- Symptom: on My Models, the "Observed N tok/s" decoration beside a row's fit
  pill usually does not appear, even when that model HAS real recorded runs
  visible on the Benchmark page. The estimate shows but the observed number —
  the more truthful signal — is missing. Root cause is in how inventory rows are
  matched to dashboard model/run records (exact-id vs model_name vs the
  local-inventory overlay's candidate ids), so the lookup misses.
- Fix the matching so an inventory row resolves to its dashboard runs whenever a
  real correspondence exists. Prefer, in order: exact local model id recorded on
  the run/candidate; the overlay's candidate_id mapping; a normalized model-name
  match (case/punctuation/whitespace-insensitive) as the last resort. A match
  must be a real correspondence — never guess by fuzzy similarity, and never
  attribute one model's numbers to another.
- When matched, show the observed tok/s from that model's MOST RECENT run (and
  keep the estimate alongside — observed beats estimate but both are useful).
  When no real match exists, show nothing extra (no zero, no em-dash-as-number).
- Also surface the same observed value on the Discover rows where a candidate
  already has runs, if that falls out naturally — do not force it.
- Tests: exact-id match, overlay candidate_id match, normalized-name match,
  no-match renders no observed decoration, most-recent-run selection when a
  model has several runs, never cross-attributes between two similarly named
  models, render subprocess-safety.
- Verify against REAL local data before reporting: the repo's dashboard DB has
  runs for Qwen3-Coder-30B-A3B and Dolphin-Mistral-24B Venice; those inventory
  rows must show observed tok/s.

F2 — HARDER RAG EVAL CORPUS (make the numbers mean something)
- Today evals/rag-retrieval has repo-docs-v0.1: 4 queries, and BGE-M3 scores
  recall@5 = 1.0 / MRR = 1.0. That proves the plumbing works but is too easy to
  measure retrieval quality — a perfect score on 4 easy queries tells us nothing
  about whether hybrid retrieval or reranking actually help.
- Build a NEW corpus + labels: evals/rag-retrieval/corpora/repo-docs-v0.2/,
  keeping v0.1 intact as the regression fixture. Target ~20-30 labeled queries
  over a larger slice of the repo's own docs (architecture, ADRs, AGENTS.md,
  benchmarking methodology, RAG docs, lab notes...). Deliberately include HARD
  cases, because that is the entire point:
    * near-duplicate/competing passages where several docs discuss the same
      topic and only one answers the query,
    * multi-hop-ish questions whose answer lives in a doc that does not repeat
      the question's vocabulary (tests semantic retrieval over keyword luck),
    * questions using different terminology than the source doc (paraphrase),
    * a few queries with MULTIPLE relevant chunks,
    * at least a couple of genuinely hard ones you expect retrieval to miss.
  Labels: stable chunk ids only — no private paths, raw text, keys, or
  responses. Document the corpus design + intent in a short SPEC or README
  section for repo-docs-v0.2.
- Extend the existing collect/scorer path to run this corpus (reuse
  collect.py + scorer.py; no rewrite).
- Report the exact commands the human should run to score v0.2 with real
  embeddings (bge-m3 via Ollama is installed) across the configurations worth
  comparing: dense vs hybrid, and identity vs cross-encoder reranker. Do NOT run
  them yourself (they need a real embedding model) and do NOT record any
  results you did not observe.
- Tests stay offline/fixture-based as today; the CI-safe deterministic path must
  remain green and must not depend on the new corpus needing a model.

Per loop: implement, test, run the full gate, STOP with a concise report
(files, tests, gate lines). Never claim a command passed unless it was run.
Begin with F1.
```
