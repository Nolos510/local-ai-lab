# AGENTS.md

Guidance for Codex and other automation working in this repository.

## Repo Rules

- Keep the project local-first. Do not add cloud API calls, model download logic, or secrets.
- Prefer small, auditable changes that preserve the current dashboard MVP behavior.
- Keep `apps/model-dashboard` dependency-light. Add runtime dependencies only when the app imports and needs them.
- Keep the local LLM benchmark harness stdlib-only unless a dependency clears the review gate below.
- Treat `data/dashboard/*.sqlite` and export folders as local runtime state.
- Update docs and lab notes when setup, validation, or safety posture changes.

## Dependency Review Gate

Before adding any dependency, challenge it:

- Can `argparse`, `csv`, `json`, `sqlite3`, `subprocess`, `pathlib`, `tempfile`, `time`, `unittest`, or another stdlib module cover the need?
- Is the dependency runtime code, or only a developer/test tool? Developer tools belong in the `dev` extra.
- Does the dependency download models, call cloud APIs, require credentials, or pull in heavy transitive packages? Reject it unless the user explicitly approves a scope change.
- Can the harness write JSONL, CSV, Markdown, and dashboard imports without it? For v0.3, assume yes until proven otherwise.
- If Harness Builder proposes a dependency, document the exact missing stdlib capability, expected import location, transitive risk, and removal plan before accepting it.

Do not add vendored packages, ad hoc requirements files, or global install instructions. Keep declared Python dependencies centralized in `pyproject.toml`.

## Validation Commands

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Use `python3` for venv creation and `python` after activation so commands use
the virtualenv interpreter. If `pytest` is missing, install the `dev` extra in
the active venv instead of relying on a global pytest.

Command hygiene:

- Use `python -m pip`, not bare `pip`, after the venv is active.
- Use `python -m pytest -q`, not a global `pytest` executable.
- Use `python3` for direct app scripts only when not relying on an activated venv.
- Keep setup docs aligned with the `python3` -> `.venv` -> `python` flow.

Sandbox note: `pip install --upgrade pip` and `pip install -e ".[dev]"` may need
network approval when dependencies are not cached. Do not work around that by
adding vendored packages or new dependency files; request approval and keep the
declared dependencies in `pyproject.toml`.

For dashboard smoke checks:

```bash
python3 scripts/model_dashboard_smoke.py
```

To include a localhost server bind/probe check:

```bash
python3 scripts/model_dashboard_smoke.py --probe-server
```

The server probe binds to `127.0.0.1` by default and accepts only loopback
hosts. In sandboxed environments, `--probe-server` may need local bind/probe
approval.
