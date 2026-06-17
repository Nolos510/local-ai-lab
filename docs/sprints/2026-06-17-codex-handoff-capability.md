# Codex Handoff — AI Lab OS Capability Sprint (2026-06-17)

Paste the fenced block into Codex. Self-contained.

---

```text
You are the main builder for the Capability Sprint in the AI Lab OS repo
(local-ai-lab), a local-first Apple Silicon AI engineering lab. Goal: take it
from impressive scaffold to genuinely useful by closing the benchmark execution
loop, clearing onboarding friction, giving the dashboard real data, and hardening
maintainability.

START HERE:
1. Read AGENTS.md in full — local-first rules, dependency gate, Definition of
   Done are binding.
2. Read docs/sprints/2026-06-17-capability-sprint.md — the plan. It SUPERSEDES
   the earlier docs/sprints/2026-06-17-refinement-sprint-3.md but reuses that
   doc's specs for L1/L2/L4/L6 (it links to the exact sections). Execute loops
   L0 → L6 IN ORDER.

CURRENT STATE:
- Sprints 1–2 shipped (charts, offline icons, security/privacy hardening, CI
  gate, ai-lab CLI).
- Capability sprint L0, L1, and L2 are complete.
- The baseline read-only dashboard `/capability` view is complete.
- The current-state portfolio evidence pack is complete.
- The next canonical implementation loop is L3: approval-gated benchmark
  execution machinery with fake-runner tests. Do not skip it.
- Gate is green locally; CI passes on GitHub.

HARD CONSTRAINTS:
- No new runtime dependencies. Dashboard + harness stay stdlib-only.
- No external/network calls from the dashboard at render time.
- MODEL EXECUTION IS ALLOWED ONLY IN L3, and only behind explicit per-run
  approval of exact model id + runtime + run id. No other loop calls a model.
  Never add cloud APIs, secrets, or telemetry.
- Narrow, package-scoped changes. Preserve all passing tests.
- No architecture-direction change without an ADR in docs/adr/.

LOOP PROTOCOL (per loop):
1. Re-read AGENTS.md + the sprint doc. Inspect `git status -sb`.
2. Implement only the files the loop lists; add/extend the listed tests.
3. Run the FULL validation gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
4. Run the loop-specific smoke command if one is listed.
5. Update docs/lab-notes/ADR only where the loop specifies.
6. Commit a self-contained change (format below), then STOP and report: files
   changed, tests added, gate pass/fail lines, smoke result, deviations, and the
   next recommended loop.
   Commit format:
     <scope>: <summary>

     <what changed, why, how validated, what was NOT tested>

     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
   Scopes: cli, bench, dashboard, docs, ci.

THE LOOPS (full detail in the sprint doc):
L0 docs/cli: COMPLETE. (a) Fix default-model onboarding in src/local_ai_lab/cli/doctor.py
   so a missing configured model yields actionable guidance (name an installed
   model + the exact LOCAL_AI_LAB_OLLAMA_MODEL to set), not a bare FAIL; update
   .env.example + README. (b) Reconcile the THREE architecture docs
   (ARCHITECTURE.md, docs/architecture.md, docs/architecture-v1.md) into one
   canonical doc; others become pointers. Test the doctor suggestion path.
L1 cli: COMPLETE. ai-lab hardware snapshot (per Sprint 3 Loop 1) — JSON, --out, NO private
   paths/usernames/env/secrets, no model calls. Smoke: ai-lab hardware snapshot.
L2 cli/bench: COMPLETE. ai-lab bench matrix (per Sprint 3 Loop 2) — reads candidates.csv,
   Markdown default + --json, marks blocked rows, runs NO models. Smoke:
   ai-lab bench matrix --limit 5.
L3 bench/cli ⭐ NEXT. CLOSE THE BENCHMARK EXECUTION LOOP (the keystone, approval-gated):
   - BUILD THIS AUTONOMOUSLY — DO NOT SKIP IT. The command, approval gate, schema
     migration, perf wiring, and ALL tests are built and verified with FAKES (fake
     endpoint/subprocess) and need NO real model call to land. The gate ensures
     nothing runs without explicit flags. Committing L3 = the machinery is in
     place, gated, and green. The actual run against a live model is a separate
     user-approved step done later, NOT a prerequisite for this commit.
   - Add ai-lab bench execute (or bench run --execute) that runs a prepared
     artifact against a local runtime via the harness (run_local /
     run_lmstudio_cli), captures perf metrics, optional draft scores, and imports
     into the dashboard.
   - APPROVAL GATE: require explicit --model-id, --runner, --run-id and an
     explicit confirmation (--i-approve-local-run or interactive yes). Print
     exactly what will run before calling; with approval absent, NO model call
     may happen (assert in tests).
   - Perf: add nullable ttft_seconds + total_latency_seconds to model_runs via an
     additive idempotent migration mirroring db._ensure_eval_score_status; reuse
     tokens_per_sec/ram_usage_gb. Capture total latency + tokens/sec; leave TTFT
     null unless streaming is wired; do NOT fabricate. Carry columns through
     csv_io import.
   - Draft scores (if included) write score_status='draft' and NEVER overwrite
     confirmed scores.
   - Add an ADR for sanctioned local benchmark execution.
   - EXTRA SCRUTINY: treat the approval gate as a safety boundary. Check exact
     --model-id, --runner, --run-id, and approval before constructing or calling
     any subprocess, HTTP request, harness execution, dashboard import, or score
     export. Tests must prove fake runners/endpoints are not called when approval
     is missing. Do not infer runnable identity from registry rows alone. No
     cloud APIs, secrets, telemetry, downloads, or external network calls.
L4 dashboard: BASELINE COMPLETE; PERF-SERIES FOLLOW-UP AFTER L3. Capability view
   (per Sprint 3 Loop 3) PLUS surface the real perf series L3 produces via
   charts.py (tokens/sec, latency) + hardware context + readiness/artifact
   counts. Read-only, no network, no private data. Smoke:
   model_dashboard_smoke.py. The current /capability page already shows hardware
   profile examples, readiness, artifact counts, dashboard run/score signals, and
   benchmark matrix guidance; add latency/TTFT surfaces only after L3 creates the
   data.
L4.5 dashboard: GATED, RECOVERABLE model-removal action in the Installed Models
   tab (build BEFORE L5 so the refactor includes it). Add a per-row Remove that:
   - is OFF by default behind --enable-delete-actions (reuse the loopback +
     action-token gate like enable_run_tests/enable_import_actions);
   - uses TWO-STEP confirm (a confirm page showing exact path + size + action;
     only the confirm POST deletes — no one-click delete);
   - LM Studio files -> MOVE TO macOS TRASH (recoverable) via osascript Finder
     (stdlib subprocess, no new dep; macOS-guarded); Ollama models -> `ollama rm
     <id>` (cleans index + shared blobs). Never rm -rf, never delete Ollama blob
     folders by hand.
   - PATH CONTAINMENT: derive the path server-side from the inventory entry (never
     a client-supplied absolute path); resolve and assert it is under
     LMSTUDIO_MODELS_ROOT or OLLAMA_MODELS_ROOT; refuse anything outside.
   - FOLD IN the scanner fix: _scan_lmstudio_filesystem_models must require a real
     weight file (.gguf/.safetensors/.bin/...) before listing a folder, so empty
     .DS_Store-only folders stop appearing.
   - Add an ADR (dashboard becomes a gated mutating surface). Tests use fakes (no
     real deletion): disabled->403; LM Studio->Trash path invoked not rm;
     Ollama->`ollama rm` invoked; out-of-root target refused; two-step confirm
     deletes nothing on the first request; scanner skips .DS_Store-only dirs.
   Smoke: model_dashboard_smoke.py.
L5 dashboard: Modularize the 3,854-line server.py into a package (layout.py,
   components.py, filters.py, pages/<page>.py); server.py keeps routing +
   make_handler + serve. BEHAVIOR-PRESERVING — all ~61 dashboard tests must pass
   UNCHANGED (edit only import paths if strictly necessary). May land
   incrementally per page group; keep each commit green. Report remainder if too
   large for one loop.
   - EXTRA SCRUTINY: pure move/refactor only. No copy/CSS/route/schema/import
     behavior changes, no feature additions, and no assertion rewrites except
     unavoidable import-path fixes. Use moved-code diff review and call out every
     non-move edit. If risk grows, stop after the last green page group.
L6 docs: CURRENT-STATE PACK COMPLETE; REFRESH AFTER L3. Portfolio evidence pack
   (per Sprint 3 Loop 4) — truthful + locally verifiable; after L3 lands,
   refresh it to reflect the real executed-benchmark capability.

If a validation command cannot run in your environment, document the exact reason
— never claim a command passed unless it was run. Begin with L0.
```

---

## Notes for the human

- A Claude Code `/loop` integrator runs on each commit: full gate + loop-specific
  smoke, checks the sprint Definition-of-Done, and flags regressions, new deps,
  new network calls, **any unapproved model call**, private-path/secret leakage,
  deleted artifacts, or missing ADRs.
- **L3 is the one that may touch a real model, but the implementation commit must
  be built and verified with fakes first.** Live execution is a separate
  user-approved step after the approval gate is implemented. When a live run is
  requested, approve the exact model id / runtime / run id.
- **L5 is the riskiest** (big refactor). If it gets shaky, have Codex land it
  page-group by page-group rather than all at once.
```
