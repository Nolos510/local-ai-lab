# AGENTS.md

Guidance for Codex and other automation working in this repository.

## Repo Rules

- Keep the project local-first. Do not add cloud API calls, model download logic, or secrets.
- Prefer small, auditable changes that preserve the current dashboard MVP behavior.
- Keep `apps/model-dashboard` dependency-light. Add runtime dependencies only when the app imports and needs them.
- Treat `data/dashboard/*.sqlite` and export folders as local runtime state.
- Update docs and lab notes when setup, validation, or safety posture changes.

## Validation Commands

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

For dashboard smoke checks:

```bash
python apps/model-dashboard/run_dashboard.py init-db --reset --with-fixtures
python apps/model-dashboard/run_dashboard.py report
python apps/model-dashboard/run_dashboard.py serve --demo
```

Then open `http://127.0.0.1:8765`. Use `--port 8766` if the default port is busy.
