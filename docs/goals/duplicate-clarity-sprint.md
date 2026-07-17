# Goal — Duplicate-test clarity sprint (authoritative run · grouped history · fresh-id guard)

- **Branch:** `codex/duplicate-clarity`
- **Thesis:** the lab intentionally keeps every benchmark run (history powers
  `bench diff` + perf sparklines), but with many runs per model, "which run is
  current?" is implicit and the runs table reads as clutter. Make current
  explicit, keep history, and close the one silent-overwrite trap. Do NOT change
  the accumulate-history behavior or the ON CONFLICT upsert import.

```text
GOAL: Execute loops D1 -> D2 in order in local-ai-lab. Read AGENTS.md first.

STANDING CONSTRAINTS (all loops):
- Dashboard stays stdlib-only; NO new default runtime deps; NO external assets
  or <script src> (the only client JS is the existing inline sidebar toggle;
  new interactions are plain links/forms handled server-side). Grouping/collapse
  must work without JS (e.g. <details>/<summary> or server-rendered sections).
- Render paths NEVER spawn subprocesses (delete-safety tests patch global
  subprocess.run and assert zero calls during renders). Subprocess work only in
  explicit POST actions / background run flows that tests can patch.
- Reuse Midnight Neon tokens + the metric-tip pattern. Escape everything.
- Never fabricate: missing values render as em dash, never a zero.
- Preserve existing behavior we are NOT changing: runs still accumulate one row
  per distinct benchmark_run_id; import stays idempotent + ON CONFLICT(id) DO
  UPDATE; sorting (U4), decision filters (U3), and observed-tok/s matching (F1)
  keep working.
- Your sandbox cannot write .git: do NOT attempt git commit; end each loop with
  a report (files, tests, gate lines).
- Full validation gate green before ending each loop:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .

D1 — AUTHORITATIVE RUN + GROUPED HISTORY (Benchmark page)
- Define "current/authoritative run" for a model, live-derived, in this priority:
  (1) the run whose benchmark_run_id matches the candidate registry's
  benchmark_run_id column for that model, if present and imported; else
  (2) the most recent run by date_tested (tie-break: highest model_runs.id).
  A pure helper (e.g. in components.py or a small module) returning, per model,
  the authoritative run id + the list of its other runs. Deterministic + tested.
- Benchmark runs table: badge the authoritative run per model with a clear
  "current" pill (metric-tip: "latest / registry-designated run for this model;
  older runs are kept for history and regression diffs"). Do not delete or hide
  older runs.
- Group runs by model so many runs of one model do not read as clutter: render
  each model as a group with its current run shown, and its older runs in a
  no-JS collapsible (<details>) labeled e.g. "N earlier runs". Keep the flat,
  fully-sortable table available too — either the grouping respects the active
  ?sort/?dir (preferred) OR provide a "group by model" toggle via query param
  that defaults ON, with an "ungrouped" view that is the current flat table.
  Whichever is simpler to keep U4 sorting correct — do not break sorting.
- Home "Top Results" and F1 observed-tok/s should reference the authoritative
  run's numbers where they currently use "most recent" (keep them consistent
  with the new definition; do not fabricate if a model has no imported run).
- Tests: authoritative selection (registry match beats recency; recency +
  id tie-break when no registry match; no runs -> none), current badge on the
  right row only, older runs still present + reachable, grouping preserves
  U4 sort, no external assets, render subprocess-safety.

D2 — FRESH-ID GUARD FOR DASHBOARD RE-TESTS (no silent overwrite)
- Problem: a dashboard-triggered test that reuses an existing benchmark_run_id
  would need a forced re-import to surface new numbers (auto-import treats an
  already-imported id as not-pending). Close it at the source: when the
  dashboard starts a run whose computed run_id already exists (in the DB or as
  an eval_results artifact dir), auto-mint a fresh unique run_id by appending a
  short timestamp/increment suffix, so every dashboard re-test is a new run that
  auto-imports normally. Never overwrite an existing artifact dir.
- Applies to both single Run-test and Run-all dispatch. The confirm/preflight
  enumeration must show the actual (possibly newly-suffixed) run ids that will
  be used, so what the user approves is what runs.
- Pure, testable id-minting helper (given existing ids -> next free id);
  collision-safe and deterministic under a fixed clock injected for tests.
- Tests (fakes only, no real execution): reused id gets a fresh suffix, a novel
  id is left unchanged, no existing artifact dir is overwritten, preflight shows
  the final ids, run-all mints distinct ids across the batch.

Per loop: implement, test, run the full gate, STOP with a concise report
(files, tests, gate lines). Never claim a command passed unless it was run.
Begin with D1.
```
