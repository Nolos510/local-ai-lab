# AI Lab Radar Source Packet

Packet title: Abliterated and Dolphin Local Candidate Shortlist
Packet date: 2026-06-05
Prepared by: Codex
Approved for radar review: yes - user requested a dedicated abliterated/dolphin dashboard section
Safe to commit: yes - public metadata only; candidate records only

## Scope

On-demand External Radar scan over curated public Hugging Face metadata for
abliterated and Dolphin-family models that may be useful in a local AI lab.
This packet is a first-pass shortlist for evaluation, not a leaderboard.

No models were downloaded, no models were run, no model APIs were called, no API
clients or dependencies were added, and no install instructions were created.
Candidates may enter `data/model_registry/candidates.csv` as radar records only;
they do not become dashboard scores or decisions until a real local benchmark
run exists.

## Source References

| Source ID | Source type | Source date | Link or local reference | Notes |
| --- | --- | --- | --- | --- |
| A | Hugging Face collection | updated Mar 2; accessed 2026-06-05 | https://huggingface.co/collections/mlabonne/abliteration | Collection of abliterated models, including Qwen3, Gemma 3, and Llama 3.1 variants. |
| B | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/mlabonne/Qwen3-8B-abliterated | Qwen3 8B abliterated source model, Apache-2.0, experimental note. |
| C | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/bartowski/mlabonne_Qwen3-8B-abliterated-GGUF | GGUF quantized Qwen3 8B abliterated package with local runtime metadata. |
| D | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/dphn/Dolphin3.0-Llama3.1-8B-GGUF | Dolphin 3.0 Llama 3.1 8B GGUF package with local runtime metadata. |
| E | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/dphn/Dolphin-Mistral-24B-Venice-Edition | Dolphin Mistral 24B Venice Edition source model. |
| F | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/mlabonne/gemma-3-12b-it-abliterated-v2-GGUF | Gemma 3 12B abliterated v2 GGUF package. |
| G | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/mlabonne/Qwen3-30B-A3B-abliterated | Qwen3 30B-A3B abliterated source model, Apache-2.0. |
| H | Hugging Face model card | accessed 2026-06-05 | https://huggingface.co/mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated-GGUF | Llama 3.1 8B abliterated GGUF baseline. |

## Copied Notes Or Excerpts

### Source A

Public metadata reviewed: the collection title, updated date, abliterated model
theme, and listed model names/sizes for Gemma 3, Qwen3, and Llama 3.1 variants.

### Source B

Public metadata reviewed: Qwen3-8B-abliterated model name, Qwen3 family tags,
Apache-2.0 license, 8B size, abliterated metadata, experimental warning, and
the model-card note that the project studies refusal behavior.

### Source C

Public metadata reviewed: Qwen3-8B abliterated GGUF package name, Apache-2.0
license, GGUF tag, local runtime tags for llama.cpp/LM Studio/Ollama, and Q4/K
quant metadata for local testing.

### Source D

Public metadata reviewed: Dolphin3.0-Llama3.1-8B-GGUF model name, GGUF tag,
Llama 3.1 license, English/conversational tags, local runtime metadata, and
available quantized GGUF file classes.

### Source E

Public metadata reviewed: Dolphin-Mistral-24B-Venice-Edition model name,
Apache-2.0 license, Mistral 24B framing, Dolphin/Venice collaboration note, and
source page link to quantization options for local runtimes.

### Source F

Public metadata reviewed: Gemma 3 12B abliterated v2 GGUF model name, Gemma
license, GGUF metadata, image-text-to-text task metadata, and local runtime
metadata.

### Source G

Public metadata reviewed: Qwen3-30B-A3B-abliterated model name, Qwen3 MoE tags,
Apache-2.0 license, and abliterated metadata.

### Source H

Public metadata reviewed: Llama 3.1 8B abliterated GGUF model name, 8B size,
GGUF metadata, Llama architecture, quant size metadata, and collection link.

## Candidate Notes

### Candidate: Qwen3-8B-Abliterated-GGUF

| Field | Value |
| --- | --- |
| Candidate name from source | bartowski/mlabonne_Qwen3-8B-abliterated-GGUF |
| Model family | Qwen3 Abliterated |
| Provider or org | mlabonne / bartowski |
| Parameter count | 8B |
| Format or runtime | GGUF; local runtime metadata includes llama.cpp, LM Studio, and Ollama |
| Claimed context window | unknown from reviewed metadata |
| License | Apache-2.0 |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Strong first specialty target because the source provides 8B GGUF metadata and local runtime hints |
| Claimed strengths | Source frames it as an abliterated Qwen3 variant; source GGUF page marks several Q4/Q5/Q6 files as recommended for local use |
| Risks or caveats | Abliteration changes refusal behavior and is described as experimental; evaluate safety boundaries and coherence before use |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Run the local benchmark harness with normal prompts plus evaluator notes on refusals, uncertainty, and policy-boundary behavior. |

### Candidate: Dolphin3.0-Llama3.1-8B-GGUF

| Field | Value |
| --- | --- |
| Candidate name from source | dphn/Dolphin3.0-Llama3.1-8B-GGUF |
| Model family | Dolphin |
| Provider or org | Cognitive Computations / dphn |
| Parameter count | 8B |
| Format or runtime | GGUF; local runtime metadata includes llama.cpp, LM Studio, and Ollama |
| Claimed context window | unknown from reviewed metadata |
| License | Llama 3.1 |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Strong first Dolphin target because it is 8B and has a dedicated GGUF package |
| Claimed strengths | Source metadata frames Dolphin 3.0 as conversational/local-use oriented |
| Risks or caveats | Low-refusal behavior, Llama license terms, and stability must be reviewed before daily-driver use |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Run the local benchmark harness and compare against Qwen r2, with separate notes for refusals and instruction-following. |

### Candidate: gemma-3-12b-it-abliterated-v2-GGUF

| Field | Value |
| --- | --- |
| Candidate name from source | mlabonne/gemma-3-12b-it-abliterated-v2-GGUF |
| Model family | Gemma Abliterated |
| Provider or org | mlabonne |
| Parameter count | 12B |
| Format or runtime | GGUF; model-card metadata includes text/image task framing |
| Claimed context window | unknown from reviewed metadata |
| License | Gemma |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Plausible local candidate, but larger than the first 8B specialty targets |
| Claimed strengths | Source task metadata and collection placement make it interesting for text-plus-vision-adjacent local testing |
| Risks or caveats | Current benchmark harness is text-first; Gemma license terms and multimodal behavior need separate review |
| Suggested radar disposition | `watchlist` |
| Proposed local eval | Keep on watchlist until text-only versus multimodal eval scope is approved. |

### Candidate: Dolphin-Mistral-24B-Venice-Edition

| Field | Value |
| --- | --- |
| Candidate name from source | dphn/Dolphin-Mistral-24B-Venice-Edition |
| Model family | Dolphin / Mistral |
| Provider or org | Cognitive Computations / Venice AI |
| Parameter count | 24B in source name |
| Format or runtime | Source model; quantized local-runtime options need verification |
| Claimed context window | unknown from reviewed metadata |
| License | Apache-2.0 |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Potential high-capability specialty target, but local quant and RAM fit must be selected first |
| Claimed strengths | Source frames it as a Dolphin/Venice uncensored Mistral 24B collaboration |
| Risks or caveats | 256 GB RAM makes size acceptable; low-refusal behavior still needs license, stability, and safety review before daily-driver use |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Select an approved local quantized artifact first; then run the local benchmark harness as a specialty comparison. |

### Candidate: Qwen3-30B-A3B-Abliterated

| Field | Value |
| --- | --- |
| Candidate name from source | mlabonne/Qwen3-30B-A3B-abliterated |
| Model family | Qwen3 Abliterated |
| Provider or org | mlabonne |
| Parameter count | 30B-A3B / 31B-class in reviewed metadata |
| Format or runtime | Safetensors source; local quantization path to verify |
| Claimed context window | unknown from reviewed metadata |
| License | Apache-2.0 |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Potential high-quality specialty target if a practical local artifact exists |
| Claimed strengths | Source collection lists it as a recent Qwen3 abliterated model |
| Risks or caveats | 256 GB RAM makes size less concerning; avoid duplicate lineage with existing Qwen r2 and confirm exact runtime before a new run |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Choose a distinct local artifact or endpoint, then compare against the existing Qwen r2 result. |

### Candidate: Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF

| Field | Value |
| --- | --- |
| Candidate name from source | mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated-GGUF |
| Model family | Llama Abliterated |
| Provider or org | mlabonne |
| Parameter count | 8B |
| Format or runtime | GGUF |
| Claimed context window | unknown from reviewed metadata |
| License | Llama 3.1 |
| Local artifact status | Not installed or benchmarked in this repo |
| Hardware fit | Useful baseline because it is 8B with established GGUF quant metadata |
| Claimed strengths | Source frames it as an abliterated Llama 3.1 8B Instruct variant |
| Risks or caveats | Older base model and Llama license mean it should be a baseline, not the first specialty benchmark unless needed |
| Suggested radar disposition | `watchlist` |
| Proposed local eval | Use only as a baseline if newer Qwen or Dolphin specialty candidates produce ambiguous results. |

## Reviewer Notes

- Candidate records must follow `automations/ai-lab-radar/candidate-schema.md`.
- This packet approves candidate-only registry rows for the six listed models.
- Do not create dashboard scores or decisions until a real local benchmark run
  exists.
- Do not add install instructions unless the user separately asks for a local
  install plan.
- Treat source claims about low-refusal or uncensored behavior as risk signals
  to benchmark, not as quality scores.
