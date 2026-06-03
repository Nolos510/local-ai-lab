# Task 002: Local Benchmark Harness Skeleton

## Goal

Build the first local, dependency-light benchmark harness skeleton that turns the
v0.1 benchmark contract into reproducible local artifacts and
dashboard-compatible CSV summaries.

## Acceptance Criteria

- Uses `evals/local-llm-benchmark/SPEC.md` as the source prompt/rubric contract.
- Requires no cloud APIs, secrets, model downloads, or model execution in fixture
  mode.
- Preserves raw response artifacts locally before scoring summaries.
- Produces dashboard-compatible `models.csv`, `model_runs.csv`,
  `eval_scores.csv`, and `decisions.csv`.
- Includes deterministic fixture output for validation.
- Includes validation for raw artifacts and dashboard CSV import.
- Keeps runtime dependencies empty unless a dependency passes the review gate in
  `AGENTS.md`.

## Expected Validation

```bash
python3 scripts/model_dashboard_smoke.py
```

Harness-specific validation commands should be added by Harness Builder and kept
aligned with `docs/lab-notes/v0.3-validation-checklist.md`.

## Status

Opened on 2026-06-03 after the v0.2 dashboard workflow and benchmark prep
checkpoint.
