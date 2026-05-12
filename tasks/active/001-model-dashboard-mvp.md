# Task 001: Model Dashboard MVP

## Goal

Build a local model performance dashboard that tracks tested local and open-weight models, run settings, eval scores, stability notes, and keep/delete decisions.

## Acceptance Criteria

- Python stdlib local web dashboard.
- SQLite persistent storage.
- CSV import and export.
- Fixture data works immediately.
- Tracks models, runs, eval scores, and decisions.
- Includes report generation.
- Includes tests for schema creation, CSV import, scoring, and report generation.
- Requires no API keys, cloud services, model downloads, or model execution.

## Validation

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 apps/model-dashboard/run_dashboard.py init-db --reset --with-fixtures
python3 apps/model-dashboard/run_dashboard.py report --out data/dashboard/reports/fixture-model-report.md
python3 apps/model-dashboard/run_dashboard.py serve --demo --host 127.0.0.1 --port 8765
```

## Status

MVP scaffold implemented on 2026-05-12.
