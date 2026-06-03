# Harness Asset Proposals v0.1

These files convert `SPEC.md` into harness-ready static assets without running
models or adding benchmark execution code.

## Prompt Manifest

Path: `manifests/prompt-manifest-v0.1.json`

Purpose: source of prompt-run truth for a future local benchmark harness.

Proposed prompt fields:

- `prompt_id`: stable prompt identifier, such as `LLMCORE-v0.1-001`.
- `title`: human-readable prompt title extracted from `SPEC.md`.
- `primary_dimensions`: rubric dimensions the prompt primarily informs.
- `expected_evidence`: evaluator checks to look for in the raw response.
- `prompt_text_lines`: prompt text as an array of lines; a harness should join
  these with newline characters before sending.

The manifest also carries `prompt_set_id`, `rubric_version`, run-mode defaults,
and a field contract for future validation.

## Rubric/Scorecard

Path: `rubrics/rubric-scorecard-v0.1.json`

Purpose: evaluator and dashboard-normalization contract for benchmark output.

Proposed scorecard fields:

- `dimensions`: the eleven dashboard metric fields, descriptions, covered
  prompt IDs, and scoring guidance.
- `score_scale`: shared 0-100 anchors.
- `score_caps`: cap rules for fabricated live knowledge, broken code, missed
  formats, and fast-but-low-quality runs.
- `aggregate_score`: mean-of-eleven `total_score` rule.
- `final_labels` and `decision_values`: dashboard-compatible summary outputs.
- `prompt_result_record_proposal`: shape for per-prompt evaluator records.
- `run_scorecard_record_proposal`: shape for aggregate run scoring.
- `dashboard_normalized_outputs`: CSV fields needed by `apps/model-dashboard`.

## Status

These are format proposals. They are ready for a future harness to consume, but
no harness code, model calls, or benchmark runs are added in this step.
