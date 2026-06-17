# AI Lab OS Capability Sprint — 2026-06-17

**Supersedes and absorbs** the prior [Sprint 3 plan](2026-06-17-refinement-sprint-3.md).
Goal: cross from "impressive scaffold" to a **genuinely useful local lab** by
closing the benchmark execution loop, clearing onboarding friction, and giving
the dashboard real data — then harden maintainability and capture evidence.

Same operating model: one **loop** at a time, full validation gate green, commit,
stop, report. Read [AGENTS.md](../../AGENTS.md) first.

## Audit basis (why these loops)

Current state is healthy: ~190 tests green, CI passing on GitHub, hardened +
offline dashboard, `ai-lab` CLI, ADRs and sprint docs tracked. The gaps that keep
it from being *useful*:

- The benchmark loop is not end-to-end: the harness can execute runs
  (`run_local`, `run_lmstudio_cli`) but `ai-lab bench run` only **prepares**
  artifacts ("does not call a model"), and scoring is manual.
- No automated perf capture (TTFT/tokens-sec/latency/RAM) — the new SVG charts
  have no real perf series to plot.
- RAG retrieval is shallow (deterministic embeddings default; no reranker/hybrid/
  eval sets).
- Onboarding bug: default model `qwen3:14b` is not installed → `doctor` FAILs
  out-of-box.
- `server.py` is 3,854 lines (monolith); three architecture docs are drifting.

## Hard constraints (binding)

- No new runtime dependencies. Dashboard + harness stay stdlib-only.
- No external/network calls from the dashboard at render time.
- **Model execution is allowed only in Loop 3 (L3) and only behind explicit
  per-run approval** of exact model id + runtime + run id (per AGENTS.md and the
  Sprint 3 constraint). No other loop calls a model. No cloud APIs, secrets, or
  telemetry, ever.
- Narrow, package-scoped changes; preserve all passing tests.
- No architecture-direction change without an ADR in `docs/adr/`.
- Runtime artifacts under `data/` stay local state.

### Validation gate (run all, every loop)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Commit convention as in prior sprints. Scopes: `cli`, `bench`, `dashboard`,
`docs`, `ci`.

---

## L0 — Quick fixes & drift cleanup

**Objective.** Remove first-run friction and documentation drift before adding
features.

**(a) Default-model onboarding.**
- Files: `src/local_ai_lab/cli/doctor.py`, `.env.example`, `README.md`.
- Today `doctor` hard-FAILs when the configured model isn't installed. Change it
  to: list installed Ollama models, and if the configured model is missing,
  emit an **actionable** message naming the closest installed model and the exact
  `LOCAL_AI_LAB_OLLAMA_MODEL=...` to set. Do not hardcode a model that may not
  exist; if nothing is installed, say so plainly with the `ollama pull` hint.
- Tests: fake `ollama list` runner — assert the suggestion path and the
  no-models-installed path produce clear guidance, not a bare failure.

**(b) Reconcile architecture docs.**
- Files: `ARCHITECTURE.md` (root), `docs/architecture.md`, `docs/architecture-v1.md`.
- Pick **one** canonical doc (recommend `docs/architecture.md`), merge the unique
  content from the other two into it, and make the others one-line pointers (or
  archive `architecture-v1.md` under a clearly dated note). Update inbound links.

**Definition of Done.** `doctor` gives actionable model guidance instead of a bare
FAIL; exactly one canonical architecture doc; gate green.

---

## L1 — `ai-lab hardware snapshot`

Build exactly as specified in
[Sprint 3, Loop 1](2026-06-17-refinement-sprint-3.md#loop-1--hardware-profile-snapshot):
new `src/local_ai_lab/cli/hardware.py`, wired into `lab.py`, stable JSON to
stdout, optional `--out`, **no private paths / usernames / env / secrets**, no
model calls. Smoke: `uv run ai-lab hardware snapshot`.

---

## L2 — `ai-lab bench matrix`

Build exactly as specified in
[Sprint 3, Loop 2](2026-06-17-refinement-sprint-3.md#loop-2--benchmark-matrix-plan):
new `src/local_ai_lab/cli/bench_matrix.py`, reads `candidates.csv`, Markdown
default + `--json`, marks `blocked` rows, **runs no models**. Smoke:
`uv run ai-lab bench matrix --limit 5`.

---

## L3 — ⭐ Close the benchmark execution loop (approval-gated)

**Objective.** Make the lab actually benchmark a model end-to-end:
**candidate → executed responses → perf metrics → (draft) scores → dashboard
import**, in one sanctioned flow. This is the core utility unlock and the only
loop permitted to call a model.

**Files.**
- Edit: `src/local_ai_lab/cli/lab.py` — add execution to the `bench` surface,
  e.g. `ai-lab bench execute` (or `bench run --execute`).
- Edit: `evals/local-llm-benchmark/harness.py` — capture perf metrics during
  `run_local` / `run_lmstudio_cli`.
- Edit: `apps/model-dashboard/model_dashboard/db.py` — additive schema migration.
- Edit: `apps/model-dashboard/model_dashboard/csv_io.py` — carry new metric
  columns through import.
- Tests: `tests/test_lab_cli.py`, `evals/local-llm-benchmark/tests/test_harness.py`,
  `apps/model-dashboard/tests/test_schema.py` / `test_csv_io.py`.
- New ADR: `docs/adr/` — sanctioned local benchmark execution + approval gate.

**Approval gate (mandatory).**
- Execution requires explicit `--model-id`, `--runner`, and `--run-id`, plus an
  explicit confirmation (`--i-approve-local-run` flag or interactive `yes`).
- Before any model call, print exactly what will run (model id, runtime,
  endpoint/command, run id, prompt-set id) and refuse if approval is absent.
- With approval flags absent, **no model call may occur** — assert this in tests.

**Extra scrutiny requested.**
- Treat this as a safety gate, not a UX prompt. Identity and approval must be
  checked before constructing or invoking any subprocess, HTTP request, harness
  execution, dashboard import, or score export.
- Do not infer runnable identity from a registry row alone. `--model-id`,
  `--runner`, and `--run-id` must be explicit at the command boundary.
- Non-interactive execution must require `--i-approve-local-run`; interactive
  confirmation is acceptable only when stdin is a TTY.
- Tests must prove the negative case: with approval missing, fake model runners,
  fake subprocesses, and fake endpoints are not called and no run/import output
  is produced.
- The preflight output must show the exact local command or endpoint shape,
  model id, runner, run id, prompt set, and dashboard import target before the
  model call. It must not print secrets or private paths beyond the explicit
  local artifact/run path.
- Approval covers only local runtimes. This loop must not introduce cloud model
  APIs, API-key requirements, telemetry, downloads, or external network calls.

**Perf capture (stdlib-only, honest).**
- Extend `model_runs` with nullable `ttft_seconds` and `total_latency_seconds`
  via an additive migration mirroring `db._ensure_eval_score_status`
  (`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`). Reuse existing
  `tokens_per_sec` and `ram_usage_gb`.
- Capture what is cleanly available: total wall-clock latency and tokens/sec
  (tokens ÷ elapsed). `ttft_seconds` only if a streaming request is wired;
  otherwise leave it null — do not fabricate. `ram_usage_gb` stays optional/
  manual unless a clean local read exists (no new deps).
- These columns feed the L4 dashboard charts.

**Draft scores (optional, non-destructive).**
- If a local-judge draft pass is included, it writes `eval_scores` rows with
  `score_status='draft'` and must **never overwrite confirmed scores**. Keep it
  clearly labeled draft.

**Import.**
- Chain into the existing import path (`csv_io.import_all`) so the run lands in
  the dashboard. One command, or two explicit steps — document which.

**Tests.**
- No execution without the approval flags (fake endpoint/subprocess; assert zero
  model calls).
- Perf metrics recorded and imported; schema migration is additive and
  idempotent.
- Draft scores never overwrite confirmed; CSV output deterministic.

**Definition of Done.** With a user-approved local model, one flow produces
executed responses, perf metrics visible in the dashboard, optional draft scores,
and an import — and with approval absent, no model is ever called. ADR committed.
Gate green.

---

## L4 — Dashboard capability view

Build as specified in
[Sprint 3, Loop 3](2026-06-17-refinement-sprint-3.md#loop-3--dashboard-capability-view),
**plus** surface the real perf series L3 now produces (tokens/sec, latency) via
the existing `charts.py` helpers, alongside hardware-snapshot context, candidate
readiness, and artifact counts. Read-only, no network, no private data. Smoke:
`python3 scripts/model_dashboard_smoke.py`.

---

## L4.5 — Installed-models delete action (gated, recoverable)

**Objective.** Add a per-row **Remove** action to the Installed Models
(inventory) tab so a model can be removed from the system from the dashboard —
safely. This crosses the dashboard from read-only into a mutating action, so it
is **off by default, gated, two-step-confirmed, recoverable, and ADR-backed.**
Build this **before L5** so the modularization sweeps up the new code.

**Files.**
- Edit: `apps/model-dashboard/model_dashboard/server.py` — inventory row delete
  control (mirror `_run_test_control`, server.py:725), a confirm page, and a new
  `/actions/delete-model` POST branch in `do_POST` (mirror the existing
  `/actions/run-test` / `/actions/import-artifact` gating).
- Edit: `apps/model-dashboard/run_dashboard.py` + `serve`/`make_handler` — add an
  `--enable-delete-actions` flag (default **off**), plumbed like
  `enable_run_tests` / `enable_import_actions`.
- New helper (optional): `apps/model-dashboard/model_dashboard/removal.py` — the
  Trash / `ollama rm` logic, isolated and testable.
- Update: `apps/model-dashboard/tests/test_model_dashboard.py`,
  `apps/model-dashboard/tests/test_http_server.py`.
- New ADR: `docs/adr/` — "Dashboard model removal is a gated, recoverable
  mutating action" (records why the read-only rule is being relaxed and the
  safeguards).

**Companion scanner fix (fold in — supersedes the standalone task chip).**
- `_scan_lmstudio_filesystem_models` (server.py:943) currently lists **any**
  folder as a `filesystem_only` model, so empty leftovers (only `.DS_Store`)
  appear as deletable models. Require at least one real weight file
  (`.gguf`/`.safetensors`/`.bin`; also consider `.mlx`/`.npz` and sharded
  `*-0000n-of-*.gguf`) before listing a folder. Folders with only metadata are
  skipped. Add a fixture test (one real-weight dir + one `.DS_Store`-only dir →
  only the real one is returned).

**Behavior & safety (mandatory).**
- **Off by default.** Only active with `--enable-delete-actions`; reuse the
  loopback-only + action-token gate already enforced in `do_POST`.
- **Two-step confirm.** First action renders a confirmation page showing the
  exact resolved path, size, runtime, and what will happen (Trash vs `ollama rm`);
  only the confirm POST (with token) performs removal. No one-click delete.
- **Deletion semantics.**
  - LM Studio (filesystem) models → **move the folder to macOS Trash**
    (recoverable) via `osascript` Finder (`tell application "Finder" to delete
    POSIX file "…"`). stdlib `subprocess`, no new dependency. macOS-guard it; on
    non-macOS refuse with a clear message (Finder Trash is macOS-only).
  - Ollama models → shell to **`ollama rm <model_id>`** (cleans the index and
    shared blob store correctly). Do not hand-delete Ollama blob folders.
- **Path containment.** Derive the target path **server-side** from the inventory
  entry (keyed by a safe identifier) — never accept a client-supplied absolute
  path. Resolve it and assert it is under `LMSTUDIO_MODELS_ROOT` or
  `OLLAMA_MODELS_ROOT`; refuse anything outside (reuse the existing
  `relative_to` / `_safe_*` traversal-guard pattern). Never `rm -rf`.
- **Refresh after.** Re-run the inventory scan so the removed row disappears.

**Tests (no real deletion in tests — all fakes).**
- Disabled by default → `/actions/delete-model` returns 403, no subprocess.
- Enabled + valid token: LM Studio target → asserts the Trash/`osascript` path is
  invoked (fake subprocess), **not** `rm`; Ollama target → asserts
  `ollama rm <id>` invoked.
- Path-containment: a target resolving outside the model roots is refused with no
  subprocess call.
- Two-step confirm: the initial request renders the confirm page and deletes
  nothing; only the confirm POST acts.
- Scanner skips `.DS_Store`-only folders.

**Loop-specific smoke.**
```bash
python3 scripts/model_dashboard_smoke.py
```

**Definition of Done.** Inventory rows offer a gated, two-step **Remove** that
Trashes LM Studio folders (recoverable) and runs `ollama rm` for Ollama models;
off by default; path-validated; empty folders no longer listed; ADR committed;
all tests pass with fakes (no real deletion); gate green.

---

## L5 — `server.py` modularization (maintainability)

**Objective.** Split the 3,854-line `server.py` into a cohesive package so future
dashboard changes are safe. **Behavior-preserving** — a pure move/refactor.

**Approach (suggested package layout).**
- `apps/model-dashboard/model_dashboard/dashboard/layout.py` — `_layout` + the
  `<style>` block + nav.
- `.../components.py` — `_table`, `_stat_card`, `_pill`, `_status_pill`, chart
  glue.
- `.../filters.py` — the `_*_filters` / `_matches_*` / `_filter_*` family.
- `.../pages/` — one module per page (`overview`, `runs`, `compare`, `inventory`,
  `radar`, `specialty`, `projects`, `storage`, `reports`, `lab`, `artifact`,
  `model_detail`).
- `server.py` keeps routing + `make_handler` + `serve`.

**Rules.** No behavior change. Move functions, fix imports, keep public names. All
~61 dashboard tests must pass **unchanged** (do not edit tests except import
paths if strictly necessary). May be split into sub-commits per page group; keep
each green. If risk feels high, land it incrementally.

**Extra scrutiny requested.**
- Treat L5 as a pure move/refactor. No copy changes, CSS redesign, route changes,
  schema changes, import/export changes, inventory behavior changes, or feature
  additions belong in this loop.
- Preserve route outputs and helper semantics. If a helper moves, either keep a
  compatibility import or update only the minimal import path required by the
  moved code.
- Dashboard tests should remain unchanged unless an import path absolutely must
  change. Any assertion rewrite is a signal the refactor is no longer
  behavior-preserving.
- Land page groups incrementally if needed. After each page group, run the
  dashboard unit tests and smoke before continuing.
- Review diffs with moved-code awareness (`git diff --color-moved` or equivalent)
  and call out any non-move edits explicitly in the loop report.
- If the refactor becomes too broad, stop after the last green page group and
  report the exact remaining functions/pages instead of forcing a large risky
  commit.

**Definition of Done.** `server.py` reduced to routing/handler; dashboard renders
identically; all dashboard tests pass unchanged; gate green. (If this proves too
large for one loop, land what's safe and report the remainder.)

---

## L6 — Portfolio evidence pack

Build as specified in
[Sprint 3, Loop 4](2026-06-17-refinement-sprint-3.md#loop-4--portfolio-evidence-pack):
update `docs/portfolio-case-study.md`, `docs/resume-bullets.md`, a
`docs/lab-notes/2026-06-17-capability-sprint-complete.md`, and `ROADMAP.md`.
**Truthful + locally verifiable only** — reflect the real executed-benchmark
capability L3 added, the dashboard data, CI gate, security posture, and
`ai-lab` surface.

---

## Sequence & rationale

1. **L0** — clear friction/drift first (cheap, unblocks L3 smoke).
2. **L1 → L2** — build the CLI capability surface and planning layer.
3. **L3** ⭐ — the keystone: real, sanctioned end-to-end benchmarking.
4. **L4** — surface the real data L3 produces.
5. **L4.5** — gated, recoverable model removal from the inventory tab (build
   before L5 so the modularization includes it).
6. **L5** — maintainability (may become its own sprint if large).
7. **L6** — capture evidence of genuinely completed capability.

Completion: all loops committed, full gate green after the final loop, no
unapproved model calls, no new runtime deps, `ai-lab` can snapshot hardware, plan
a matrix, and **execute an approved benchmark** that lands in the dashboard.
