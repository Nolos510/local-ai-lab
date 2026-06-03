# AI Lab OS

AI Lab OS is a local-first workspace for testing open, local, and open-weight AI models on Apple Silicon hardware. It keeps model discovery, evaluations, dashboards, reusable workflows, project notes, and resume evidence in one shared source of truth while the system is still evolving.

The first working application is the Local Model Performance Dashboard in `apps/model-dashboard`.

## Goals

- Track which local models are actually useful, not just which models are currently hyped.
- Record model metadata, backend settings, quantization, speed, memory use, eval scores, stability notes, and keep/delete decisions.
- Keep data local in SQLite and CSV files.
- Build toward radar automation, benchmark harnesses, reusable skills, weekly briefs, QA workflows, local RAG, and portfolio evidence.

## Repository Map

```text
apps/model-dashboard/          Local model performance dashboard MVP
automations/                   Future model radar and weekly brief jobs
evals/local-llm-benchmark/     Personal benchmark suite
skills/                        Reusable AI workflow skills
data/                          Local registry, eval results, dashboard DB, fixtures
tasks/                         PRDs, active work, completed tasks
agents/                        Role prompts and review checklists
scripts/                       Import, audit, and evidence automation
docs/                          Portfolio, resume evidence, and lab notes
```

## Skill Library

The `skills/` directory contains reusable Codex workflows for local LLM evaluation, research briefs, code review, PRD-to-task planning, resume bullets, and SEO audits. Each skill is a lightweight folder with invocation instructions and a small output template for future threads to reuse.

## Quick Start

Create a local virtual environment and install the repo with developer tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use `python3` to create the virtual environment on macOS. After activation, use
`python` so every command runs through `.venv/bin/python`. If `python` does not
resolve to the virtualenv, reactivate it with `source .venv/bin/activate`.

Run the test suite:

```bash
python -m pytest -q
```

Run the dashboard smoke check:

```bash
python3 scripts/model_dashboard_smoke.py
```

The editable install exposes the dashboard package from `apps/model-dashboard`.
The dashboard runtime currently uses only Python standard library modules; the
`dev` extra installs `pytest` for local validation.

If `python -m pytest -q` fails with `No module named pytest`, the `dev` extra is
not installed in the active environment. Rerun `python -m pip install -e ".[dev]"`
after activating `.venv`.

In sandboxed Codex runs, pip may need network approval to download build tooling
or `pytest` from PyPI. That network access is only for installing developer
dependencies; running the dashboard and tests does not call cloud APIs, download
models, or require secrets.

```bash
python3 apps/model-dashboard/run_dashboard.py init-db --reset --with-fixtures
python3 apps/model-dashboard/run_dashboard.py report
python3 apps/model-dashboard/run_dashboard.py serve --demo
```

Then open `http://127.0.0.1:8765`.

The MVP uses only Python standard library modules. It does not download models, call APIs, or touch cloud services.
