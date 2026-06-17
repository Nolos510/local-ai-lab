# Sprint 3 Portfolio Evidence Pack

Date: 2026-06-17
Status: complete for the portfolio evidence loop

## Summary

This pass converted the current AI Lab OS work into portfolio-ready evidence:

- Updated `docs/portfolio-case-study.md`.
- Updated `docs/resume-bullets.md`.
- Updated `ROADMAP.md`.
- Recorded this completion note.

The docs now reflect the current committed product loop without claiming
unfinished benchmark-execution automation.

## Verifiable Capabilities

- Local-first dashboard with lab, capability, radar, specialty, project,
  inventory, runs, compare, reports, artifacts, and storage views.
- Unified `ai-lab` CLI for local status, radar listing, hardware snapshot,
  benchmark matrix planning, benchmark artifact prep, dashboard import/report,
  and dashboard launch.
- Confirmed Qwen local benchmark artifacts under `data/eval_results`.
- Read-only capability dashboard page for hardware profile examples, candidate
  readiness, artifact counts, and next benchmark matrix guidance.
- Security posture separating candidate claims, installed inventory, benchmark
  evidence, confirmed scores, and final decisions.

## Validation Evidence

Required gate for this loop:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Expected current results after the L4 documentation pass:

- Dashboard tests: 64 passing.
- Eval harness tests: 8 passing.
- Repo pytest: 134 passing.
- Dashboard smoke: passing.
- Ruff: passing.

## Not Claimed Complete

- A second unique confirmed model benchmark.
- Approval-gated `ai-lab` benchmark execution from the unified CLI.
- First-class latency/TTFT dashboard series.
- Retrieval-quality eval fixtures for the RAG lane.

## Next Recommended Loop

Choose one:

- If continuing the capability sprint, build the approval-gated benchmark
  execution loop with fake-runner tests before any live local model execution.
- If packaging for portfolio, capture screenshots from `/lab`, `/capability`,
  `/radar`, `/projects`, `/inventory`, and `/reports`, then prepare a release
  tag once the v1 definition is explicit.
