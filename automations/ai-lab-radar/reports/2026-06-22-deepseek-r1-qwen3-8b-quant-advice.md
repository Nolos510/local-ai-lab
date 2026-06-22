# Quantization Advice

Base repo: `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B`
Candidate: `20260605-deepseek-r1-0528-qwen3-8b`
Network lookup: `yes`

These recommendations are metadata hypotheses only. They do not approve a download, install, model run, or eval score.

| Recommendation | Runtime | Artifact repo | Quant | Fit | Approval | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| quality_check | LM Studio / Ollama / llama.cpp | lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q6_K | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Quality-first comparison quant that should be practical for 8B if local runtime support is confirmed. |
| quality_check | LM Studio / Ollama / llama.cpp | lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q8_0 | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Quality-first comparison quant that should be practical for 8B if local runtime support is confirmed. |
| fast_alternate | LM Studio / Ollama / llama.cpp | lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q4_K_M | fast_smaller | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Fast/smaller alternate for throughput checks or runtime compatibility triage. |
| recommended_balanced | LM Studio / Ollama / llama.cpp | bartowski/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-GGUF | Q5_K_M | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Balanced starting point for 8B on a 256 GB Apple Silicon target. |
| quality_check | LM Studio / Ollama / llama.cpp | bartowski/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-GGUF | Q6_K | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Quality-first comparison quant that should be practical for 8B if local runtime support is confirmed. |
| quality_check | LM Studio / Ollama / llama.cpp | bartowski/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-GGUF | Q8_0 | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Quality-first comparison quant that should be practical for 8B if local runtime support is confirmed. |
| fast_alternate | LM Studio / Ollama / llama.cpp | bartowski/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-GGUF | Q4_K_M | fast_smaller | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Fast/smaller alternate for throughput checks or runtime compatibility triage. |
| recommended_balanced | LM Studio / Ollama / llama.cpp | unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q5_K_M | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Balanced starting point for 8B on a 256 GB Apple Silicon target. |
| quality_check | LM Studio / Ollama / llama.cpp | unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q6_K | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Quality-first comparison quant that should be practical for 8B if local runtime support is confirmed. |
| quality_check | LM Studio / Ollama / llama.cpp | unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q8_0 | quality_first_practical | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Quality-first comparison quant that should be practical for 8B if local runtime support is confirmed. |
| fast_alternate | LM Studio / Ollama / llama.cpp | unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF | Q4_K_M | fast_smaller | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Fast/smaller alternate for throughput checks or runtime compatibility triage. |
| fast_alternate | LM Studio / Ollama / llama.cpp | unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF | UD-Q4_K_XL | fast_smaller | metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review | Fast/smaller alternate for throughput checks or runtime compatibility triage. |

Next benchmark step: register or select one exact local runtime model ID, complete source/license/provenance review, then use `uv run ai-lab bench execute` with explicit local-run approval.
