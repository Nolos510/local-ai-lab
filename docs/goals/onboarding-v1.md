# Goal — Onboarding + v1 release

- **Branch:** `codex/onboarding-v1`
- **Area:** `docs/`, `README.md`, `.github/`, `scripts/`, the `[project]` version in `pyproject.toml`
- **Reserved ADR:** 0011 (only if needed)

```text
GOAL: Make local-ai-lab genuinely usable by a new person end-to-end, then prepare a
v1 release with validation evidence.

BRANCH: codex/onboarding-v1. AREA: docs/, README.md, .github/, scripts/, and the
[project] version in pyproject.toml (edit ONLY the version line). Reserve ADR 0011
(only if needed). Do NOT change app/runtime logic.

START HERE: Read AGENTS.md, README.md, ROADMAP.md (the v1 "Local AI Lab Product
Loop" items), and the existing docs/.

LOOPS:
O1: Verify the quickstart ACTUALLY works and fix the docs where it doesn't:
    - RAG path: uv sync; docker compose config; doctor; ingest sample docs;
      LOCAL_AI_LAB_LLM_PROVIDER=mock ask. Document exact working commands.
    - Lab loop: radar list -> bench matrix -> (prepared) bench -> import -> dashboard.
    Run every command you document; never claim one passed unless it ran. Record
    which steps need a live model/Qdrant vs. which run offline.
O2: Write a clean GETTING_STARTED.md (or restructure README) with a 5-minute
    offline path and the full local path, plus the dashboard operating surface
    (which --enable-* flag does what, safety posture).
O3: Prepare the v1 release: bump [project] version; write CHANGELOG.md / release
    notes summarizing what shipped (dashboard, ai-lab CLI, approval-gated benchmark
    execution, security/privacy posture) with VALIDATION EVIDENCE (paste the gate
    output). Confirm CI is green.

CONSTRAINTS:
- Truthful + locally verifiable only. Do not imply live perf data or an executed
  benchmark exists if none has been run.
- Run the FULL gate every commit (the repo's 5 validation commands). Commit scope:
  docs.
- DO NOT git push or create/push a remote tag. Prepare an annotated tag locally
  and STOP for my approval before any push.

Per loop: implement, run the gate, commit, STOP and report. Begin with O1.
```
