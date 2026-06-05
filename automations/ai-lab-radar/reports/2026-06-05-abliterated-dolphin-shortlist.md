# AI Lab Radar Report

Date: 2026-06-05
Reviewer: Codex
Source packet: `automations/ai-lab-radar/inputs/2026-06-05-abliterated-dolphin-shortlist.md`

## Summary

- Candidates reviewed: 6
- Ready for evaluation: 4
- Watchlist: 2
- Skipped: 0
- Needs more information: 0

This report creates a dedicated abliterated/Dolphin candidate lane for the
dashboard. It is based on public metadata only. It does not download models,
run models, call model APIs, add API clients, use secrets, create scores, or
create decisions.

The source packet is approved for candidate-only registry entries:

```text
Approved for radar review: yes - user requested a dedicated abliterated/dolphin dashboard section
Safe to commit: yes - public metadata only; candidate records only
```

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Qwen3-8B-Abliterated-GGUF | Hugging Face model card and GGUF package | Best first abliterated target: 8B, Apache-2.0, GGUF, and local-runtime metadata. | Abliteration is experimental and changes refusal behavior; score only after local benchmark evidence. | `ready_for_eval` |
| Dolphin3.0-Llama3.1-8B-GGUF | Hugging Face model card | Best first Dolphin target: 8B GGUF with local runtime metadata. | Low-refusal behavior, Llama license terms, and stability must be reviewed. | `ready_for_eval` |
| gemma-3-12b-it-abliterated-v2-GGUF | Hugging Face model card and abliterated collection | Useful specialty watchlist candidate for Gemma/local multimodal-adjacent testing. | Current benchmark is text-first; Gemma license and multimodal scope need review. | `watchlist` |
| Dolphin-Mistral-24B-Venice-Edition | Hugging Face model card | Higher-capability Dolphin/Venice specialty candidate. | 256 GB RAM makes size acceptable; low-refusal behavior still needs license, stability, and safety review. | `ready_for_eval` |
| Qwen3-30B-A3B-Abliterated | Hugging Face model card and abliterated collection | Larger Qwen3 MoE abliterated candidate with Apache-2.0 source metadata. | 256 GB RAM makes size less concerning; avoid duplicate lineage with the existing Qwen r2 run. | `ready_for_eval` |
| Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF | Hugging Face model card and abliterated collection | Baseline abliterated 8B GGUF for comparing newer specialty candidates. | Older base model and Llama license make it a baseline, not the first run. | `watchlist` |

## Candidate Records

### Qwen3-8B-Abliterated-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-qwen3-8b-abliterated-gguf` |
| `model_name` | Qwen3-8B-Abliterated-GGUF |
| `model_family` | Qwen3 Abliterated |
| `provider_or_org` | mlabonne / bartowski |
| `params_b` | 8 |
| `format_or_runtime` | GGUF through LM Studio or llama.cpp |
| `source_url` | https://huggingface.co/bartowski/mlabonne_Qwen3-8B-abliterated-GGUF |
| `source_date` | accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Practical 8B Qwen3 abliterated candidate with GGUF availability for local low-refusal behavior testing. |
| `risk_notes` | Abliteration changes refusal behavior; benchmark with explicit safety and risk notes and do not convert source claims into scores. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Run local benchmark harness with normal prompts plus evaluator notes on refusals, uncertainty, and policy-boundary behavior. |

### Dolphin3.0-Llama3.1-8B-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-dolphin3-llama31-8b-gguf` |
| `model_name` | Dolphin3.0-Llama3.1-8B-GGUF |
| `model_family` | Dolphin |
| `provider_or_org` | Cognitive Computations / dphn |
| `params_b` | 8 |
| `format_or_runtime` | GGUF through LM Studio or llama.cpp |
| `source_url` | https://huggingface.co/dphn/Dolphin3.0-Llama3.1-8B-GGUF |
| `source_date` | accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Practical 8B Dolphin GGUF candidate for local agentic and general-assistant comparison. |
| `risk_notes` | Dolphin low-refusal behavior needs safety, license, and stability review before daily-driver use. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Run local benchmark harness and compare against Qwen r2, with separate notes for refusals and instruction-following. |

### gemma-3-12b-it-abliterated-v2-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-gemma-3-12b-it-abliterated-v2-gguf` |
| `model_name` | gemma-3-12b-it-abliterated-v2-GGUF |
| `model_family` | Gemma Abliterated |
| `provider_or_org` | mlabonne |
| `params_b` | 12 |
| `format_or_runtime` | GGUF with text/image model-card metadata |
| `source_url` | https://huggingface.co/mlabonne/gemma-3-12b-it-abliterated-v2-GGUF |
| `source_date` | accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | 12B Gemma abliterated GGUF candidate with multimodal-adjacent metadata; useful for a future text-plus-vision lane. |
| `risk_notes` | Current harness is text-first; Gemma license terms and local artifact behavior need review before benchmark import. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Keep on watchlist until text-only versus multimodal eval scope is approved. |

### Dolphin-Mistral-24B-Venice-Edition

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-dolphin-mistral-24b-venice-edition` |
| `model_name` | Dolphin-Mistral-24B-Venice-Edition |
| `model_family` | Dolphin / Mistral |
| `provider_or_org` | Cognitive Computations / Venice AI |
| `params_b` | 24 |
| `format_or_runtime` | Source model with quantized local-runtime options to verify |
| `source_url` | https://huggingface.co/dphn/Dolphin-Mistral-24B-Venice-Edition |
| `source_date` | accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | 24B Dolphin/Venice uncensored candidate that may be a higher-capability specialty model if a local quantized artifact is approved. |
| `risk_notes` | 256 GB RAM makes size acceptable; low-refusal behavior still needs license, stability, and safety review before daily-driver use. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Select an approved local quantized artifact first; then run the local benchmark harness as a specialty comparison. |

### Qwen3-30B-A3B-Abliterated

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-qwen3-30b-a3b-abliterated` |
| `model_name` | Qwen3-30B-A3B-Abliterated |
| `model_family` | Qwen3 Abliterated |
| `provider_or_org` | mlabonne |
| `params_b` | 30B-A3B / 31B-class |
| `format_or_runtime` | Safetensors source; local quantization path to verify |
| `source_url` | https://huggingface.co/mlabonne/Qwen3-30B-A3B-abliterated |
| `source_date` | accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Large Qwen3 MoE abliterated candidate with Apache-2.0 source metadata; potential high-quality specialty model. |
| `risk_notes` | 256 GB RAM makes size less concerning; avoid duplicate lineage with existing Qwen r2 and confirm exact runtime before a new run. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Choose a distinct local artifact or endpoint, then compare against the existing Qwen r2 result. |

### Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260605-llama31-8b-instruct-abliterated-gguf` |
| `model_name` | Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF |
| `model_family` | Llama Abliterated |
| `provider_or_org` | mlabonne |
| `params_b` | 8 |
| `format_or_runtime` | GGUF through LM Studio or llama.cpp |
| `source_url` | https://huggingface.co/mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated-GGUF |
| `source_date` | accessed 2026-06-05 |
| `discovered_at` | 2026-06-05 |
| `why_interesting` | Older high-download Llama 3.1 abliterated GGUF baseline for comparing newer specialty models against a known local 8B lineage. |
| `risk_notes` | Older base model and Llama license mean it should be a baseline, not the first specialty benchmark unless needed. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Use only as a baseline if newer Qwen or Dolphin specialty candidates produce ambiguous results. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Qwen3-8B-Abliterated-GGUF | Local benchmark harness with extra evaluator notes on refusal, uncertainty, and coherence. | Candidate-only. No score or decision until local responses exist. |
| Dolphin3.0-Llama3.1-8B-GGUF | Local benchmark harness, compared against Qwen r2 and Qwen3 abliterated if available. | Candidate-only. No score or decision until local responses exist. |
| Dolphin-Mistral-24B-Venice-Edition | Local benchmark harness after selecting a local quantized artifact or endpoint. | Candidate-only. 256 GB RAM means size is not the primary blocker. |
| Qwen3-30B-A3B-Abliterated | Local benchmark harness after runtime/artifact reconciliation with Qwen r2. | Candidate-only. Use to compare larger specialty Qwen behavior. |

## Watchlist

| Candidate | Reason | Revisit trigger |
| --- | --- | --- |
| gemma-3-12b-it-abliterated-v2-GGUF | Text/image metadata is interesting, but the current harness is text-first. | Revisit when a text-plus-vision lane is planned or a text-only scope is approved. |
| Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF | Useful baseline, but older than Qwen3/Dolphin first targets. | Revisit if newer specialty runs need a known 8B comparison. |

## Skips

| Candidate | Reason |
| --- | --- |
| None | No candidate was skipped in this scan. |

## Needs More Information

| Candidate | Missing information |
| --- | --- |
| None | Missing metadata is captured in watchlist risk notes. |

## Import Or Task Notes

- Registry updates: add the six candidate-only rows to
  `data/model_registry/candidates.csv`.
- Dashboard follow-up: `/lab` should show an `Abliterated / Dolphin Lane`
  section sourced from the registry.
- Benchmark follow-up: start with `Qwen3-8B-Abliterated-GGUF` or
  `Dolphin3.0-Llama3.1-8B-GGUF`, whichever is available locally first.
- Score boundary: do not create `scores.json`, dashboard imports, or decisions
  until a real local benchmark run exists.
