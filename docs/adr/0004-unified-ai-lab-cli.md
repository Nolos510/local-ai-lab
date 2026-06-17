# ADR 0004: Unified `ai-lab` Operating CLI

Status: accepted

Date: 2026-06-16

## Context

AI Lab OS workflows were spread across several entry points:

- `local-ai-lab` for the local RAG/provider app
- `evals/local-llm-benchmark/harness.py` for benchmark artifacts
- `apps/model-dashboard/run_dashboard.py` for dashboard import/report/serve
- direct CSV/SQLite inspection for radar and status checks

That was workable for development, but it made the product loop harder to teach,
repeat, validate, and turn into portfolio evidence.

## Decision

Expose a new `ai-lab` console script at `local_ai_lab.cli.lab:main`.

The command is a thin stdlib-only orchestrator:

- `ai-lab status` reads local CSV/SQLite/artifact state directly.
- `ai-lab radar list` reads candidate records directly from the registry CSV.
- `ai-lab bench run` initializes a benchmark artifact for an approved candidate
  through the existing benchmark harness.
- `ai-lab import`, `ai-lab report`, and `ai-lab dashboard` shell out to the
  existing dashboard entry point.

The CLI does not download models, call model APIs, call cloud APIs, or add
secrets. It does not run a model implicitly; benchmark model execution remains a
separate explicit local harness action.

## Consequences

AI Lab OS now has a single top-level operating surface for the local product
loop while preserving package boundaries between the RAG app, benchmark harness,
and dashboard.

Tests assert that workflow actions dispatch to existing scripts with explicit
argv lists, which keeps command construction auditable and avoids shell
injection risks.

Future hardware profiling and portfolio-report commands can extend this surface
without turning the RAG runtime into an agent system or adding hidden cloud
behavior.
