# Goal — "Answers, not data" sprint (Fit Advisor · Task Recommender · Batch Queue)

- **Branch/worktree:** `codex/fit-advisor` (worktree `.worktrees/fit-advisor`)
- **Thesis:** the lab collects hardware snapshots, quant metadata, per-dimension
  scores, and real perf runs — but never answers the user's actual questions.
  This sprint turns data into answers. Community demand validated (VRAM-fit
  calculators are a whole tool category on HF/web).

```text
GOAL: Make the local-ai-lab dashboard ANSWER the three questions every local-LLM
user has, using only data the lab already collects. Execute loops A1 -> A2 -> A3
in order. Read AGENTS.md first — its local-first rules, dependency gate, and
Definition of Done are binding.

HARD CONSTRAINTS:
- Dashboard stays stdlib-only; NO new default runtime deps; NO external/network
  calls from the dashboard at render time (inline no-src JS only — the
  test_capability_page_uses_no_external_assets invariant must stay green).
- Reuse Midnight Neon tokens (var(--*)); match the existing 4-section IA
  (Home / Discover / My Models / Benchmark) and the metric-tip explainer pattern.
- Model execution ONLY behind the existing approval gate. Never fabricate
  numbers: estimates must be labeled "est."; recommendations must come from
  CONFIRMED scores only.
- Full validation gate green before every commit:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .
  Commit per loop (scope: dashboard/cli/bench), then STOP and report.

A1 — FIT ADVISOR ("Can I run it?") — dashboard + small pure module
- New apps/model-dashboard/model_dashboard/fit.py: pure stdlib functions that
  estimate memory need from params_b + quantization bits:
  est_weights_gb = params_b * bits/8 * 1.1 overhead; plus a context overhead
  allowance. Classify against the latest hardware snapshot memory (from the
  existing capability/hardware profile data) minus a 16 GB system reserve:
  comfortable (<50% of budget) / fits (<80%) / tight (<100%) / exceeds.
  Unknown params/quant -> "unknown" (never guess silently).
- Surface a "Fit" pill (with metric-tip explaining the estimate math + that it
  is an estimate) on: Discover candidate rows, My Models rows, and the Home
  "this machine" card (e.g. "fits up to ~230 GB est. weights").
- Where a REAL benchmark run exists for a model (tokens_per_sec in the DB),
  show observed tok/s next to the fit pill — observed data beats estimates.
- Tests: fit math unit tests (boundaries, unknown inputs, no NaN), pill renders
  on all three surfaces, estimate labeled "est.", no external assets.

A2 — TASK RECOMMENDER ("Which of my models for task X?") — Home + Benchmark
- New pure helper (components or a small recommend.py): from CONFIRMED
  eval_scores rows only, compute the best model per dimension using the
  existing per-dimension columns (instruction_following, reasoning,
  coding_debugging, agent_planning, research_synthesis, creativity,
  long_context, speed_practicality...). Group them into user-facing tasks:
  Coding, Reasoning/Agents, Research/Writing, Long context, Fast & practical.
- Home gets a compact "Best for..." panel: task -> model name + score + link to
  the model detail. Only show tasks backed by >=1 confirmed score; if only one
  model is scored, say so honestly ("only 1 model scored — benchmark more to
  compare") rather than implying a comparison.
- Benchmark page: small "leaders" strip above the runs table.
- Tests: recommender ignores draft scores, handles 0/1/N scored models, ties.

A3 — BATCH BENCH QUEUE ("Grow the evidence") — CLI, approval-gated
- Extend ai-lab bench: a queue mode that runs MULTIPLE ready candidates
  sequentially through the EXISTING execute path. One explicit approval lists
  every model id + runner + run id up front (--i-approve-local-run covers the
  enumerated batch only); refuse to start if any candidate lacks an exact local
  model id. Per-model failures don't abort the batch; final summary table.
- No new deps; reuse harness runners. Tests with fakes: no execution without
  approval; batch enumerates before running; partial-failure summary.

Never claim a command passed unless it was run. Begin with A1.
```
