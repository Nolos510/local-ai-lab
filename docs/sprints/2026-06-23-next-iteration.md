# AI Lab OS — Next Iteration: RAG Quality + Model-Management Consolidation (2026-06-23)

Two parallel tracks. **You steer Codex manually**, so these are steering
references you paste/redirect from — not a contract Codex follows autonomously.
Pick loops in whatever order suits; the integrator `/loop` verifies each commit
against the gate regardless of track.

## Where we are (eval)

- Dashboard/CLI lane is now heavily polished and feature-rich; gate green (~176
  tests). The Midnight Neon redesign introduced a cluster of **layout/overflow
  regressions** (radar scroll, table widths, overview chart overflow) that were
  swept up over ~7 follow-up commits — all caught by eye, not tests.
- A net-new **quantization advisor** (`ai-lab quant advise` + dashboard section,
  opt-in `--lookup-hf`) landed, plus run-test backgrounding, auto-import, and a
  gated delete action.
- The **RAG retrieval lane is still untouched** — the biggest structural gap.
- Inconsistency noted: capability/compare use a newer chart-summary/preview/
  expand pattern; the overview used the old plain panels (just fixed the overflow
  + made the chart grid single-column).

## Validation gate (every loop, both tracks)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Hard constraints unchanged: stdlib-only dashboard; no new *default* runtime deps
(reranker backend behind an optional extra only); no external/network assets in
the dashboard; default `/ask` stays privacy-narrow; model execution only via the
approval-gated L3 surface; no architecture change without an ADR.

---

# Track A — RAG Quality (retrieval)

Execute the existing plan: **[RAG Quality Sprint](2026-06-18-rag-quality-sprint.md)**
(loops R1–R5), with the locked decisions: reranker = abstraction + optional
`[rerank]` extra; embedding default stays `deterministic` (BGE-M3 added as a
documented option, no forced flip); citations stay `source_name`/`chunk_index`
with raw retrieval behind an opt-in local-debug flag. Codex handoff already
written: [codex-handoff-rag-quality.md](2026-06-18-codex-handoff-rag-quality.md).

This is the bigger structural gap — recommended once the model-management
consolidation below is settled (or interleave as you like).

---

# Track B — Model-Management Consolidation

Make the dashboard/CLI model-management work Codex has been building cohere, and
close the regression debt the redesign created.

## M1 — Chart consistency + regression guards

**Objective.** End the "caught by eye, not tests" pattern and unify chart UX.
- Bring the **overview** charts onto the same `chart-summary` / `chart-preview` /
  expand-dialog pattern used by capability/compare (currently inconsistent).
- Add **chart invariant tests** that would have caught the overview bug:
  `charts.horizontal_bars` must never emit a bar `width` exceeding `PLOT_WIDTH`;
  the SVG `viewBox` width must bound all `x`+`width`; empty/oversized inputs
  degrade to the placeholder. (Files: `tests/test_charts.py` / dashboard tests.)
- Verify the single-column `.chart-grid` change (commit `5ab2728`) reads well on
  capability/compare too, or scope per-page if it regresses their layout.

**DoD.** Overview/compare/capability share one chart panel pattern; a chart that
overflows its plot fails a test; gate green.

## M2 — Quant advisor hardening + ADR

**Objective.** Solidify the net-new `ai-lab quant advise` surface.
- Confirm default behavior is **local-only**; the `--lookup-hf` path fetches
  **public metadata only** (no model download/run/API), is opt-in, leaks no
  secrets/paths, and writes only repo-local output.
- This introduces a **new external-network code path** — add an ADR per AGENTS.md
  §4 (External Radar may gather public metadata on demand) documenting scope +
  guardrails. The dashboard quant-advice section must stay **offline** (renders
  saved local JSON only).
- Tests with fakes (no real network); assert no network call without `--lookup-hf`.

**DoD.** Quant advisor documented + ADR'd; opt-in network path tested with fakes;
dashboard section offline; gate green.

## M3 — Run + inventory operating-surface coherence

**Objective.** Make the run/inventory action surface consistent and documented.
- Audit the gated actions (`--enable-run-tests`, `--enable-import-actions`,
  `--enable-delete-actions`, inventory refresh, background run-tests, auto-import)
  for consistent gating, confirm flows, and UX. Reconcile any drift.
- Document the dashboard **operating surface** (which flag enables what, what each
  action does, safety posture) in `apps/model-dashboard/README.md` + a lab note.

**DoD.** One coherent, documented action surface; gating consistent; gate green.

## M4 — Docs / portfolio / roadmap refresh

**Objective.** Reflect the real current state truthfully.
- Update `docs/portfolio-case-study.md`, `docs/resume-bullets.md`, a dated lab
  note, and `ROADMAP.md` to include the model-management lane (quant advisor, run
  automation, delete, inventory) and the redesign. Truthful + locally verifiable;
  no implied live perf data unless a real benchmark has run.

**DoD.** Docs/roadmap match reality; no overclaiming; gate green.

---

## Recommended sequence

1. **M1** — fixes the regression-test gap + chart inconsistency (highest leverage
   given the recent pattern).
2. **M2 → M3** — harden + document the model-management surface.
3. **Track A (R1–R5)** — the RAG structural gap, with the plan already written.
4. **M4** — refresh docs last, once the above land.

Interleave freely — you're steering. The integrator loop checks every commit.
