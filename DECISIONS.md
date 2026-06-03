# Decisions

## 2026-05-12: Start as One Repo

AI Lab OS starts as one monorepo because the radar, eval harness, dashboard, skills, tasks, and evidence docs share data and context. Separate repos can come later for portfolio-ready tools or security boundaries.

## 2026-05-12: Dependency-Free Dashboard MVP

The Local Model Performance Dashboard uses the Python standard library instead of Streamlit or Flask for the MVP. This keeps setup simple on macOS, avoids dependency installation, and makes validation possible immediately.

## 2026-05-12: SQLite as Dashboard Source of Truth

The dashboard persists data in SQLite under `data/dashboard`. CSV remains the interchange format for fixtures, imports, exports, and future benchmark scripts.

## 2026-05-12: Fixture-First Workflow

The dashboard ships with demo CSV fixtures so the app, tests, and reports work before any real model testing data exists.

## 2026-05-12: No Model Automation in MVP

The MVP tracks model results only. It does not download, install, run, benchmark, or call any AI model.

## 2026-05-13: Root Python Project Metadata

AI Lab OS uses a root `pyproject.toml` so local setup is reproducible with `python -m pip install -e ".[dev]"`. The dashboard package is discovered from `apps/model-dashboard`, runtime dependencies remain empty because the app is stdlib-only, and the `dev` extra installs `pytest` for validation.

## 2026-05-15: Local LLM Benchmark v0.1 Contract

The first repeatable local LLM benchmark is documentation-first under `evals/local-llm-benchmark/SPEC.md`. It defines prompt set `ai-lab-local-llm-core-v0.1`, rubric version `ai-lab-local-llm-rubric-v0.1`, raw local artifact expectations, and dashboard-compatible CSV output. Benchmark-only identifiers stay in raw artifacts, skill reports, and `model_runs.run_notes` until the dashboard needs first-class prompt-level tables.

## 2026-06-03: v0.3 Harness Dependency Gate

The v0.3 local benchmark harness can remain Python stdlib-only. Expected harness needs are command parsing, JSONL, CSV, Markdown, subprocess capture, timestamps, temporary files, and dashboard import output, all covered by the standard library. Any Harness Builder proposal for new dependencies must first document the missing stdlib capability, runtime vs dev scope, transitive risk, and why it does not violate local-first/no-cloud boundaries.
