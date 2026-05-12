# AI Lab OS Architecture

## System Shape

AI Lab OS is one local-first repo while the tools are still closely related. Shared data lives under `data/`, active work lives under `tasks/`, and reusable operating patterns live under `skills/`, `agents/`, and `docs/`.

## Data Flow

```text
AI Lab Radar
  -> data/model_registry
  -> evals/local-llm-benchmark
  -> data/eval_results
  -> apps/model-dashboard
  -> docs/resume-evidence and docs/portfolio
```

## Components

- **AI Lab Radar:** Future automation for finding candidate models to review. It records candidates only and does not download models.
- **LLM Eval Harness:** Future local benchmark suite that writes structured eval outputs for dashboard import.
- **Model Dashboard:** Current MVP. It stores model metadata, test runs, eval scores, and decisions in SQLite with CSV import/export.
- **Skill Library:** Reusable workflows for evaluation, research, code review, PRD-to-tasks, resume bullets, and SEO audits.
- **Weekly Briefs:** Future automation for recurring research summaries from approved local or user-provided sources.
- **Stack Auditor:** Future scripts for checking local tools, versions, permissions, and security posture.
- **Resume Automation:** Future evidence exporter that turns completed work and reports into portfolio-ready artifacts.

## Current Dashboard Storage

The dashboard uses `data/dashboard/model_dashboard.sqlite` as local runtime state. Fixture CSVs live in `apps/model-dashboard/fixtures` and can recreate a demo database at any time.

## Boundary Rules

- Keep shared schemas and reusable data formats in the main repo.
- Split a component into its own repo only when it becomes portfolio-ready, needs separate deployment, or needs a different security boundary.
