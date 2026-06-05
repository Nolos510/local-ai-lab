# v1 Validation Evidence

Date: 2026-06-05

## Branch State

Working branch was switched from `master` to local `main` tracking
`origin/main`. At the start of this pass, `origin/main` and `origin/master`
were both at:

```text
1a3f54e Merge main into master
```

## Candidate Runtime Check

Target requested by the user:

```text
Qwen3-30B-A3B-Instruct
```

Local LM Studio observations:

- `lms ls --json` exposed only the loaded LLM
  `qwen3-coder-30b-a3b-instruct-mlx`.
- `lms ps --json` reported display name `Qwen3 Coder 30B A3B Instruct`.
- The local filesystem contained
  `~/.lmstudio/models/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit`.
- No exact local inventory entry for `Qwen3-30B-A3B-Instruct` was visible
  through the CLI checks.
- `http://127.0.0.1:1234/v1/models` was reachable after local network
  approval, but returned `401 Unauthorized`.

Conclusion: the vanilla Qwen3 30B benchmark was not run in this pass. Creating
a scored artifact would have risked benchmarking the previously tested Coder
model under the wrong name.

## Registry Changes

- Added `20260605-qwen3-30b-a3b-instruct-lmstudio` as a separate vanilla Qwen3
  candidate.
- Moved `20260605-qwen3-30b-a3b-abliterated` to `watchlist` until a matching
  local artifact or endpoint exists.
- Corrected the existing Qwen3 Coder candidate link to the scored `r2`
  benchmark artifact.

## Dashboard Link Evidence

Dashboard loop links were added without schema changes:

- Imported run notes are parsed for `benchmark_run_id=...`.
- `/runs` shows an artifact link for imported runs.
- `/models/<id>` shows artifact links in run history.
- `/artifacts/<run_id>` shows candidate context plus imported model and
  decision state when available.
- `/lab` shows artifact import/decision state in the artifact table.

## Commands To Reproduce Runtime Check

```bash
lms ls --json
lms ps --json
python3 - <<'PY'
from urllib.request import urlopen
print(urlopen("http://127.0.0.1:1234/v1/models", timeout=5).read().decode())
PY
```

The HTTP check may require local network approval and may fail with `401
Unauthorized` until the local LM Studio server auth path is configured for the
benchmark runner.

## Pending Benchmark Command

Run only after the exact model id is visible:

```bash
python3 evals/local-llm-benchmark/harness.py init-run \
  --benchmark-run-id 20260605-qwen3-30b-a3b-instruct-lmstudio-r1 \
  --model-name "Qwen3-30B-A3B-Instruct" \
  --backend "LM Studio" \
  --format "Local OpenAI-compatible" \
  --quantization "not reported" \
  --hardware "Mac Studio Apple M3 Ultra, 32-core CPU, 256 GB RAM, macOS 26.3.1" \
  --temperature 0.2 \
  --top-p 0.9
```

## Validation Results

Dashboard and harness validation passed after the dashboard loop-link changes:

```text
python3 -m unittest discover -s apps/model-dashboard/tests
22 tests passed.

python3 -m unittest discover -s evals/local-llm-benchmark/tests
4 tests passed, 2 skipped.

python3 scripts/model_dashboard_smoke.py
Dashboard smoke passed.

uv run pytest
59 tests passed.

uv run ruff check .
All checks passed.
```

The current complete scored benchmark loop remains the Qwen3 Coder `r2`
artifact. Its dashboard CSVs imported into a temp database:

```text
python3 apps/model-dashboard/run_dashboard.py import-csv \
  --db /private/tmp/qwen-r2-v1-dashboard.sqlite \
  --models data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit-r2/dashboard-import/models.csv \
  --runs data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit-r2/dashboard-import/model_runs.csv \
  --scores data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit-r2/dashboard-import/eval_scores.csv \
  --decisions data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit-r2/dashboard-import/decisions.csv

Imported rows: {'models': 1, 'model_runs': 1, 'eval_scores': 1, 'decisions': 1}
```

The temp report was generated at:

```text
/private/tmp/qwen-r2-v1-dashboard-report.md
```
