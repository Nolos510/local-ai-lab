# AI Lab Radar Candidate Schema

Use this schema for candidate records before any model is downloaded, installed,
or benchmarked.

## Candidate Fields

| Field | Requirement | Notes |
| --- | --- | --- |
| `candidate_id` | Required | Stable local ID, such as `20260603-qwen-coder-local`. |
| `model_name` | Required | Human-readable model name. Do not invent names. |
| `model_family` | Optional | Examples: Qwen, Llama, Mistral, Gemma. |
| `provider_or_org` | Optional | Publisher, lab, or local source. |
| `params_b` | Optional | Parameter count in billions when known. |
| `format_or_runtime` | Optional | Examples: GGUF, MLX, Ollama, LM Studio. |
| `claimed_context_window` | Optional | Claimed context length. Leave blank when unknown. |
| `license` | Optional | License string when known. Do not infer. |
| `source_url` | Optional | Upstream page or local note reference. |
| `source_date` | Optional | Date of the source, not the discovery date. |
| `discovered_at` | Required | ISO timestamp or date when added to radar. |
| `why_interesting` | Required | Concise reason to track. |
| `claimed_strengths` | Optional | Claims from source notes, clearly marked as claims. |
| `local_fit` | Optional | Expected fit for Apple Silicon or local workflow. |
| `hardware_fit` | Optional | Known or expected RAM/VRAM practicality. |
| `risk_notes` | Optional | License, size, safety, quality, or source-confidence concerns. |
| `recommended_next_step` | Required | `watchlist`, `ready_for_eval`, `skip`, or `needs_more_info`. |
| `proposed_eval` | Optional | Benchmark or skill to use next. |

## Dashboard Mapping

Candidates are not dashboard records yet. When a candidate is actually tested,
map stable fields into:

- `models.csv`: model identity, family, provider, params, license, source URL.
- `model_runs.csv`: backend, format, quantization, context, hardware, run notes.
- `eval_scores.csv`: benchmark scores after evaluation only.
- `decisions.csv`: keep/watchlist/retest/skip after evaluation.

## Boundary Rules

- A radar candidate is a review target, not an install request.
- Do not convert claims into scores without a benchmark run.
- Do not create download instructions unless the user explicitly asks for a
  local install plan.
- Keep private notes out of tracked candidate records unless the user confirms
  they should be committed.
