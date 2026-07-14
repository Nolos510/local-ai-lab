# Goal — Scoring-loop sprint (drill-down · local judge · efficiency frontier · regression watch)

- **Branch:** `codex/scoring-loop`
- **Thesis:** close the last manual bottleneck (hand-scoring) and turn the lab's
  accumulated runs into comparative + longitudinal insight. Every loop builds on
  data/infra that already exists.

```text
GOAL: Execute loops S1 -> S4 in order in local-ai-lab. Read AGENTS.md first —
local-first rules, dependency gate, and Definition of Done are binding.

STANDING CONSTRAINTS (all loops):
- Dashboard stays stdlib-only; NO new default runtime deps; NO external/network
  calls or <script src> from the dashboard (inline no-src JS only); reuse
  Midnight Neon tokens and the metric-tip explainer pattern.
- Render paths must NEVER spawn subprocesses (delete-safety tests patch global
  subprocess.run and assert zero calls during renders).
- Model execution ONLY behind the existing approval-gate pattern
  (--i-approve-local-run; explicit ids; refusal BEFORE any subprocess/endpoint).
- Never fabricate numbers. Missing metrics render as an em dash, not zero.
- Draft scores NEVER overwrite confirmed scores (score_status discipline).
- Your sandbox cannot write .git: do NOT attempt git commit; leave changes in
  the working tree and end each loop with a report.
- Run the FULL validation gate green before ending each loop:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .

S1 — PER-PROMPT DRILL-DOWN + A/B VIEWER (dashboard)
- Extend the existing /artifacts/<benchmark_run_id> detail page: a per-prompt
  table from the run's raw_responses.jsonl — prompt id, latency (if present),
  token counts (if present), and the response text (HTML-escaped, collapsed to
  a preview with an expand affordance; loopback-only dashboard so local viewing
  of the lab's own raw artifact is sanctioned — never include private absolute
  paths).
- A/B compare: choose two runs that share prompt_set_id (picker on the
  Benchmark page or artifact page) -> side-by-side responses per prompt with
  per-run latency/tokens. Same escaping/collapse rules.
- Graceful degradation: missing/corrupt jsonl lines are skipped with a visible
  note; runs without raw artifacts show an honest empty state.
- Tests: fixture artifacts (2 runs, shared prompt set, one corrupt line);
  escaping of <script> in a response; A/B pairing; empty states; no external
  assets; render subprocess-safety.

S2 — LOCAL-JUDGE DRAFT SCORING (CLI machinery; NO real model call in tests)
- New: ai-lab bench judge --run <benchmark_run_id> --judge-model <exact-id>
  --runner {ollama,lmstudio-cli,openai-compatible} --i-approve-local-run
  [--db ...]. Reads the run's raw_responses.jsonl + the rubric
  (evals/local-llm-benchmark/rubrics/...), prompts the judge model per response
  with a strict JSON-output rubric template, parses per-dimension scores, and
  writes eval_scores rows with score_status='draft' for that run's model.
- Approval gate identical in spirit to bench execute: refusal (with a preflight
  showing run id, judge model, runner, row count, output target) BEFORE any
  subprocess/endpoint call when --i-approve-local-run is absent.
- Honesty: unparseable judge output -> skip that prompt with a note in the
  summary; never invent a score; never touch confirmed rows; judging a run that
  already has confirmed scores still only writes drafts.
- Docs: extend BENCHMARK_METHODOLOGY.md with the judge flow + clear caveat that
  draft scores are suggestions pending human confirmation.
- Tests (fakes only): approval refusal (no subprocess), draft-only writes,
  confirmed rows untouched, parse-failure skipping, preflight enumeration.
- End the loop report with the exact real command for the user to judge the two
  20260714-*-r3 runs with qwen3-coder-30b-a3b-instruct-mlx as judge. Do NOT run
  it yourself.

S3 — EFFICIENCY FRONTIER (dashboard, cheap)
- New pure helper: efficiency = tokens_per_sec / ram_usage_gb (None-safe,
  div-by-zero-safe) surfaced as a column on the Benchmark runs table with a
  metric-tip explaining it ("throughput per GB of peak RAM — higher earns its
  memory").
- New charts.py scatter: x = tokens_per_sec, y = confirmed total_score, bubble
  radius = ram_usage_gb, one point per model (latest confirmed run). Runs
  without confirmed scores are excluded from the scatter with an honest note.
  Deterministic SVG, escaped labels, empty-state placeholder, bars/points never
  exceed the plot area.
- Tests: efficiency math (None/zero), scatter point count, exclusion note,
  empty state, escaping.

S4 — REGRESSION WATCH (CLI + model detail)
- New: ai-lab bench diff --run <id-A> --run <id-B> (same model expected; warn
  if not) -> table of deltas for tokens_per_sec, total_latency_seconds,
  ram_usage_gb, and confirmed total_score where present: absolute + % change,
  missing values as em dash. Read-only (no model calls, no approval needed).
- Dashboard model detail page: a perf-over-time strip (existing runs ordered by
  date_tested) — small deterministic SVG sparkline per metric via charts.py,
  with values labeled; single-run models show an honest "one run — nothing to
  compare yet".
- Tests: delta math incl. missing metrics; wrong-model warning; sparkline
  determinism + single-run state.

Per loop: implement, test, run the full gate, STOP with a concise report
(files, tests, gate lines). Never claim a command passed unless it was run.
Begin with S1.
```
