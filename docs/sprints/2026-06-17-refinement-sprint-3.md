# AI Lab OS Refinement Sprint 3 — 2026-06-17

Purpose: turn AI Lab OS into a repeatable local capability engine for hardware
optimization, model upgrade decisions, skill growth, and portfolio evidence.

Sprint 3 builds on the completed Sprint 2 base:

- CI gates dashboard tests, eval harness tests, dashboard smoke, and ruff.
- `ai-lab` is the unified local operating CLI.
- The dashboard/radar/benchmark lanes are local-first and dependency-light.
- Security/privacy hardening is in place: no raw chunk dumps by default,
  loopback-only local service boundaries, and no hidden cloud/model calls.

## Hard Constraints

- No new runtime dependencies.
- Do not download, run, or call any model unless a loop explicitly asks for a
  local benchmark execution step and the user approves the exact local model id,
  runtime, and run id.
- Do not call cloud APIs, add cloud clients, add secrets, or add telemetry.
- Do not turn source claims or hardware guesses into eval scores.
- Dashboard render paths must make no external network calls.
- Keep changes narrow and package-scoped.
- No architecture-direction change without an ADR in `docs/adr/`.
- Runtime artifacts under `data/` stay local state unless explicitly safe to
  commit.

## Loop Protocol

Run exactly one loop at a time.

For each loop:

1. Re-read `AGENTS.md` and this sprint doc.
2. Inspect `git status -sb` before editing.
3. Implement only the files listed for that loop.
4. Add or update the tests listed for that loop.
5. Run the full validation gate:

   ```bash
   python3 -m unittest discover -s apps/model-dashboard/tests
   python3 -m unittest discover -s evals/local-llm-benchmark/tests
   python3 scripts/model_dashboard_smoke.py
   uv run pytest -q
   uv run ruff check .
   ```

6. Run any loop-specific smoke command listed in the loop.
7. Update docs/lab notes/ADR only where the loop specifies.
8. Commit a self-contained change, then stop and report before starting the next
   loop.

Commit format:

```text
<scope>: <summary>

<what changed, why, how validated, what was NOT tested>

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

Allowed scopes this sprint: `cli`, `bench`, `dashboard`, `docs`.

Report after each loop:

- files changed;
- tests added/updated;
- validation pass/fail lines;
- safety posture;
- deviations from plan;
- next recommended loop.

## Loop 1 — Hardware Profile Snapshot

**Objective.** Add a local, read-only hardware profile snapshot command so the
lab can track what machine/runtime context each benchmark is meant to represent.

**Files.**

- New: `src/local_ai_lab/cli/hardware.py`
- Edit: `src/local_ai_lab/cli/lab.py`
- New/update: `tests/test_lab_cli.py` or `tests/test_hardware_profile.py`
- Docs: `README.md`, `docs/lab-notes/`

**Behavior.**

- Add `ai-lab hardware snapshot`.
- Output stable JSON to stdout by default.
- Optional `--out <path>` writes JSON to a repo-local path.
- Capture only non-secret system facts available through stdlib/platform and
  safe local commands when present:
  - OS/platform;
  - Python version;
  - machine/processor;
  - CPU count;
  - optional macOS `sysctl` values for chip brand and memory size;
  - optional presence/version strings for `ollama`, `lms`, `mlx_lm`, and
    `llama-cli` without starting servers or models.
- Do not include username, home directory, private paths, environment variables,
  tokens, prompts, documents, or model inventory.

**Tests.**

- Fake command runners for `sysctl`/runtime version checks.
- Assert no private path or environment dump appears.
- Assert `--out` writes valid JSON.
- Assert command works when optional runtime commands are missing.

**Loop-specific smoke.**

```bash
uv run ai-lab hardware snapshot
```

**Definition of Done.** Hardware snapshot works offline, is tested with fakes,
does not call models, and produces no private-path leakage.

## Loop 2 — Benchmark Matrix Plan

**Objective.** Add a benchmark planning command that creates an auditable local
matrix of candidate/runtime/profile combinations without running models.

**Files.**

- New: `src/local_ai_lab/cli/bench_matrix.py`
- Edit: `src/local_ai_lab/cli/lab.py`
- New/update: `tests/test_lab_cli.py` or `tests/test_bench_matrix.py`
- Docs: `README.md`, `docs/lab-notes/`

**Behavior.**

- Add `ai-lab bench matrix`.
- Read `data/model_registry/candidates.csv`.
- Include only `ready_for_eval` candidates by default.
- Optional filters: `--status`, `--runner`, `--limit`.
- Output Markdown by default; optional `--json`.
- Include candidate id, model name, runner, local model id, benchmark run id
  proposal, security state, and required preflight notes.
- Mark rows as `blocked` if exact local runtime id is missing or download
  approval/security review is not acceptable.
- Do not initialize runs, call endpoints, inspect private model folders, or run
  benchmark prompts.

**Tests.**

- Fixture registry with ready/watchlist/blocked cases.
- Assert blocked reasons are explicit.
- Assert JSON and Markdown modes are deterministic.
- Assert no subprocess/model command is invoked.

**Loop-specific smoke.**

```bash
uv run ai-lab bench matrix --limit 5
```

**Definition of Done.** The lab can produce a local benchmark queue/matrix from
candidate records without running models or inventing scores.

## Loop 3 — Dashboard Capability View

**Objective.** Surface hardware/profile and benchmark-plan context in the
dashboard without adding runtime dependencies or render-time network calls.

**Files.**

- Edit: `apps/model-dashboard/model_dashboard/server.py`
- Optional new helper: `apps/model-dashboard/model_dashboard/capability.py`
- Update: `apps/model-dashboard/tests/test_model_dashboard.py`
- Docs: `apps/model-dashboard/README.md`, `docs/lab-notes/`

**Behavior.**

- Add a local capability section/page reachable from the lab dashboard.
- Show:
  - latest committed hardware-profile examples if present;
  - candidate readiness counts;
  - benchmark artifact counts;
  - next benchmark matrix guidance.
- Keep it read-only. No refresh button that runs model/runtime commands.
- Do not display private paths, raw prompts, raw responses, or secrets.

**Tests.**

- Page renders with empty/missing optional hardware profile data.
- Page renders candidate/artifact counts from temp fixtures.
- Static assertions for no external `http(s)` assets.

**Loop-specific smoke.**

```bash
python3 scripts/model_dashboard_smoke.py
```

**Definition of Done.** Dashboard exposes capability/readiness context using
local files only, with no network calls and no private data leakage.

## Loop 4 — Portfolio Evidence Pack

**Objective.** Convert Sprint 1-3 work into concise hireability evidence:
architecture, validation, local-first posture, and next benchmark targets.

**Files.**

- New/update: `docs/portfolio-case-study.md`
- New/update: `docs/resume-bullets.md`
- New: `docs/lab-notes/2026-06-17-sprint-3-complete.md`
- Update: `ROADMAP.md`

**Behavior.**

- Summarize the local-first AI Lab OS capability loop.
- Include validation evidence, CI gate, dashboard, benchmark harness, radar,
  security posture, and `ai-lab` CLI.
- Add resume bullets that are truthful, specific, and locally verifiable.
- Add next skill plan: hardware profiling, local eval design, RAG quality, model
  runtime comparison, and portfolio publishing.

**Tests.**

- No code tests required unless code changes are made in this loop.
- Still run the full validation gate.

**Definition of Done.** The repo has updated portfolio/resume evidence that a
human reviewer can verify from committed files and passing validation.

## Completion Criteria

Sprint 3 is complete when:

- all four loops are committed;
- full validation gate is green after the final loop;
- no model was downloaded/run/called without explicit user approval;
- no new runtime dependencies were added;
- `ai-lab` can report status, hardware snapshot, and benchmark matrix locally;
- dashboard capability context is visible and offline;
- portfolio evidence reflects the completed work truthfully.
