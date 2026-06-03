# AI Lab Radar Report

Date: 2026-06-03
Reviewer: Codex
Source packet: `automations/ai-lab-radar/inputs/2026-06-03-approved-source-packet.md`

## Summary

- Candidates reviewed: 2
- Ready for evaluation: 1
- Watchlist: 1
- Skipped: 0
- Needs more information: 0

This report uses only the approved repo-local source packet. It does not fetch
web pages, download models, run models, call cloud APIs, use secrets, create
dashboard decisions, or turn source claims into eval scores.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Model Atlas 7B | Source A, Source C from approved packet | Source claims fast behavior on MacBook Air M2 and good answers on simple coding prompts. | Source claims overconfident dates. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, local artifact path, and RAM/VRAM practicality are unknown. | `watchlist` |
| Model Boreal 13B | Source B, Source C from approved packet | Source claims stronger long-form summaries and better uncertainty statements than Atlas 7B. | Source claims slower behavior than Atlas 7B. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, local artifact path, and RAM/VRAM practicality are unknown. | `ready_for_eval` |

## Candidate Records

### Model Atlas 7B

| Field | Value |
| --- | --- |
| `candidate_id` | `20260603-model-atlas-7b` |
| `model_name` | Model Atlas 7B |
| `model_family` | unknown |
| `provider_or_org` | unknown |
| `params_b` | 7 |
| `format_or_runtime` | unknown |
| `claimed_context_window` | unknown |
| `license` | unknown |
| `source_url` | `local-file:automations/ai-lab-radar/inputs/2026-06-03-approved-source-packet.md#source-a` |
| `source_date` | unknown |
| `discovered_at` | 2026-06-03 |
| `why_interesting` | Source claims fast behavior on MacBook Air M2 and good answers on simple coding prompts. |
| `claimed_strengths` | Claimed fast on MacBook Air M2; claimed good answers on simple coding prompts. |
| `local_fit` | Source claims testing without internet access; local artifact status is unknown. |
| `hardware_fit` | Source claims fast behavior on MacBook Air M2; RAM or VRAM practicality is unknown. |
| `risk_notes` | Source claims overconfident dates. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Revisit after confirming local artifact, runtime, and license; test coding and date-sensitive truthfulness before treating as a daily-driver candidate. |

### Model Boreal 13B

| Field | Value |
| --- | --- |
| `candidate_id` | `20260603-model-boreal-13b` |
| `model_name` | Model Boreal 13B |
| `model_family` | unknown |
| `provider_or_org` | unknown |
| `params_b` | 13 |
| `format_or_runtime` | unknown |
| `claimed_context_window` | unknown |
| `license` | unknown |
| `source_url` | `local-file:automations/ai-lab-radar/inputs/2026-06-03-approved-source-packet.md#source-b` |
| `source_date` | unknown |
| `discovered_at` | 2026-06-03 |
| `why_interesting` | Source claims stronger long-form summaries and better uncertainty statements than Atlas 7B. |
| `claimed_strengths` | Claimed stronger long-form summaries; claimed better uncertainty statements. |
| `local_fit` | Source claims testing without internet access; local artifact status is unknown. |
| `hardware_fit` | Source claims slower behavior than Atlas 7B; RAM or VRAM practicality is unknown. |
| `risk_notes` | Slower than Atlas 7B. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | If already locally available and approved for testing, run `evals/local-llm-benchmark/SPEC.md` through `skills/local-llm-eval`, especially research synthesis and uncertainty prompts. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Model Boreal 13B | `evals/local-llm-benchmark/SPEC.md` via `skills/local-llm-eval`; prioritize research synthesis and uncertainty prompts. | Candidate only. Do not create `eval_scores.csv`, dashboard decisions, or final labels until a real local benchmark run produces evidence. |

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| Model Atlas 7B | Interesting speed and simple coding claims, but claimed date overconfidence is a material reliability risk. | Revisit after confirming local artifact/runtime/license and running date-sensitive truthfulness plus coding checks. |

## Skips

| Candidate | Reason |
| --- | --- |
| None | No supplied candidate clearly warrants `skip`. |

## Needs More Information

| Candidate | Missing information |
| --- | --- |
| None | Both candidates have enough approved source material for candidate-only disposition. Missing metadata remains captured as risk notes. |

## Import Or Task Notes

- Registry updates: none in this pass; this report is candidate-only.
- Benchmark follow-ups: prepare a local benchmark task for Model Boreal 13B only
  after confirming the model is already locally available and approved for
  testing.
- Dashboard follow-ups: none; no eval scores, labels, or dashboard decisions
  were created.
- Open questions: license, provider or organization, runtime or format, context
  window, local artifact path, RAM/VRAM practicality, and whether either model
  should later be tested for image input, browser use, or private document
  retrieval.

## Safety Posture

- Used only `automations/ai-lab-radar/inputs/2026-06-03-approved-source-packet.md`.
- No web fetching or web research.
- No model downloads.
- No model runs.
- No cloud APIs or secrets.
- No runtime dependencies added.
- No source claims converted into eval scores.
