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
| `model_page_url` | Optional | Public model page or local inventory page for user review. Metadata only; not an install command. |
| `github_url` | Optional | GitHub repository for the model/project when one is explicit. |
| `lm_studio_url` | Optional | LM Studio-compatible model page when explicit. |
| `ollama_url` | Optional | Ollama library or registry page when explicit. |
| `runtime_availability` | Optional | Short text naming known or unverified runtimes such as LM Studio, Ollama, llama.cpp, MLX, GGUF, or Safetensors. |
| `local_runner` | Optional | Exact local runner for approved one-click tests, such as `lmstudio-cli` or `openai-compatible`. Leave blank when unverified. |
| `local_model_id` | Optional | Exact local runtime model id. Required before dashboard run buttons can execute a model. |
| `default_endpoint` | Optional | Loopback/private-LAN endpoint for `openai-compatible` runs only. Do not store public URLs. |
| `security_review_status` | Required for registry rows | `unreviewed`, `needs_review`, `local_inventory_reviewed`, `reviewed`, or `blocked`. This is a due-diligence state, not a quality score. |
| `download_approval` | Required for registry rows | `not_approved`, `not_needed_local`, `approved`, or `blocked`. Default external candidates to `not_approved`. |
| `license_review_status` | Required for registry rows | `unknown`, `needs_review`, `reviewed`, or `blocked`. Do not infer license compatibility from popularity. |
| `provenance_status` | Required for registry rows | Examples: `source_metadata_only`, `local_inventory`, `unverified_local_inventory`, `unverified_local_note`, or `reviewed_artifact`. |
| `security_notes` | Required for registry rows | Short notes about source trust, artifact format, checksum/hash needs, custom-code risk, and unresolved safety concerns. |
| `isolation_notes` | Optional | Local runtime or sandbox guidance. Prefer LM Studio, Ollama, llama.cpp, or MLX paths that do not run untrusted model-card code. |
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
- Runtime/model links are navigation metadata only. Do not turn them into
  download, install, or model execution steps without explicit user approval.
- External candidates default to `security_review_status=needs_review` and
  `download_approval=not_approved` until a specific artifact, license, source,
  and local runtime path are reviewed.
- Treat executable code as higher risk than weight files. Do not run model-card
  Python, custom loaders, install scripts, notebooks, or repository code as part
  of model recommendation.
- Prefer local runtimes that load weights without executing upstream code. For
  formats, note whether the candidate is GGUF, MLX, Safetensors, or an
  unreviewed/custom format.
- Before approving a new download or update, record source provenance, license
  posture, file format, expected runtime, and checksum/hash or release evidence
  when available.
- Dashboard run buttons may only use explicit local runner metadata from an
  approved candidate row. Do not guess local model IDs from public model names.
- Do not convert claims into scores without a benchmark run.
- Do not create download instructions unless the user explicitly asks for a
  local install plan.
- Keep private notes out of tracked candidate records unless the user confirms
  they should be committed.
