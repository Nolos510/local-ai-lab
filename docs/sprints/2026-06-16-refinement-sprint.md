# AI Lab OS Refinement Sprint — 2026-06-16

Source of truth for the four-iteration refinement sprint. Codex (or any builder)
executes one **loop** at a time against this document. Each loop is independently
shippable and must leave the repo green.

## Operating Rules (read first)

- Read [AGENTS.md](../../AGENTS.md) before starting. All non-negotiable
  local-first, dependency-gate, and Definition-of-Done rules apply.
- **No new runtime dependencies.** Every iteration here is implementable with the
  Python standard library. The dashboard stays stdlib-only (see DECISIONS.md,
  2026-05-12 "Dependency-Free Dashboard MVP").
- **No external network calls** from the dashboard at render time (this sprint
  removes the one that exists).
- Keep changes narrow and package-scoped. One iteration = one focused PR/commit
  group with tests. Do not refactor unrelated code.
- Preserve current dashboard behavior and all 46 existing dashboard tests.

## Per-Loop Protocol

For every iteration:

1. Implement the change in the listed files only.
2. Add/extend the listed tests.
3. Run the **validation gate** (below). All must pass.
4. Update docs/roadmap as noted.
5. Commit with the message convention, then **stop and report** before the next
   iteration.

### Validation gate (run all, every loop)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run ruff check .
```

If `uv` is unavailable, `ruff check .` against the project config is acceptable;
document the substitution in the report.

### Commit convention

```
<scope>: <summary>

<what changed, why, how validated, what was NOT tested>

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

Scopes: `dashboard`, `ci`, `cli`.

---

## Iteration 1 — Inline SVG charts (zero-dependency)

**Objective.** Add visual comparison to the dashboard. Bars/sparklines rendered
as inline SVG strings — no JS, no chart library, fully theme-aware via existing
CSS variables.

**Why (leverage).** Highest visible payoff. A "model performance dashboard" with
no charts undersells the data. Also lays the rendering groundwork for v3 metrics
(TTFT, tokens/sec, memory pressure).

**Files.**
- New: `apps/model-dashboard/model_dashboard/charts.py`
- Edit: `apps/model-dashboard/model_dashboard/server.py`
  - `_compare` (server.py:2884) — primary home for charts.
  - `_overview` (the `/` route handler) — a summary bar.
  - The `<style>` block in `_layout` (server.py:2076+) — add chart CSS classes.
- New: `apps/model-dashboard/tests/test_charts.py`

**Data to chart (real columns, verified).**
- `model_runs.tokens_per_sec`, `model_runs.ram_usage_gb` — throughput / footprint.
- `eval_scores.total_score` — headline quality bar per model.
- Per-axis dimensions on a model detail / compare view (optional radar):
  `instruction_following, truthfulness_uncertainty, reasoning, coding_debugging,
  agent_planning, local_ai_lab_usefulness, research_synthesis,
  business_seo_strategy, long_context, creativity, speed_practicality`.
- TTFT / latency columns do **not** exist yet — do not invent them. Leave a
  `# v3: TTFT/latency once captured` note where a future series would slot in.

**Implementation notes.**
- `charts.py` exposes pure functions returning SVG strings, e.g.
  `horizontal_bars(items, *, value_format="{:.1f}", max_value=None)` where
  `items` is a list of `(label, value)`. Deterministic output (testable).
- Use `viewBox` + percentage/computed widths so it scales responsively.
- Color via CSS: bars `fill: var(--accent)`, text `fill: var(--muted)`, gridline
  `var(--line)`. No hard-coded hex so light/dark themes both work.
- HTML-escape every label (`xml.sax.saxutils.escape` or the existing `escape`
  import) — labels come from model names.
- Empty/Null series returns a muted "No data yet" placeholder, never a broken
  SVG.
- Keep bar height/gap constants small and named at module top.

**Tests (`test_charts.py`).**
- Returns a string containing `<svg` and a `viewBox`.
- N items → N `<rect`/bar elements.
- Largest value maps to full bar width; zero/empty → placeholder text, no
  `NaN`/`inf`, no division-by-zero.
- A label containing `<`/`&` is escaped in the output.

**Docs.** Tick the relevant v1 "Compare at least two models in the dashboard"
evidence in [ROADMAP.md](../../ROADMAP.md) only if compare visualization now
ships; add a one-line lab note under `docs/lab-notes/`.

**Definition of Done.** Compare and Overview render charts for real rows; demo
rows still render; all 46 prior tests + new chart tests pass; no new deps; no
network calls.

---

## Iteration 2 — Vendor icons offline (close the CDN gap)

**Objective.** Remove the only external network dependency in the dashboard. The
icon font is currently fetched from `cdn.jsdelivr.net` at
[server.py:2075](../../apps/model-dashboard/model_dashboard/server.py) — the
dashboard shows no icons offline, which contradicts the local-first posture.

**Why (leverage).** Small, self-contained, and fixes a real local-first
inconsistency. Makes the dashboard fully functional with no internet.

**Files.**
- New: `apps/model-dashboard/model_dashboard/icons.py`
- Edit: `apps/model-dashboard/model_dashboard/server.py`
  - Remove the `<link rel="stylesheet" href="https://cdn.jsdelivr.net/...">`.
  - Replace every `<i class="ti ti-*">` usage with `icon("ti-*")` output.
- New: `apps/model-dashboard/tests/test_icons.py`

**Implementation notes.**
- Enumerate every icon in use first:
  `grep -oE 'ti-[a-z0-9-]+' apps/model-dashboard/model_dashboard/server.py | sort -u`.
  Include `NAV_ICONS` (server.py:48) and every `_stat_card(... "ti-*")` call.
- `icons.py` holds an `ICONS: dict[str, str]` mapping each used name to its inline
  SVG path data, plus `icon(name, *, cls="ti")` returning
  `<svg class="{cls}" viewBox="0 0 24 24" ...>{paths}</svg>`.
- Source the path data from Tabler Icons (MIT licensed). Add a short MIT
  attribution header in `icons.py` and a line in a `NOTICE` or the dashboard
  README. Do **not** vendor the whole font — only the ~15 used glyphs.
- Unknown icon name → a neutral fallback glyph (e.g. circle), never a crash.
- Keep the `.ti`/`.nav .ti` CSS sizing rules; they now style `<svg>` instead of
  `<i>` (set `width/height: 1em; fill: currentColor` as needed).

**Tests (`test_icons.py`).**
- Rendered `_layout(...)` output contains **no** `cdn.jsdelivr` and no `http`
  stylesheet link.
- Every name in `NAV_ICONS` resolves to a string containing `<svg`.
- Unknown name returns the fallback, not an exception.

**Docs.** Note the offline-icons change in a `docs/lab-notes/` entry and the
dashboard README. Mention MIT attribution.

**Definition of Done.** Dashboard renders all icons with networking disabled; no
`http(s)` asset references remain in layout; tests pass; no new deps.

---

## Iteration 3 — Gate dashboard + eval tests in CI

**Objective.** The 46 dashboard tests and the eval-harness tests are not run in
CI today — only the root `tests/` suite via `uv run pytest`. Add them so they
gate PRs.

**Why (leverage).** Cheap, low-risk, and protects every iteration above from
silent regressions.

**Files.**
- Edit: `.github/workflows/ci.yml`

**Implementation notes.**
- After the existing `Pytest` step, add steps mirroring its existence-guarded
  style:
  - `Dashboard tests`:
    `python3 -m unittest discover -s apps/model-dashboard/tests`
    guarded by `[ -d apps/model-dashboard/tests ]`.
  - `Eval harness tests`:
    `python3 -m unittest discover -s evals/local-llm-benchmark/tests`
    guarded by `[ -d evals/local-llm-benchmark/tests ]`.
  - `Dashboard smoke`:
    `python3 scripts/model_dashboard_smoke.py`
    guarded by `[ -f scripts/model_dashboard_smoke.py ]`.
- These are stdlib `unittest`; they run inside the already-synced job. Do not add
  the `--probe-server` flag (it needs a local bind that CI may block).

**Tests / validation.** Verify locally that all three commands pass, then confirm
the workflow YAML is valid (`yaml`-lint or a dry parse). Optionally prove the
gate works by temporarily breaking a dashboard test and confirming the new step
fails (revert before commit).

**Docs.** None required beyond the commit message; optionally note in AGENTS.md
§11 that CI now runs these suites.

**Definition of Done.** CI runs all three new steps on PR + push to main; a
failing dashboard test would now fail CI.

---

## Iteration 4 — Unified `ai-lab` CLI

**Objective.** One operable surface for the product loop instead of scattered
commands (`run_dashboard.py`, `harness.py`, `scripts/*`, copy-paste import
commands). Add an `ai-lab` console script that orchestrates the existing pieces.

**Why (leverage).** Biggest utility payoff; turns the documented loop into a
single tool. Highest effort — do it last, on top of the now-charted, offline,
CI-gated base.

**Files.**
- New: `src/local_ai_lab/cli/lab.py` (with `main()`).
- Edit: `pyproject.toml` — add to `[project.scripts]`:
  `ai-lab = "local_ai_lab.cli.lab:main"` (alongside the existing
  `local-ai-lab = "local_ai_lab.cli.app:main"`).
- New: `tests/test_lab_cli.py` (root `tests/`, runs under `uv run pytest`).

**Subcommands (argparse only).**
- `ai-lab status` — print loop state: ready candidates, artifacts, draft vs
  confirmed scores, latest decisions. Read directly from
  `data/model_registry/candidates.csv`, `data/eval_results/`, and the dashboard
  SQLite (`data/dashboard/model_dashboard.sqlite`). Reuse `model_dashboard.db`
  read helpers where clean.
- `ai-lab radar list` — list candidates from the registry CSV.
- `ai-lab bench run --candidate <id>` — invoke the existing benchmark harness
  (`evals/local-llm-benchmark/harness.py`) via `subprocess`.
- `ai-lab import --run <benchmark_run_id>` — invoke the existing CSV import path
  (`model_dashboard.csv_io.import_all` / the documented import command).
- `ai-lab report` — invoke the existing reports path.
- `ai-lab dashboard [--port N]` — launch `apps/model-dashboard/run_dashboard.py`.

**Boundary guidance (important).** `src/local_ai_lab` and
`apps/model-dashboard` are separate packages. To respect that boundary and
AGENTS.md "small, explicit, testable":
- For `bench`, `import`, `report`, `dashboard` — **shell out** (`subprocess`) to
  the existing entry points/commands rather than cross-importing. This keeps the
  CLI a thin orchestrator and avoids tangling the two packages.
- For `status` / `radar list` — direct stdlib reads (`csv`, `sqlite3`) are fine.
- Do not duplicate business logic that already lives in the harness or
  `csv_io`.

**Tests (`test_lab_cli.py`).**
- Arg parsing builds the expected command for each subcommand (monkeypatch
  `subprocess.run` and assert the argv).
- `status` formats counts from a temp fixture DB/CSV without launching anything.
- Unknown subcommand exits non-zero with usage.

**Docs.** Add an `ai-lab` quick-start block to README.md and AGENTS.md §11;
record an ADR under `docs/adr/` if the CLI changes how the loop is operated
(it introduces a new operating surface, so an ADR is appropriate).

**Definition of Done.** `ai-lab status` runs offline against fixtures; each
subcommand dispatches correctly under test; `pyproject` exposes the script; no
new deps; `uv run pytest` green.

---

## Sequence & rationale

1. **Charts** — biggest visible win, unblocks v3 metrics surfacing.
2. **Offline icons** — closes the local-first CDN gap before more UI ships.
3. **CI gate** — protects iterations 1–2 and everything after.
4. **`ai-lab` CLI** — top-level utility, built on the hardened base.

Each loop ends with the validation gate green and a report. Do not start the next
loop until the current one is shipped and reported.
