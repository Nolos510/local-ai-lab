# Codex Handoff — Next Iteration (2026-06-23)

Two tracks; the human steers which loop runs. Track A (RAG) handoff already
exists: paste [codex-handoff-rag-quality.md](2026-06-18-codex-handoff-rag-quality.md).
Track B (model-management) block is below.

---

```text
You are the main builder for the Model-Management Consolidation track in the
AI Lab OS repo (local-ai-lab), a local-first Apple Silicon AI lab. Goal:
make the dashboard/CLI model-management work cohere and close the regression
debt from the recent redesign.

START HERE:
1. Read AGENTS.md in full (local-first rules, §4 External Radar metadata rule,
   §5 dependency gate, Definition of Done are binding).
2. Read docs/sprints/2026-06-23-next-iteration.md (Track B, loops M1-M4).
   Execute the loop the human points you at.

CURRENT STATE: Dashboard/CLI is feature-rich and green (~176 tests). Recent work:
Midnight Neon redesign (+ several layout-regression fixes), gated delete action,
background run-tests, auto-import, and a new `ai-lab quant advise` quantization
advisor (opt-in --lookup-hf public-metadata lookup). RAG retrieval lane is still
untouched (that is the separate Track A).

HARD CONSTRAINTS:
- Stdlib-only dashboard; no new DEFAULT runtime deps; no external/network assets
  in the dashboard (inline no-src JS only). The quant advisor's --lookup-hf is the
  ONLY sanctioned external call and only for public metadata (no model
  download/run/API), opt-in, no secrets.
- Model execution only via the approval-gated bench-execute surface.
- Narrow, package-scoped changes; preserve passing tests; no architecture change
  without an ADR.

LOOP PROTOCOL (per loop):
1. Re-read AGENTS.md + the sprint doc; inspect `git status -sb`.
2. Implement only the listed files; add/extend the listed tests.
3. Run the FULL gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
4. Commit self-contained (scope: dashboard, cli, docs), then STOP and report.

THE LOOPS (detail in the sprint doc):
M1 dashboard: Unify the OVERVIEW charts onto the same chart-summary/chart-preview/
   expand-dialog pattern capability/compare already use (overview still used the
   old plain panels). Add chart INVARIANT tests: charts.horizontal_bars must never
   emit a bar width > PLOT_WIDTH and the viewBox width must bound all bars; empty/
   oversized inputs -> placeholder. Confirm the single-column .chart-grid (commit
   5ab2728) reads well on capability/compare or scope per-page.
M2 cli/dashboard: Harden `ai-lab quant advise`. Default local-only; --lookup-hf =
   public metadata ONLY (no download/run/API), opt-in, no secrets/paths, repo-local
   output. Add an ADR (AGENTS.md §4) for the external-network code path. Dashboard
   quant-advice section stays offline (saved local JSON only). Tests use fakes;
   assert NO network call without --lookup-hf.
M3 dashboard/docs: Make the run/inventory action surface coherent — audit
   --enable-run-tests / --enable-import-actions / --enable-delete-actions /
   inventory refresh / background run-tests / auto-import for consistent gating +
   confirm flows; document the operating surface in apps/model-dashboard/README.md
   + a lab note.
M4 docs: Refresh portfolio-case-study.md, resume-bullets.md, a dated lab note, and
   ROADMAP.md to include the model-management lane + redesign. Truthful only; no
   implied live perf data unless a real benchmark has run.

Never claim a command passed unless it was actually run.
```

---

## Notes for the human

- The integrator `/loop` verifies every commit (gate + universal flags: new
  default deps, dashboard external assets, raw chunks in default /ask, unapproved
  model calls, overclaiming) regardless of which track/loop Codex is on.
- M1 is the highest-leverage Track-B loop — it closes the regression-test gap that
  let the overview/redesign bugs through.
- Track A (RAG R1–R5) is the bigger structural gap whenever you want to pivot.
```
