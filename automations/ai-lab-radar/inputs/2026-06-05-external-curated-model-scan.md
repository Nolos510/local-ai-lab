# AI Lab Radar Source Packet

Packet title: External Curated Model Metadata Scan
Packet date: 2026-06-05
Prepared by: Codex
Approved for radar review: partial - DeepSeek-R1-0528-Qwen3-8B only
Safe to commit: yes - public metadata only; only DeepSeek may enter registry

## Scope

On-demand External Radar scan over curated public metadata sources. This packet
collects candidate metadata only from Hugging Face model cards, official model
docs, and GitHub project pages. No models were downloaded, no models were run,
no model APIs were called, no API clients or dependencies were added.

Approval is partial: only `DeepSeek-R1-0528-Qwen3-8B` is approved for registry
entry and local benchmark follow-up. All other candidates in this packet remain
unregistered review material until separately approved by the user.

## Source References

| Source ID | Source type | Source date | Link or local reference | Notes |
| --- | --- | --- | --- | --- |
| A | Hugging Face model card | source page date not explicit; accessed 2026-06-05 | https://huggingface.co/Qwen/Qwen3-30B-A3B-MLX-4bit | Qwen3 30B-A3B MLX 4-bit model card. |
| B | Hugging Face model card | 2025 citation year; accessed 2026-06-05 | https://huggingface.co/google/gemma-3n-E4B-it | Google Gemma 3n E4B instruction-tuned model card. |
| C | Hugging Face model card | source page date not explicit; accessed 2026-06-05 | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | DeepSeek R1 0528 Qwen3 8B model card. |
| D | Hugging Face model card | source page date not explicit; accessed 2026-06-05 | https://huggingface.co/microsoft/Phi-4-mini-reasoning | Microsoft Phi-4 mini reasoning model card. |
| E | Hugging Face model card | 2025-06 release implied by model name; accessed 2026-06-05 | https://huggingface.co/mistralai/Mistral-Small-3.2-24B-Instruct-2506 | Mistral Small 3.2 24B Instruct model card. |
| F | GitHub project README | source page date not explicit; accessed 2026-06-05 | https://github.com/ggml-org/llama.cpp | Runtime metadata reference for local GGUF and Apple Silicon support. |

## Copied Notes Or Excerpts

### Source A

Public metadata reviewed: model name, MLX and 4-bit precision tags,
Apache-2.0 license, Qwen3 MoE family, 30.5B total and 3.3B active parameter
description, and native 32,768 token context claim with a 131,072 token YaRN
claim.

### Source B

Public metadata reviewed: Gemma 3n E4B instruction-tuned model name, Google
provider, Gemma family, efficient execution on low-resource devices claim,
multimodal input claim, text-output behavior, open-weights framing, and
training data citation year.

### Source C

Public metadata reviewed: DeepSeek-R1-0528-Qwen3-8B model name, DeepSeek
provider, Qwen3 8B architecture reference, local-running reference to the
DeepSeek-R1 repository, and model-card benchmark claims for math, science, and
coding-oriented tests.

### Source D

Public metadata reviewed: Phi-4-mini-reasoning model name, Microsoft provider,
Phi-4 family, 3.8B parameter architecture statement, 128K token context claim,
and stated focus on math reasoning in memory/compute-constrained environments.

### Source E

Public metadata reviewed: Mistral-Small-3.2-24B-Instruct-2506 model name,
Mistral AI provider, Apache-2.0 license, 24B size in model name, instruction
following, repetition, and function-calling improvements over the prior Small
3.1 release, and a stated GPU RAM requirement for unquantized vLLM use.

### Source F

Public metadata reviewed: llama.cpp project description as local C/C++ LLM
inference, Apple Silicon support, GGUF/local model-file usage, and support list
covering Qwen, DeepSeek, Phi, Gemma, and Mistral model families.

## Candidate Notes

### Candidate: Qwen/Qwen3-30B-A3B-MLX-4bit

| Field | Value |
| --- | --- |
| Candidate name from source | Qwen/Qwen3-30B-A3B-MLX-4bit |
| Model family | Qwen3 |
| Provider or org | Qwen |
| Parameter count | 30.5B total; 3.3B activated |
| Format or runtime | MLX; 4-bit precision |
| Claimed context window | 32,768 native; 131,072 with YaRN |
| License | Apache-2.0 |
| Local artifact status | External metadata only; existing local Qwen retest artifact is separate and already committed |
| Hardware fit | Strong candidate for Apple Silicon testing because source package is MLX 4-bit |
| Claimed strengths | Source claims Qwen3 reasoning, instruction-following, agent/tool use, multilingual support, and coding/math strengths. |
| Risks or caveats | Existing local Qwen retest already covers a related installed artifact. Confirm exact model ID and runtime match before adding a second registry row. |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | If approved and distinct from the committed Qwen retest, run `evals/local-llm-benchmark/SPEC.md` through `skills/local-llm-eval`. |

### Candidate: DeepSeek-R1-0528-Qwen3-8B

| Field | Value |
| --- | --- |
| Candidate name from source | deepseek-ai/DeepSeek-R1-0528-Qwen3-8B |
| Model family | DeepSeek R1 / Qwen3 |
| Provider or org | DeepSeek AI |
| Parameter count | 8B architecture reference |
| Format or runtime | Source references local running through DeepSeek-R1; llama.cpp lists DeepSeek and Qwen families as supported model families |
| Claimed context window | unknown |
| License | unknown from reviewed page metadata |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Likely more practical than 24B-30B candidates due 8B size, but exact local quantization path needs approval and artifact selection. |
| Claimed strengths | Source benchmark table claims strong AIME, HMMT, GPQA, and LiveCodeBench scores for this distilled reasoning variant. |
| Risks or caveats | Need explicit license confirmation and a local artifact format before evaluation. Avoid importing API/web claims as eval evidence. |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Approve candidate, select a local GGUF/MLX/Ollama/LM Studio artifact, then run the local benchmark harness. |

### Candidate: google/gemma-3n-E4B-it

| Field | Value |
| --- | --- |
| Candidate name from source | google/gemma-3n-E4B-it |
| Model family | Gemma 3n |
| Provider or org | Google |
| Parameter count | E4B class; exact parameter interpretation needs confirmation from source docs before registry entry |
| Format or runtime | Transformers-style model card; llama.cpp lists Gemma family support |
| Claimed context window | unknown from reviewed metadata |
| License | unknown from reviewed metadata |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Interesting for local testing because source claims efficient execution on low-resource devices. |
| Claimed strengths | Source claims multimodal input across text, image, video, and audio, with text outputs and broad multilingual training coverage. |
| Risks or caveats | Current harness is text-first. Multimodal claims need a separate eval design; license/access terms need confirmation before registry entry. |
| Suggested radar disposition | `watchlist` |
| Proposed local eval | After approval, start with text-only benchmark prompts, then design a separate multimodal extension only if needed. |

### Candidate: microsoft/Phi-4-mini-reasoning

| Field | Value |
| --- | --- |
| Candidate name from source | microsoft/Phi-4-mini-reasoning |
| Model family | Phi-4 |
| Provider or org | Microsoft |
| Parameter count | 3.8B |
| Format or runtime | Transformers-style model card; llama.cpp lists Phi family support |
| Claimed context window | 128K tokens |
| License | unknown from reviewed metadata |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Size is attractive for local testing; exact supported local artifact must be chosen before eval. |
| Claimed strengths | Source states math-reasoning focus and memory/compute-constrained use cases. |
| Risks or caveats | Source states it is designed and tested for math reasoning only, so it may not be a general local assistant candidate. |
| Suggested radar disposition | `needs_more_info` |
| Proposed local eval | Confirm license and local artifact, then decide whether to add math-heavy prompts before comparing against general assistant models. |

### Candidate: mistralai/Mistral-Small-3.2-24B-Instruct-2506

| Field | Value |
| --- | --- |
| Candidate name from source | mistralai/Mistral-Small-3.2-24B-Instruct-2506 |
| Model family | Mistral Small |
| Provider or org | Mistral AI |
| Parameter count | 24B in model name |
| Format or runtime | Safetensors; vLLM and Transformers noted on source page |
| Claimed context window | 131,072 max token value appears in source usage examples; official docs also list 128k context for Mistral Small 3.2 |
| License | Apache-2.0 |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Watchlist: source notes about unquantized vLLM GPU RAM make direct local testing riskier; a local quantized artifact would need separate approval. |
| Claimed strengths | Source claims better instruction following, fewer infinite generations, and more robust function-calling template versus Small 3.1. |
| Risks or caveats | Source runtime guidance is server/GPU oriented. Do not assume Mac-local fit without approved local artifact evidence. |
| Suggested radar disposition | `watchlist` |
| Proposed local eval | Revisit after confirming an approved local artifact and hardware fit; use text and tool-call-adjacent prompts if approved. |

## Reviewer Notes

- Candidate records must follow `automations/ai-lab-radar/candidate-schema.md`.
- This packet is partially approved for DeepSeek only.
- Do not create registry rows for Qwen, Gemma, Phi, or Mistral from this packet
  without separate user approval.
- `ready_for_eval` candidates should point to
  `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`.
- Do not create dashboard scores or decisions until a real local benchmark run
  exists.
- Do not add install instructions unless the user separately asks for a local
  install plan.
