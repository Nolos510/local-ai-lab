# AI Lab Radar

Local-first workflow scaffold for tracking interesting local and open-weight AI
models as review candidates.

## Purpose

AI Lab Radar turns manually approved model discovery notes into candidate records
for later evaluation. It does not download models, run models, call cloud APIs,
or require secrets.

## Radar Lanes

### Local Radar

Local Radar uses only repo-local, user-approved source packets and prior local
benchmark artifacts. This is the default lane for creating durable candidate
records.

### External Radar

External Radar is an on-demand metadata scan over curated public sources such as
official model cards, Hugging Face pages, GitHub release/readme pages, and
official project docs. External Radar may collect source links and public claims,
but it must write an unapproved source packet first. External candidates do not
enter `data/model_registry/candidates.csv` until the user explicitly approves
them.

External Radar still must not download models, run models, call model APIs, add
API clients, use secrets, or create install instructions.

## Inputs

Use only user-approved local inputs, such as:

- User-provided release notes, model cards, benchmark notes, or links.
- Local research notes copied into a thread or report.
- Prior AI Lab OS benchmark reports and dashboard decisions.

For Local Radar, do not add crawler code, automatic web fetching, package
downloads, model downloads, or API clients to this automation.

For External Radar, perform public metadata discovery manually/on demand and
write a source packet with `Approved for radar review: no` and `Safe to commit:
no` until the user approves it.

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

For External Radar, insert an approval gate between steps 1 and 2. The first
packet/report is candidate-only and must not edit `data/model_registry`.

## Validation

For documentation-only radar updates, inspect the diff and confirm no runtime
dependencies, network calls, secrets, or download logic were added.

If radar output feeds dashboard CSV import, run:

```bash
python3 scripts/model_dashboard_smoke.py
```
