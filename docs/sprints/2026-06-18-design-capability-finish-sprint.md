# AI Lab OS — Design Landing + Capability Finish Sprint (2026-06-18)

Finishes the [Capability Sprint](2026-06-17-capability-sprint.md) (L4.5/L5/perf/
portfolio still open) and lands the polish opened by the Midnight Neon redesign.

## Where we are

Committed and green (dashboard 67, eval 8, repo pytest 141, ruff):

- Capability Sprint **L0, L1, L2, L3, L4 (baseline), L6 (interim)** are done.
  L3 (approval-gated benchmark execution) is verified — the gate refuses any
  model call without explicit `--model-id`/`--runner`/`--run-id` + approval.
- The dashboard was **redesigned** ("Midnight Neon": dark-first, glassmorphism,
  gradient title/metrics, neon nav) and the top nav became a **left collapsible
  sidebar** with a persistent (localStorage) toggle — committed in `992f661`.

Still open: **L4.5** (gated delete), **L5** (server.py modularization),
**L4 perf follow-up**, **L6 refresh** — plus design polish the redesign invites.

## Hard constraints (binding)

- No new runtime dependencies. Dashboard + harness stay stdlib-only.
- **No external/network assets in the dashboard.** The only client JS allowed is
  **inline, no `src`, no network** (the sidebar toggle established this). The
  test `test_capability_page_uses_no_external_assets` enforces it — keep it green.
- Model execution stays confined to the L3 surface, behind explicit per-run
  approval. No other path calls a model. No cloud APIs, secrets, telemetry.
- Build on the committed Midnight Neon design — new UI (e.g. the delete confirm
  page) must reuse its tokens/classes, not introduce a second visual language.
- Narrow, package-scoped changes; preserve passing tests. No architecture change
  without an ADR in `docs/adr/`.

### Validation gate (run all, every loop)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Commit convention as in prior sprints. Scopes: `dashboard`, `bench`, `docs`, `ci`.

---

## F1 — L4.5 gated delete action (carryover)

Build exactly as specified in
[Capability Sprint, L4.5](2026-06-17-capability-sprint.md#l45--installed-models-delete-action-gated-recoverable):
per-row **Remove** in the Installed Models tab — **off by default**
(`--enable-delete-actions`), **two-step confirm**, LM Studio → macOS **Trash**
(recoverable, `osascript`, no new dep), Ollama → **`ollama rm`**, **path-contained**
to `~/.lmstudio/models` / `~/.ollama/models`, never `rm -rf`, never a
client-supplied path. **Fold in** the scanner fix (skip `.DS_Store`-only folders).
ADR required. Tests with fakes (no real deletion).

**Design addition:** the confirm page + delete control must match the committed
Midnight Neon style (reuse `.panel`, `.pill`, button tokens, `var(--*)`); the
control is destructive, so use the danger/draft color treatment for the confirm
button, not the accent gradient.

---

## F2 — Design polish

**Objective.** Finish the look the redesign opened. Small, contained, no new deps.

**(a) Neon-ify the SVG charts.**
- Files: `apps/model-dashboard/model_dashboard/charts.py`, the chart CSS classes
  in `server.py` (`.chart-bar`, `.chart-label`, `.chart-value`, `.chart-gridline`).
- Give bars the accent gradient: add an SVG `<linearGradient>` (violet `#8b7bff`
  → cyan `#2ad4ee`) in the chart `<defs>` and fill bars with it; keep a solid
  `var(--accent)` fallback. Stay deterministic/testable; keep the empty-state
  placeholder.
- Tests: extend `test_charts.py` — output still contains `<svg`/`viewBox`, N bars,
  gradient def present, empty series still yields the placeholder.

**(b) Collapsed-rail tooltips.**
- When the sidebar is collapsed, hovering an icon should reveal its label (the
  `<span>` is hidden when collapsed). Use a CSS tooltip (e.g. `title` attribute,
  or a `::after` from the link's text) — no JS beyond what exists. Keep it
  accessible (don't remove the label from the DOM; visually hide it).

**Definition of Done.** Charts render with neon gradient bars + graceful empty
state; collapsed sidebar shows labels on hover; gate green; no external assets.

---

## F3 — L5 server.py modularization (carryover, now larger)

Build as specified in
[Capability Sprint, L5](2026-06-17-capability-sprint.md#l5--serverpy-modularization-maintainability):
split `server.py` (~4,170 lines now) into `layout.py` + `components.py` +
`filters.py` + `pages/<page>.py`; `server.py` keeps routing + `make_handler` +
`serve`. **Behavior-preserving** — all 67 dashboard tests must pass **unchanged**
(import-path edits only).

**Now also relocate:** the expanded Midnight Neon `<style>` block, the sidebar
markup (`.app`/`.sidebar`/`.brand`/`.collapse-btn`), and the **inline toggle
script** — the script must remain inline (no `src`) so the no-external-assets
test stays green. Land page-group by page-group if risk grows; report remainder.

---

## F4 — L4 perf-series follow-up

**Objective.** Surface the perf columns L3 added (`ttft_seconds`,
`total_latency_seconds`, plus existing `tokens_per_sec`) in the dashboard.

- Files: `server.py` compare/capability views, `charts.py`.
- Render latency / tokens-per-sec bars via `charts.py` (neon gradient from F2),
  with a **graceful empty state** — there is no real perf data until an approved
  L3 run is executed, so the view must read cleanly with all-null columns.
- Tests: the view renders with empty perf data and with a fixture row that has
  perf values.

**Definition of Done.** Compare/capability show perf series when present, degrade
cleanly when absent; gate green.

---

## F5 — L6 portfolio refresh

Update `docs/portfolio-case-study.md`, `docs/resume-bullets.md`, a
`docs/lab-notes/2026-06-18-design-capability-finish-complete.md`, and `ROADMAP.md`
to reflect the **redesign**, the **gated delete action**, and the **approval-gated
execution** capability. **Truthful + locally verifiable only** — if no real
benchmark has been executed yet, say so (do not imply live perf data exists).

---

## Sequence & rationale

1. **F1** (delete) and **F2** (polish) — dashboard features land first.
2. **F3** (L5) — modularization sweeps up F1 + F2 + redesign in one move.
3. **F4** (perf) and **F5** (portfolio) — after the refactor.

Optional, user-driven milestone (not a Codex loop): **execute one real approved
benchmark** (e.g. `gpt-oss:20b` or `qwen3-coder-30b-a3b-instruct-mlx`) so F4's
charts show live data and F5 can claim it truthfully.
