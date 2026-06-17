# Dashboard Capability View

Status: active

The dashboard has a local `/capability` page for sprint planning and benchmark
readiness review.

## What It Shows

- Latest committed hardware profile JSON examples from `docs/lab-notes`, when
  present.
- Candidate readiness counts from `data/model_registry/candidates.csv`.
- Ready candidate preflight state, including missing runtime ids and approval
  gate blockers.
- Benchmark artifact counts from `data/eval_results`.
- Dashboard run and score counts from the selected local SQLite database.
- The next read-only benchmark matrix command:

```bash
uv run ai-lab bench matrix --limit 5
```

## Safety Boundary

The page reads only repo-local CSV, JSON, SQLite, and artifact metadata. It does
not refresh inventory, call runtime CLIs, start model servers, inspect private
model folders, run prompts, download models, or display raw responses.

Hardware profile examples are optional. If no committed profile JSON exists, the
page shows the safe command for creating one:

```bash
uv run ai-lab hardware snapshot --out docs/lab-notes/hardware-snapshot-local.json
```

## Validation

Loop smoke:

```bash
python3 scripts/model_dashboard_smoke.py
```
