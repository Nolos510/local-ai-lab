# Local Model Performance Dashboard

A dependency-free local dashboard for reviewing model evaluation results in AI Lab OS.

## Requirements

- Python 3.9 or newer
- No runtime package install is required for the dashboard itself
- The repo `dev` extra installs `pytest` for test validation
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

The Lab Dashboard page is available at:

```text
http://127.0.0.1:8765/lab
```

It is the read-only v1 command center for the local product loop. It shows ready
radar candidates, benchmark artifact state, draft/confirmed score counts, import
linkage, decisions, and the next benchmark commands to run locally.

The Overview page supports URL-backed filters for search text, final label, decision, and install status. Filtered views can be bookmarked or shared locally, for example:

```text
http://127.0.0.1:8765/?label=CODING_SPECIALIST&keep=yes
```

The Radar Candidates page is available at:

```text
http://127.0.0.1:8765/radar
```

It reads `data/model_registry/candidates.csv` and displays candidate-only radar
records separately from scored eval results. Candidate rows may link to local
source packets, radar reports, and benchmark artifact directories, but they do
not become dashboard scores or final labels.

Scored eval rows now include `score_status`. Existing and manually confirmed
scores default to `confirmed`; local-judge suggestions may be imported as
`draft`. Draft scores are visible in the overview, run list, compare page, model
detail page, and Markdown report so they are not confused with confirmed
evidence.

## Tests

From the repository root, create or activate the repo venv, install the dev
extra, and run pytest:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Use `python3` before the venv exists, then use `python` after activation. The
test files use `unittest`, and pytest is the configured test runner for the
repo. If pytest is missing, the `dev` extra was not installed in the active
environment.

In sandboxed environments, pip may need network approval to fetch pytest or
build tooling. The dashboard itself still has no runtime package dependencies
and does not make network, cloud, API, or model download calls.

## Smoke Test

Run the dashboard smoke script from the repository root:

```bash
python3 scripts/model_dashboard_smoke.py
```

The smoke script runs the dashboard tests, creates a fixture SQLite database in a system temp directory, and writes a Markdown report next to that temp database.

To include a local server probe, pass:

```bash
python3 scripts/model_dashboard_smoke.py --probe-server
```

The server probe binds to `127.0.0.1` on a temporary free port and requests only local dashboard pages.

## CSV Tables

The import/export workflow expects one CSV per table:

- `models.csv`
- `model_runs.csv`
- `eval_scores.csv`
- `decisions.csv`

Headers must match the table fields exported by the app. Blank `total_score` and
`final_label` values in `eval_scores.csv` are filled deterministically during
import. Older `eval_scores.csv` files without `score_status` import as
`confirmed`.

## Benchmark Import Contract

The initial repeatable local LLM benchmark format lives in `evals/local-llm-benchmark/SPEC.md`.
It defines the prompt set, rubric version, raw evidence expectations, scoring dimensions, and
the normalized CSV fields that map into the dashboard MVP tables.
