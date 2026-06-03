# AI Lab Radar

Local-first workflow scaffold for tracking interesting local and open-weight AI
models as review candidates.

## Purpose

AI Lab Radar turns manually approved model discovery notes into candidate records
for later evaluation. It does not download models, run models, call cloud APIs,
or require secrets.

## Inputs

Use only user-approved local inputs, such as:

- User-provided release notes, model cards, benchmark notes, or links.
- Local research notes copied into a thread or report.
- Prior AI Lab OS benchmark reports and dashboard decisions.

Do not add crawler code, automatic web fetching, package downloads, model
downloads, or API clients to this automation.

## Outputs

Radar work should produce:

- Candidate summaries using `candidate-schema.md`.
- Optional report notes using `templates/radar-report.md`.
- Candidate registry records under `data/model_registry` when a candidate is
  ready to track.
- Follow-up task recommendations for local benchmark or dashboard work.

## Workflow

1. Collect source notes and record where they came from.
2. Normalize each candidate using `candidate-schema.md`.
3. Mark the candidate as `watchlist`, `ready_for_eval`, `skip`, or
   `needs_more_info`.
4. Recommend the next local action without downloading or running the model.
5. If a model is ready for evaluation, point it at
   `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`.

## Validation

For documentation-only radar updates, inspect the diff and confirm no runtime
dependencies, network calls, secrets, or download logic were added.

If radar output feeds dashboard CSV import, run:

```bash
python3 scripts/model_dashboard_smoke.py
```
