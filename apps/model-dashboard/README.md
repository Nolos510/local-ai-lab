# Local Model Performance Dashboard

A dependency-free local dashboard for reviewing model evaluation results in AI Lab OS.

## Requirements

- Python 3.9 or newer
- No Python package install is required
- No API keys, cloud services, model downloads, or network calls are required

## Quick Start

From the repository root:

```bash
python3 apps/model-dashboard/run_dashboard.py init-db --reset --with-fixtures
python3 apps/model-dashboard/run_dashboard.py serve --demo
```

Then open `http://127.0.0.1:8765`.

The default database path is `data/dashboard/model_dashboard.sqlite`. This runtime file is local state and is ignored by git.

If port `8765` is already in use, pass another local port:

```bash
python3 apps/model-dashboard/run_dashboard.py serve --demo --port 8766
```

## Commands

Create or reset the SQLite database:

```bash
python3 apps/model-dashboard/run_dashboard.py init-db --reset
```

Create or reset the database and load the bundled fixture CSV files:

```bash
python3 apps/model-dashboard/run_dashboard.py init-db --reset --with-fixtures
```

Import table-shaped CSV files:

```bash
python3 apps/model-dashboard/run_dashboard.py import-csv \
  --models apps/model-dashboard/fixtures/models.csv \
  --runs apps/model-dashboard/fixtures/model_runs.csv \
  --scores apps/model-dashboard/fixtures/eval_scores.csv \
  --decisions apps/model-dashboard/fixtures/decisions.csv
```

Export dashboard tables to CSV:

```bash
python3 apps/model-dashboard/run_dashboard.py export-csv
```

Generate a Markdown report:

```bash
python3 apps/model-dashboard/run_dashboard.py report
```

Run the local web dashboard:

```bash
python3 apps/model-dashboard/run_dashboard.py serve
```

Use `--demo` with `serve` to load fixtures automatically when the selected database has no model rows.

## Tests

Run the stdlib test suite from the repository root:

```bash
python3 -m unittest discover apps/model-dashboard/tests
```

## CSV Tables

The import/export workflow expects one CSV per table:

- `models.csv`
- `model_runs.csv`
- `eval_scores.csv`
- `decisions.csv`

Headers must match the table fields exported by the app. Blank `total_score` and `final_label` values in `eval_scores.csv` are filled deterministically during import.
