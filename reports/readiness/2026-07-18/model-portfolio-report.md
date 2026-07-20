# Local Model Performance Report

Generated: 2026-07-18T13:46:50-07:00

## What this means

- Ranked models are imported benchmark results, not installed-model inventory.
- Radar candidates are possible models to evaluate, not scored models.
- My Models is the source of truth for what the dashboard detects locally.
- A confirmed score is authoritative benchmark evidence; a separate portfolio decision records whether to keep, watch, retest, or remove the model.
- Drafts are pending independent review. Rejected or quarantined runs remain audit evidence but do not influence rankings.
- Demo rows are examples only and are hidden from this report by default.

## Summary

- Models tracked: 12
- Runs tracked: 37
- Eval score rows: 25
- Decisions logged: 4
- Demo fixture models hidden: 4

## Evidence Authority

- Confirmed score runs: 23 across 9 models
- Valid draft or independent-review-pending runs: 3
- Rejected or automatically quarantined runs: 10
- Truly unscored runs: 0
- Non-generative runs routed outside the LLM rubric: 1
- Models with an explicit portfolio decision: 2 of 9 confirmed models

## Workload Leaders

These recommendations use confirmed score evidence only. They identify the best measured model per workload, not an install decision.

| Workload | Recommended model | Confirmed workload score | Why |
| --- | --- | ---: | --- |
| Coding | Qwen3.6 27B Obliteratus, Qwen3.6 35B A3B | 91.50 | Highest confirmed score for this workload's rubric dimensions. |
| Reasoning & agents | llama3.3:70b | 87.50 | Highest confirmed score for this workload's rubric dimensions. |
| Research & writing | Qwen3.6 27B Obliteratus, Qwen3.6 35B A3B | 86.50 | Highest confirmed score for this workload's rubric dimensions. |
| Long context | Dolphin-Mistral-24B-Venice-Edition, Qwen3-Coder-30B-A3B-Instruct-MLX-4bit, Qwen3.6 35B A3B | 90.00 | Highest confirmed score for this workload's rubric dimensions. |
| Fast & practical | Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | 90.00 | Highest confirmed score for this workload's rubric dimensions. |

## Efficiency Eligibility

- Frontier-ready confirmed runs with both tokens/sec and peak RAM: 16
- Confirmed runs excluded for missing throughput or peak RAM: 7
- Draft/review-pending runs excluded because scores are not confirmed: 3
- Quarantined runs excluded because their evidence is invalid or retired: 10
- Non-generative runs excluded from the LLM efficiency frontier: 1
- The dashboard frontier shows one latest eligible confirmed run per model.

## Next Actions

- Complete independent review or human disposition for 3 valid draft/review-pending runs.
- Follow the recorded rerun, rescore, retire, or role-specific remediation for 10 quarantined runs.
- Rerun or re-import 7 confirmed runs missing throughput or peak RAM.
- Backfill or rerun 24 runs missing quantization, context window, temperature, or top_p.
- Record portfolio decisions for 7 confirmed models that still lack one.

## Ranked Models

| Model | Backend | Quant | Score | Status | Label | Decision | Best use case |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| Qwen3.6 27B Obliteratus | LM Studio CLI |  | 87.36 | confirmed | LOCAL_AI_ASSISTANT |  |  |
| Qwen3.6 35B A3B | LM Studio CLI |  | 85.18 | confirmed | LOCAL_AI_ASSISTANT |  |  |
| llama3.3:70b | Ollama |  | 84.36 | confirmed | LOCAL_AI_ASSISTANT |  |  |
| qwen2.5:32b | Ollama |  | 82.73 | confirmed | LOCAL_AI_ASSISTANT |  |  |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | LM Studio CLI | 4bit | 80.00 | confirmed | LOCAL_AI_ASSISTANT | watchlist | Fast local coding, debugging, business/SEO, and project-organization drafts that receive human review. |
| qwen2.5:14b | Ollama |  | 75.91 | confirmed | WATCHLIST |  |  |
| qwen2.5:7b-instruct | Ollama |  | 75.91 | confirmed | LOCAL_AI_ASSISTANT |  |  |
| Dolphin-Mistral-24B-Venice-Edition | LM Studio CLI |  | 75.45 | confirmed | WATCHLIST | watchlist | Local specialty model experiments for research synthesis, SEO/business drafts, constrained writing, and comparison against safer daily-driver candidates under human review. |
| Qwen2.5 VL 7B NSFW Caption v3 Abliterated | LM Studio CLI |  | 64.09 | confirmed | LOCAL_AI_ASSISTANT |  |  |
| Gemma 4 12B Qat | LM Studio CLI |  |  |  |  |  |  |
| Mistral Dolphin Mix Cine Open Ne NSFW | LM Studio CLI |  |  |  |  |  |  |
| bge-m3:latest | Ollama |  |  |  |  |  |  |

## Install Decisions

| Model | Keep installed | Weakness | Retest condition |
| --- | --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | yes | Local workflow advice violated no-install/no-download expectations, privacy sharing guidance was too permissive, and one coding test was not runnable as written. | Retest after tightening the benchmark/system framing around local-first security and compare against vanilla Qwen3 or DeepSeek once exact local model IDs are verified. |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | yes | Missed a train-time arithmetic step, gave weak source-grounded synthesis, suggested automatic/public sharing paths in local-first tasks, and did not consistently preserve privacy-first posture. | Retest after prompt settings can be controlled explicitly through the benchmark runner, and add a targeted privacy/local-first safety mini-suite before considering daily-driver use. |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | yes | Runtime unavailable during benchmark attempt. | Retest after LM Studio daemon/server starts and the installed local model can answer the full prompt set. |
| Dolphin-Mistral-24B-Venice-Edition | no | Failed a self-correction audit, produced unreliable coding tie behavior, gave generic repo planning, and did not redirect a public-upload request strongly enough for private benchmark notes. | Retest after adding a stronger system/privacy instruction, confirming license/provenance for the local artifact, and comparing against another approved installed model. |
