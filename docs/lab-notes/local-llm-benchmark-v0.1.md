# Local LLM Benchmark v0.1 Spec Note

Date: 2026-05-15

## What Changed

- Added the first repeatable local LLM benchmark contract in
  `evals/local-llm-benchmark/SPEC.md`.
- Defined prompt set `ai-lab-local-llm-core-v0.1` with 12 prompts covering
  truthfulness, reasoning, coding, debugging, planning, local AI lab usefulness,
  supplied-source synthesis, business SEO, long-context organization,
  constrained creativity, and privacy boundaries.
- Defined rubric version `ai-lab-local-llm-rubric-v0.1` with the same eleven
  dashboard score dimensions already used by `apps/model-dashboard`.
- Defined raw artifact expectations for `metadata.json`, `raw_responses.jsonl`,
  `evidence.md`, report output, and dashboard import CSV files.
- Documented how benchmark-only fields such as `benchmark_run_id`,
  `prompt_set_id`, `rubric_version`, and raw artifact paths fit into
  `run_notes` until the dashboard has first-class benchmark tables.

## Safety Posture

- The spec is local-first and documentation-only.
- It does not add model execution, model downloads, network calls, API keys, or
  new runtime dependencies.
- Raw responses and benchmark notes are treated as local user data.
- The baseline benchmark explicitly disables internet, browser, MCP, and file
  access unless a future prompt variant says otherwise.

## Follow-Up

- Build a small harness that writes `raw_responses.jsonl` and dashboard import
  CSVs from this spec.
- Add fixture benchmark artifacts once the harness exists.
- Consider first-class dashboard tables for prompt-level evidence after the MVP
  schema settles.

## 2026-06-03 Harness Asset Proposal

- Added `evals/local-llm-benchmark/manifests/prompt-manifest-v0.1.json` with
  prompt IDs, titles, primary dimensions, expected evidence, and prompt text
  lines extracted from `SPEC.md`.
- Added `evals/local-llm-benchmark/rubrics/rubric-scorecard-v0.1.json` with the
  score scale, eleven dashboard dimensions, evidence rules, score caps,
  aggregate score rule, final labels, decision values, and dashboard CSV fields.
- Added `evals/local-llm-benchmark/HARNESS_ASSETS.md` to explain the proposed
  manifest and scorecard shapes.
- No harness code, model calls, or benchmark runs were added.
