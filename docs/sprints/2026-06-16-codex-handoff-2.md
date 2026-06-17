# Codex Handoff Prompt — AI Lab OS Refinement Sprint 2 (2026-06-16)

Paste the fenced block into Codex as the task prompt. Self-contained.

---

```text
You are the main builder for Sprint 2 of a refinement effort in the AI Lab OS
repo (local-ai-lab), a local-first Apple Silicon AI engineering lab.

START HERE:
1. Read AGENTS.md in full — local-first rules, dependency-review gate, and
   Definition of Done are binding.
2. Read docs/sprints/2026-06-16-refinement-sprint-2.md — the Sprint 2 plan, with
   exact files, the issue list, and acceptance criteria. Execute its iterations
   IN ORDER.

CURRENT STATE (important):
- Sprint 1 shipped inline SVG charts (commit 3d171c4) and offline icons (538adf5).
- The security/privacy hardening pass shipped in commit 33d3554.
- A follow-up documentation pass should keep the ADR/API docs and sprint notes
  aligned with that shipped hardening work before continuing to CI/CLI/hygiene.

HARD CONSTRAINTS:
- No new runtime dependencies. Dashboard + harness stay stdlib-only.
- No external/network calls from the dashboard at render time.
- Narrow, package-scoped changes. Preserve all passing tests.
- No model downloads/runs/calls. No architecture change without an ADR in
  docs/adr/.

LOOP PROTOCOL (per iteration):
1. Implement only what the iteration specifies.
2. Add/extend tests as specified.
3. Run the FULL validation gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
4. Update docs/roadmap/ADR as the iteration specifies.
5. Commit (format below), then STOP and report: files changed, tests added,
   gate pass/fail lines, and any deviation.
   Commit format:
     <scope>: <summary>

     <what changed, why, how validated, what was NOT tested>

     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
   Scopes: security, privacy, ci, cli, docs.

THE FOUR ITERATIONS (full detail in the sprint-2 doc):
1. security/privacy: SHIPPED.
   - Commit 33d3554 landed the hardening pass.
   - Follow-up docs should keep the `/ask` privacy ADR, README/API docs, and
     sprint notes current.
2. ci: Add dashboard-tests, eval-harness-tests, and dashboard-smoke steps to
   .github/workflows/ci.yml (existence-guarded like current steps). Ensure ruff
   lints the whole repo. No --probe-server. This gate would have caught the
   Iteration 1 lint error — make it real.
3. cli: Build the `ai-lab` console script per Sprint 1 Iteration 4
   (src/local_ai_lab/cli/lab.py; register in pyproject [project.scripts];
   subcommands status/radar list/bench run/import/report/dashboard; subprocess
   for actions, stdlib reads for status; tests/test_lab_cli.py; ADR for the new
   operating surface).
4. docs: Repo hygiene — reconcile ROADMAP.md vs docs/roadmap.md into ONE
   canonical roadmap; `git add docs/sprints/`; keep the Discord learning
   assistant proposal under docs/ideas/. Leave no stray untracked docs at docs/
   root.

If a validation command cannot run in your environment, document the exact
reason — never claim a command passed unless it was run. Begin with the first
remaining unshipped iteration.
```

---

## Notes for the human

- A Claude Code `/loop` integrator is running again: on each Codex commit it
  re-runs the full gate, checks Definition-of-Done in the sprint-2 doc, and flags
  regressions / new deps / new network calls / local-first violations.
- Iteration 1 is now shipped; the next builder should start from CI unless a doc
  freshness issue is found.
- The breaking `/ask` change has a durable ADR/docs requirement; keep downstream
  consumers from relying on `retrieved_chunks`, `source_path`, or `preview`.
