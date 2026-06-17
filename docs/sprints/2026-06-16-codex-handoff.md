# Codex Handoff Prompt — AI Lab OS Refinement Sprint (2026-06-16)

Paste everything in the fenced block below into Codex as the task prompt. It is
self-contained and points Codex at the detailed plan.

---

```text
You are the main builder for a refinement sprint in the AI Lab OS repo
(local-ai-lab), a local-first Apple Silicon AI engineering lab.

START HERE:
1. Read AGENTS.md in full — its local-first rules, dependency-review gate, and
   Definition of Done are binding.
2. Read docs/sprints/2026-06-16-refinement-sprint.md — the sprint plan. It
   defines four iterations ("loops") with exact files, columns, tests, and
   acceptance criteria. Execute them IN ORDER.

HARD CONSTRAINTS (do not violate):
- No new runtime dependencies. Every iteration is standard-library only.
- The dashboard (apps/model-dashboard) stays stdlib-only and must make NO
  external network calls at render time. Iteration 2 removes the one CDN call
  that exists today — do not add others.
- Keep changes narrow and package-scoped. Do not refactor unrelated code or
  rewrite the 3,700-line server.py wholesale. Preserve current dashboard
  behavior and all existing tests.
- Do not download, run, or call any model. Radar candidates are review records,
  not eval scores.
- No architecture-direction change without an ADR in docs/adr/.

LOOP PROTOCOL (repeat for each of the 4 iterations):
1. Implement only the files listed for that iteration.
2. Add/extend the tests listed for that iteration.
3. Run the full validation gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run ruff check .   (or: ruff check .  if uv is unavailable — note it)
4. Update docs/ROADMAP as the iteration specifies.
5. Commit as a self-contained change. Commit message format:
     <scope>: <summary>

     <what changed, why, how validated, what was NOT tested>

     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
   Scopes: dashboard, ci, cli.
6. STOP and report what you did before starting the next iteration. In the
   report state: files changed, tests added, validation-gate results (paste the
   pass/fail lines), and any deviation from the plan.

THE FOUR ITERATIONS (full detail in the sprint doc):
1. dashboard: Inline SVG charts (zero-dependency) on Compare + Overview.
   New apps/model-dashboard/model_dashboard/charts.py + test_charts.py.
   Use real columns only: model_runs.tokens_per_sec, ram_usage_gb,
   eval_scores.total_score and its per-axis dimensions. TTFT/latency columns do
   NOT exist — do not invent them. Theme via existing CSS variables.
2. dashboard: Vendor icons offline. New icons.py with inline SVG for the ~15
   used ti-* glyphs (Tabler, MIT — add attribution). Remove the jsdelivr <link>
   at server.py ~line 2075 and replace every <i class="ti ti-*"> with icon().
   Add test_icons.py asserting no cdn/http asset link remains.
3. ci: Add dashboard-tests, eval-harness-tests, and dashboard-smoke steps to
   .github/workflows/ci.yml, existence-guarded like the current steps. Do not
   use --probe-server.
4. cli: New src/local_ai_lab/cli/lab.py exposing an `ai-lab` console script
   (register in pyproject [project.scripts]). Subcommands: status, radar list,
   bench run, import, report, dashboard. Shell out (subprocess) to existing
   entry points for bench/import/report/dashboard; direct stdlib reads for
   status/radar. Add tests/test_lab_cli.py. Add an ADR in docs/adr/ since this
   introduces a new operating surface.

If a validation command genuinely cannot run in your environment, document the
exact reason in the report — never claim a command passed unless it was run.
Begin with Iteration 1.
```

---

## Notes for the human

- A separate Claude Code `/loop` is running as the integrator: after each Codex
  iteration lands, it re-runs the validation gate, checks progress against the
  sprint doc's Definition-of-Done items, and flags regressions or local-first
  violations. Codex builds; the loop verifies.
- If you want Codex to do all four without pausing, delete step 6's "STOP" and
  tell it to run the gate after every iteration and report once at the end —
  but pausing per-iteration is recommended for review.
