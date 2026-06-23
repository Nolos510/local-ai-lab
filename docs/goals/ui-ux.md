# Goal — UI/UX discrepancies

- **Branch:** `codex/ui-ux`
- **Area:** `apps/model-dashboard/` (presentation only)

```text
GOAL: Systematically fix UI/UX discrepancies in the local-ai-lab dashboard, one
page/area per cycle. After each cycle, pitch ranked improvements; I approve or
redirect; repeat.

SCOPE GUARDRAILS (stay inside these):
- Touch ONLY presentation: layout.py, components.py, the pages/* templates,
  charts.py, icons.py, and CSS. Do NOT change routing, DB/queries, business
  logic, or the data a page shows.
- Behavior-preserving: all existing tests must pass UNCHANGED. Stdlib-only.
- No external/network assets — inline, no-src JS only (the
  test_capability_page_uses_no_external_assets invariant must stay green).
- Reuse the existing Midnight Neon design tokens (var(--*)); do NOT introduce a
  new palette, font, or component language. Make pages CONSISTENT with each
  other, not novel.

METHOD (systematic, not ad-hoc):
- Work one page at a time, in this order: overview, lab, capability, compare,
  inventory, runs, model_detail, radar, specialty, projects, storage, reports.
- Audit each page against this checklist: spacing/alignment, typography scale,
  table overflow + horizontal scroll on wide tables, chart legibility (bars must
  not exceed their plot; text must be readable, not shrunk), responsive at
  <=760px, empty states, hover/focus states, color contrast, consistency with
  sibling pages.

PER-CYCLE LOOP:
1. Pick the next page; list the concrete discrepancies you found.
2. Fix them. Where a bug class is testable, ADD a regression test (e.g. a chart
   bar width never exceeds PLOT_WIDTH; a wide table has overflow-x scroll) so it
   can't silently come back.
3. VERIFY: run the dashboard on :8765, confirm the page returns 200, and visually
   confirm the specific fix (don't trust 200 alone — that's what missed the chart
   overflow). Note what you verified.
4. Run the full gate: dashboard unittest + eval unittest +
   scripts/model_dashboard_smoke.py + uv run pytest -q + uv run ruff check .
5. Commit one cohesive change (scope: dashboard), then STOP and PITCH.

PITCH FORMAT (after each cycle):
- Fixed: bullet list of discrepancy -> fix.
- Proposals: 3-5 ranked improvement ideas, each with {problem, proposal,
  effort S/M/L, risk}. Wait for my approve/redirect before the next cycle.
```
