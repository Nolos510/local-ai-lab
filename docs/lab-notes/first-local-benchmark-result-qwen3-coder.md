# First Local Benchmark Result: Qwen3 Coder Attempt

Date: 2026-06-03

Run ID: `20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit`

## Summary

Created the first real local benchmark artifact directory for the installed
local model `Qwen3-Coder-30B-A3B-Instruct-MLX-4bit` through the v0.1 local LLM
benchmark harness.

This run is a failed-runtime benchmark attempt, not a scored model evaluation.
LM Studio did not start or expose the local server during the run, so no prompts
were executed and no model responses were captured.

## Safety And Local-First Review

- No cloud APIs, external network calls, secrets, or model download logic were
  added for this result.
- The attempted model source was a local LM Studio model artifact. Private
  filesystem paths are intentionally omitted from the GitHub copy.
- Raw response artifacts are generated local files under
  `data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/`.
- `raw_responses.jsonl` contains one record per benchmark prompt with the
  runtime error and an empty `raw_response` field.
- Dashboard CSVs contain normalized summaries and local artifact pointers only.

## Evidence Quality

- Evidence file: `evidence.md`.
- Raw response file: `raw_responses.jsonl`, omitted from the GitHub copy and
  regenerated locally during benchmark runs.
- Each prompt record states: `LM Studio daemon failed to start; prompt was not run.`
- No score file was created and `eval_scores.csv` remains header-only because
  there was no model-output evidence to score.
- No final label was assigned because no prompt responses were produced.

## Dashboard Import Review

Validated the dashboard import CSVs:

- `models.csv`: 1 row.
- `model_runs.csv`: 1 row with benchmark ID, prompt set, rubric version, and raw
  artifact path in `run_notes`.
- `eval_scores.csv`: 0 rows, intentionally unscored.
- `decisions.csv`: 1 row.

Temp import validation succeeded:

```bash
python3 apps/model-dashboard/run_dashboard.py import-csv \
  --db /private/tmp/qwen-first-benchmark-import.sqlite \
  --models data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/dashboard-import/models.csv \
  --runs data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/dashboard-import/model_runs.csv \
  --scores data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/dashboard-import/eval_scores.csv \
  --decisions data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/dashboard-import/decisions.csv
```

Result:

- Imported rows: `{'models': 1, 'model_runs': 1, 'eval_scores': 0, 'decisions': 1}`.
- Dashboard report generation from the imported database succeeded.
- CSV headers match `model_dashboard.csv_io.TABLE_FIELDS`.

## Decision

Decision: `retest`

Justification: the backend failed before prompt execution, so model capability,
score, and final label are not established.

Retest condition: rerun after LM Studio daemon/server starts and the installed
local model can answer the full prompt set.
