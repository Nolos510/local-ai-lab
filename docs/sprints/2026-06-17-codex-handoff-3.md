# Codex Handoff Prompt — AI Lab OS Refinement Sprint 3 (2026-06-17)

Paste the fenced block into Codex as the task prompt. It is self-contained.

---

```text
You are the main builder for Sprint 3 of AI Lab OS in the local-ai-lab repo, a
local-first Apple Silicon AI engineering lab.

START HERE:
1. Read AGENTS.md in full. Its local-first rules, dependency-review gate, and
   Definition of Done are binding.
2. Read docs/sprints/2026-06-17-refinement-sprint-3.md. Execute the loops in
   order.

GOAL:
Turn AI Lab OS into a repeatable local capability engine for hardware
optimization, model upgrade decisions, skill growth, and portfolio evidence.

HARD CONSTRAINTS:
- No new runtime dependencies.
- Do not download, run, or call any model unless a loop explicitly asks for it
  and the user approves the exact local model id, runtime, and run id.
- Do not call cloud APIs, add cloud clients, add secrets, or add telemetry.
- Do not turn source claims or hardware guesses into eval scores.
- Dashboard render paths must make no external network calls.
- Keep changes narrow and package-scoped.
- No architecture-direction change without an ADR in docs/adr/.
- Runtime artifacts under data/ stay local state unless explicitly safe to
  commit.

LOOP PROTOCOL:
For each loop:
1. Inspect git status.
2. Implement only the files listed for that loop.
3. Add/update the tests listed for that loop.
4. Run the full gate:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
5. Run the loop-specific smoke command.
6. Commit with:
     <scope>: <summary>

     <what changed, why, how validated, what was NOT tested>

     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
7. STOP and report files changed, tests, validation lines, safety posture, and
   next loop.

LOOPS:
1. cli: Hardware Profile Snapshot
   Add `ai-lab hardware snapshot` as a local, read-only, privacy-safe hardware
   profile command.
2. bench: Benchmark Matrix Plan
   Add `ai-lab bench matrix` to create a deterministic candidate/runtime plan
   without running models.
3. dashboard: Capability View
   Add read-only dashboard capability/readiness context with no network calls.
4. docs: Portfolio Evidence Pack
   Update portfolio/resume/lab-note/roadmap evidence for Sprint 1-3.

If a validation command genuinely cannot run, document the exact reason. Never
claim a command passed unless it was run. Begin with Loop 1.
```

---

## Notes for the human

- Sprint 3 does **not** start with model execution. It starts by measuring and
  planning safely.
- The first real model benchmark should only happen after a benchmark matrix row
  has exact runtime id, security approval, and user approval.
- Good Sprint 3 output should help with both local capability and resume-proof:
  commands, tests, docs, validation evidence, and clear local-first decisions.
