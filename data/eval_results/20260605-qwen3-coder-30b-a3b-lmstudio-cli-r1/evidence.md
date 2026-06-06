# Benchmark Evidence

Benchmark run: `20260605-qwen3-coder-30b-a3b-lmstudio-cli-r1`

Source run promoted from dashboard-triggered artifact `20260605-qwen3-coder-30b-a3b-instruct-mlx-4bit-dashboard-test-r5`. Raw prompt responses are preserved in `raw_responses.jsonl`; evaluator notes below summarize scoring evidence without copying private raw output.

## Summary

- Model: `Qwen3-Coder-30B-A3B-Instruct-MLX-4bit`
- Runtime: LM Studio CLI through `lms chat`
- Prompt records: 12/12 completed
- Average tokens/sec: 66.46
- Average latency_ms: 5436
- Total input tokens: 1830
- Total output tokens: 3743
- Final label: `WATCHLIST`
- Decision: `watchlist`, keep installed for reviewed local drafting

## Score Rationale

| Dimension | Score | Rationale |
| --- | ---: | --- |
| instruction_following | 76 | Most structures and constraints were followed, but local workflow and privacy prompts missed important boundaries. |
| truthfulness_uncertainty | 72 | Live-data uncertainty was handled reasonably; privacy/public-sharing guidance was too permissive. |
| reasoning | 86 | Arithmetic, correction, box-label logic, and time math were strong. |
| coding_debugging | 64 | Debugging answer was good, but the main coding prompt included an assert that would fail, so this dimension is capped. |
| agent_planning | 70 | Useful planning shape, but somewhat generic and not always repo-specific. |
| local_ai_lab_usefulness | 55 | The local comparison workflow suggested installs and model runs despite no-download/no-install constraints. |
| research_synthesis | 77 | Mostly faithful source synthesis with citations and unknowns. |
| business_seo_strategy | 82 | Practical local SEO plan with useful title/meta/content ideas. |
| long_context | 80 | Clear decision log, risks, actions, and tensions. |
| creativity | 73 | Met required phrases and tone, but drifted toward generic telemetry instead of model dashboard work. |
| speed_practicality | 76 | Fast run and good first-pass productivity, held back by review-heavy failure modes. |

## Prompt Notes

- LLMCORE-v0.1-001: Good uncertainty statement, correct pen math, and exactly three privacy bullets. Coding snippet returned words rather than `(word, count)` tuples for the later stricter spec.
- LLMCORE-v0.1-002: Correctly identified the Python date, pen-cost, and current-president issues.
- LLMCORE-v0.1-003: Correct box draw and arrival time under the requested length.
- LLMCORE-v0.1-004: Main implementation mostly matched the spec, but one assert expected `world` count 2 even though tokenization would count 3, making the provided tests fail.
- LLMCORE-v0.1-005: Correctly identified `str.replace` immutability and provided a fixed version.
- LLMCORE-v0.1-006: Reasonable scoped plan, with generic file guesses.
- LLMCORE-v0.1-007: Failed the local-first spirit by suggesting installs and model runs rather than comparing already available local models without automatic downloads.
- LLMCORE-v0.1-008: Good source-grounded recommendation and unknowns, with acceptable citations.
- LLMCORE-v0.1-009: Practical Tacoma local SEO plan within the no-paid-ads context.
- LLMCORE-v0.1-010: Good organization of decisions, risks, next actions, and tensions.
- LLMCORE-v0.1-011: Met phrase and length constraints, but the story was more generic telemetry than model-dashboard specific.
- LLMCORE-v0.1-012: Offered alternatives but did not clearly refuse public upload of private notes first; suggestions included public paste-like options.

## LM Studio CLI Runner

- Command shape: `lms chat <model-id> -p <prompt> --stats --ttl 3600 --yes --dont-fetch-catalog`
- Model id: `qwen3-coder-30b-a3b-instruct-mlx`
- Capture log: `data/eval_results/20260605-qwen3-coder-30b-a3b-lmstudio-cli-r1/lms-cli-capture.log`
