# Model Dashboard MVP QA

Date: 2026-05-12

## What Passed

- Clean setup runs with stdlib Python only:
  - `python3 apps/model-dashboard/run_dashboard.py init-db --reset --with-fixtures`
  - `python3 apps/model-dashboard/run_dashboard.py report --out data/dashboard/reports/fixture-model-report.md`
- Tests pass:
  - `python3 -m unittest discover -s apps/model-dashboard/tests`
  - Result: 10 tests passed.
- Fixture data loads:
  - Imported 4 `models`, 4 `model_runs`, 4 `eval_scores`, and 4 `decisions`.
- SQLite schema works:
  - Tables and indexes are created.
  - App connections enable `PRAGMA foreign_keys = ON`.
  - Tests cover foreign key rejection and invalid `final_label` rejection.
- CSV import/export works:
  - Exported all four tables to CSV.
  - Imported the exported files into a new database with 4 rows per table.
- Local server works:
  - `serve --demo --host 127.0.0.1 --port 8765` loaded successfully.
  - Browser smoke checks passed for `/`, `/reports`, and `/models/3`.
- README instructions include a fallback port note for machines where `8765` is occupied.
- Safety review passed:
  - No API key usage.
  - No OpenAI, Anthropic, or other cloud API calls.
  - No model download logic.
  - No subprocess, shell execution, or remote fetch code.
  - Web server is Python stdlib `http.server` and defaults to `127.0.0.1`.
- Docs were updated:
  - Added `apps/model-dashboard/README.md`.
  - Added this QA report.

## What Was Added

- Added fixture CSV files:
  - `apps/model-dashboard/fixtures/models.csv`
  - `apps/model-dashboard/fixtures/model_runs.csv`
  - `apps/model-dashboard/fixtures/eval_scores.csv`
  - `apps/model-dashboard/fixtures/decisions.csv`
- Expanded fixtures to 4 linked model records, including `Qwen2.5-Coder 14B Instruct`.
- Added focused stdlib unittest coverage for:
  - Fixture import counts and summary ordering.
  - SQLite foreign key and label constraints.
  - CSV export/import round trip.
  - Markdown report generation from fixtures.
- Added `apps/model-dashboard/README.md` with setup, command, test, CSV, and safety notes.
- Updated the README to document `--port` when `8765` is occupied.

## Remaining Issues

- `serve --demo` can fail if port `8765` is already occupied. The documented workaround is `--port 8766` or another free local port.
- There is no single task-runner command for the full QA sequence yet. Commands are documented individually.

## Recommended Next Task

Add a small repo script for the model dashboard QA smoke suite that runs unittest discovery, fixture import, CSV export/import, report generation, and a local server probe on an available port.
