# AI Lab Radar Report

Date: 2026-06-03
Reviewer: Codex
Source packet: `evals/local-llm-benchmark/SPEC.md`, prompt `LLMCORE-v0.1-008: Research Synthesis From Supplied Sources`

## Summary

- Candidates reviewed: 2
- Ready for evaluation: 1
- Watchlist: 1
- Skipped: 0
- Needs more information: 0

This report uses only the local source packet facts from Source A, Source B, and
Source C in the benchmark spec. It does not fetch links, download models, create
install instructions, or assign eval scores.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Model Atlas 7B | Source A, Source C | Claims fast behavior on a MacBook Air M2 and good answers on simple coding prompts. | Source claims it often gives overconfident dates. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. | `watchlist` |
| Model Boreal 13B | Source B, Source C | Claims stronger long-form summaries and better uncertainty statements than Atlas 7B. | Source claims it is slower than Atlas 7B. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. | `ready_for_eval` |

## Candidate Records

### Model Atlas 7B

| Field | Value |
| --- | --- |
| `candidate_id` | `20260603-model-atlas-7b` |
| `model_name` | Model Atlas 7B |
| `model_family` | Unknown |
| `provider_or_org` | Unknown |
| `params_b` | 7 |
| `format_or_runtime` | Unknown |
| `claimed_context_window` | Unknown |
| `license` | Unknown |
| `source_url` | `local-file:evals/local-llm-benchmark/SPEC.md#LLMCORE-v0.1-008` |
| `source_date` | Unknown |
| `discovered_at` | 2026-06-03 |
| `why_interesting` | Source claims fast behavior on MacBook Air M2 and good simple coding responses. |
| `claimed_strengths` | Claimed fast on MacBook Air M2; claimed good answers on simple coding prompts. |
| `local_fit` | Claimed tested without internet access on MacBook Air M2. |
| `hardware_fit` | Claimed fast on MacBook Air M2; RAM/VRAM practicality unknown. |
| `risk_notes` | Source claims overconfident dates. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Revisit for a local coding and truthfulness/date-sensitivity benchmark after local artifact, runtime, and license are confirmed. |

### Model Boreal 13B

| Field | Value |
| --- | --- |
| `candidate_id` | `20260603-model-boreal-13b` |
| `model_name` | Model Boreal 13B |
| `model_family` | Unknown |
| `provider_or_org` | Unknown |
| `params_b` | 13 |
| `format_or_runtime` | Unknown |
| `claimed_context_window` | Unknown |
| `license` | Unknown |
| `source_url` | `local-file:evals/local-llm-benchmark/SPEC.md#LLMCORE-v0.1-008` |
| `source_date` | Unknown |
| `discovered_at` | 2026-06-03 |
| `why_interesting` | Source claims stronger long-form summaries and better uncertainty statements than Atlas 7B. |
| `claimed_strengths` | Claimed stronger long-form summaries; claimed better uncertainty statements. |
| `local_fit` | Claimed tested without internet access. |
| `hardware_fit` | Claimed slower than Atlas 7B; RAM/VRAM practicality unknown. |
| `risk_notes` | Slower than Atlas 7B. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Run the local LLM benchmark research-synthesis and uncertainty prompts first, with speed metadata captured but no score created until a real run exists. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Model Boreal 13B | `evals/local-llm-benchmark/SPEC.md`, especially research synthesis and uncertainty-focused prompts. | Candidate only. Do not create `eval_scores.csv` or dashboard decisions until a local benchmark run produces evidence. |

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| Model Atlas 7B | Interesting speed and simple coding claims, but date overconfidence is a material risk for daily-driver use. | Revisit after confirming local artifact/runtime/license and testing date-sensitive truthfulness alongside simple coding prompts. |

## Skips

| Candidate | Reason |
| --- | --- |
| None | No candidate in the supplied packet clearly warrants `skip`. |

## Needs More Information

| Candidate | Missing information |
| --- | --- |
| None | Missing metadata is recorded as risk notes but does not block using Boreal as the first eval target or keeping Atlas on watchlist. |

## Import Or Task Notes

- Registry updates: none in this pass; this is a candidate report only.
- Benchmark follow-ups: prepare a local benchmark task for Model Boreal 13B after confirming the model is already locally available and approved for evaluation.
- Dashboard follow-ups: none; no eval scores or dashboard decisions were created.
- Open questions: license, provider or organization, runtime or format, context window, local artifact path, RAM/VRAM practicality, and whether either model is intended for image input, browser use, or private document retrieval.
