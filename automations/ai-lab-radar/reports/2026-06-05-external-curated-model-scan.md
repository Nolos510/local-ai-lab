# AI Lab Radar Report

Date: 2026-06-05
Reviewer: Codex
Source packet: `automations/ai-lab-radar/inputs/2026-06-05-external-curated-model-scan.md`

## Summary

- Candidates reviewed: 5
- Ready for evaluation: 2
- Watchlist: 2
- Skipped: 0
- Needs more information: 1

This report is based on an External Radar metadata-only scan. It does not
download models, run models, call model APIs, add API clients, use secrets,
create registry rows, create dashboard scores, or create dashboard decisions.

The source packet is partially approved:

```text
Approved for radar review: partial - DeepSeek-R1-0528-Qwen3-8B only
Safe to commit: yes - public metadata only; only DeepSeek may enter registry
```

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Qwen/Qwen3-30B-A3B-MLX-4bit | Hugging Face model card | MLX 4-bit Qwen3 MoE candidate aligns directly with Apple Silicon local eval. | Existing committed Qwen r2 result may already cover a related installed artifact; avoid duplicate registry rows until model IDs are reconciled. | `ready_for_eval` |
| DeepSeek-R1-0528-Qwen3-8B | Hugging Face model card plus llama.cpp family support reference | Smaller reasoning/coding candidate with source benchmark claims and likely practical local size. | License and exact local artifact format need confirmation before registry entry. | `ready_for_eval` |
| google/gemma-3n-E4B-it | Hugging Face model card plus llama.cpp Gemma family support reference | Efficient-device and multimodal claims make it useful to watch for local lab expansion. | Current benchmark harness is text-first; license/access and exact local artifact need approval. | `watchlist` |
| microsoft/Phi-4-mini-reasoning | Hugging Face model card plus llama.cpp Phi family support reference | Very small reasoning-focused model could be a fast local math-reasoning baseline. | Source scope is math reasoning, not general assistant use; license and local artifact need confirmation. | `needs_more_info` |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | Hugging Face model card and Mistral docs | Apache-2.0 24B model with source claims around instruction following, repetition reduction, and function calling. | Official source runtime notes are GPU/server oriented; Mac-local quantized path is not approved yet. | `watchlist` |

## Candidate Records

### Qwen/Qwen3-30B-A3B-MLX-4bit

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-qwen3-30b-a3b-mlx-4bit` |
| `model_name` | Qwen/Qwen3-30B-A3B-MLX-4bit |
| `model_family` | Qwen3 |
| `provider_or_org` | Qwen |
| `params_b` | 30.5 total; 3.3 activated |
| `format_or_runtime` | MLX; 4-bit precision |
| `claimed_context_window` | 32,768 native; 131,072 with YaRN |
| `license` | Apache-2.0 |
| `source_url` | https://huggingface.co/Qwen/Qwen3-30B-A3B-MLX-4bit |
| `source_date` | source page date not explicit; accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Strong Apple Silicon fit because source package is MLX and 4-bit. |
| `claimed_strengths` | Source claims Qwen3 reasoning, coding, agent/tool use, instruction-following, multilingual, and long-context abilities. |
| `local_fit` | Likely high after model ID reconciliation with existing Qwen artifacts. |
| `hardware_fit` | MLX 4-bit suggests Mac-local practicality, but exact local artifact must be matched. |
| `risk_notes` | Could duplicate the already committed Qwen local benchmark lineage. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | If approved and distinct from the committed Qwen retest, run local benchmark harness. |

### DeepSeek-R1-0528-Qwen3-8B

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-deepseek-r1-0528-qwen3-8b` |
| `model_name` | DeepSeek-R1-0528-Qwen3-8B |
| `model_family` | DeepSeek R1 / Qwen3 |
| `provider_or_org` | DeepSeek AI |
| `params_b` | 8 |
| `format_or_runtime` | Local running referenced by source; GGUF-family feasibility to verify |
| `claimed_context_window` | unknown |
| `license` | unknown from reviewed metadata |
| `source_url` | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B |
| `source_date` | source page date not explicit; accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Compact reasoning/coding candidate suitable for a local benchmark queue. |
| `claimed_strengths` | Source benchmark table reports strong math, science, and LiveCodeBench results. |
| `local_fit` | Promising because of 8B size, pending approved artifact selection. |
| `hardware_fit` | Likely easier than 24B-30B candidates, but artifact format is not chosen. |
| `risk_notes` | License and exact local runtime path need confirmation. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Approve candidate, choose local artifact, then run the local benchmark harness. |

### google/gemma-3n-E4B-it

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-gemma-3n-e4b-it` |
| `model_name` | google/gemma-3n-E4B-it |
| `model_family` | Gemma 3n |
| `provider_or_org` | Google |
| `params_b` | E4B class; exact parameter mapping needs confirmation |
| `format_or_runtime` | Transformers-style model card; local family support to verify |
| `claimed_context_window` | unknown |
| `license` | unknown from reviewed metadata |
| `source_url` | https://huggingface.co/google/gemma-3n-E4B-it |
| `source_date` | 2025 citation year; accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Efficient-device and multimodal claims could expand local lab coverage. |
| `claimed_strengths` | Source claims multimodal input and multilingual coverage. |
| `local_fit` | Watchlist until text-only and multimodal eval fit are separated. |
| `hardware_fit` | Source claims efficient low-resource execution, but artifact fit is not selected. |
| `risk_notes` | Current benchmark is text-first; external access/license details need review. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Confirm approval and local artifact; start with text-only benchmark if approved. |

### microsoft/Phi-4-mini-reasoning

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-phi-4-mini-reasoning` |
| `model_name` | microsoft/Phi-4-mini-reasoning |
| `model_family` | Phi-4 |
| `provider_or_org` | Microsoft |
| `params_b` | 3.8 |
| `format_or_runtime` | Transformers-style model card; local family support to verify |
| `claimed_context_window` | 128K tokens |
| `license` | unknown from reviewed metadata |
| `source_url` | https://huggingface.co/microsoft/Phi-4-mini-reasoning |
| `source_date` | source page date not explicit; accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Small math-reasoning baseline for local constrained hardware. |
| `claimed_strengths` | Source focuses on multi-step, logic-intensive mathematical problem solving. |
| `local_fit` | Needs local artifact and license confirmation. |
| `hardware_fit` | Size is promising; supported local runtime remains unverified. |
| `risk_notes` | Narrow math reasoning scope may make it a specialty benchmark, not a general model. |
| `recommended_next_step` | `needs_more_info` |
| `proposed_eval` | Confirm license/runtime and decide whether math-heavy prompts belong in the harness. |

### mistralai/Mistral-Small-3.2-24B-Instruct-2506

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-mistral-small-3-2-24b-instruct-2506` |
| `model_name` | mistralai/Mistral-Small-3.2-24B-Instruct-2506 |
| `model_family` | Mistral Small |
| `provider_or_org` | Mistral AI |
| `params_b` | 24 |
| `format_or_runtime` | Safetensors; vLLM and Transformers noted by source |
| `claimed_context_window` | 128k/131,072-class context in reviewed source metadata |
| `license` | Apache-2.0 |
| `source_url` | https://huggingface.co/mistralai/Mistral-Small-3.2-24B-Instruct-2506 |
| `source_date` | 2025-06 release implied by model name; accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | General instruction-following candidate with function-calling and repetition improvements claimed by source. |
| `claimed_strengths` | Source claims improved instruction following, reduced infinite generations, and stronger function-calling template. |
| `local_fit` | Watchlist until a user-approved local quantized artifact is identified. |
| `hardware_fit` | Source unquantized vLLM guidance implies high GPU memory; local Mac fit needs evidence. |
| `risk_notes` | Do not assume local practicality from official server-oriented source notes. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Revisit after approved local artifact selection; run text and function-call-adjacent prompts. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Qwen/Qwen3-30B-A3B-MLX-4bit | `evals/local-llm-benchmark/SPEC.md` via `skills/local-llm-eval`, only if approved and distinct from the committed Qwen result. | Candidate-only. Do not create scores or decisions until a new benchmark run exists. |
| DeepSeek-R1-0528-Qwen3-8B | Local benchmark harness after license and local artifact are approved. | Candidate-only. No import until scored evidence exists. |

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| google/gemma-3n-E4B-it | Multimodal and efficient-device claims are interesting, but current harness is text-first. | Revisit after local artifact, license/access, and text-vs-multimodal eval scope are approved. |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | Strong general-model claims, but official runtime notes are GPU/server oriented. | Revisit after a user-approved quantized local artifact and hardware fit evidence are available. |

## Skips

| Candidate | Reason |
| --- | --- |
| None | No candidate was skipped in this scan. |

## Needs More Information

| Candidate | Missing information |
| --- | --- |
| microsoft/Phi-4-mini-reasoning | License, local artifact/runtime, and whether the current benchmark should grow a math-reasoning lane. |

## Import Or Task Notes

- Registry updates: add only `DeepSeek-R1-0528-Qwen3-8B` to
  `data/model_registry/candidates.csv`. Qwen, Gemma, Phi, and Mistral remain
  unregistered until separately approved.
- Benchmark follow-ups: DeepSeek is the first external candidate selected to
  prove the external-radar-to-local-benchmark loop.
- Dashboard follow-ups: existing candidate registry fields can display approved
  external candidates through `/radar`; no schema change is required in this
  pass.
- Open questions: which external candidates the user approves, whether to add a
  math-heavy prompt lane, and whether multimodal candidates should wait for a
  separate harness extension.
