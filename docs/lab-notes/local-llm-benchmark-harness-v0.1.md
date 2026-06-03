# Local LLM Benchmark Harness v0.1

Date: 2026-06-03

## What Changed

- Added a Python stdlib-only harness at
  `evals/local-llm-benchmark/harness.py`.
- Added local prompt and rubric files:
  `evals/local-llm-benchmark/prompts/ai-lab-local-llm-core-v0.1.json` and
  `evals/local-llm-benchmark/rubrics/ai-lab-local-llm-rubric-v0.1.json`.
- The harness can create run artifact directories, write response and scoring
  templates, preserve human-supplied raw responses in `raw_responses.jsonl`, and
  emit the four dashboard import CSV files.
- Added harness tests under `evals/local-llm-benchmark/tests` and included them
  in the repo `pytest` testpaths.

## Safety Posture

- The harness does not call models, download models, or use cloud APIs.
- The harness has no network imports and no runtime dependencies beyond the
  Python standard library.
- Response capture is explicit: raw model output must be supplied by a local
  human/operator as JSONL.
- `eval_scores.csv` and `decisions.csv` remain header-only until manual score
  and decision files are provided, avoiding accidental import of fake scores.

## Validation

- Prompt and rubric JSON files can be validated with `python3 -m json.tool`.
- Harness tests run as part of `python -m pytest -q`.
