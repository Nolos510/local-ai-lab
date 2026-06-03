# AI Lab Radar Report

Date: 2026-06-03
Reviewer: Codex
Source packet: `automations/ai-lab-radar/inputs/2026-06-03-real-local-candidates.md`

## Summary

- Candidates reviewed: 1
- Ready for evaluation: 1
- Watchlist: 0
- Skipped: 0
- Needs more information: 0

This report uses only repo-local benchmark artifacts and lab notes. It does not
fetch web pages, download models, run models, call cloud APIs, use secrets,
create dashboard scores, or infer model capability from the failed runtime
attempt.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | Local benchmark metadata, evidence, and lab note | Installed local LM Studio model artifact was already selected for the first benchmark attempt on Mac Studio hardware. | LM Studio daemon/server failed before prompt execution. No model responses, scores, final label, context window, or license are established. | `ready_for_eval` |

## Candidate Records

### Qwen3-Coder-30B-A3B-Instruct-MLX-4bit

| Field | Value |
| --- | --- |
| `candidate_id` | `20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit` |
| `model_name` | Qwen3-Coder-30B-A3B-Instruct-MLX-4bit |
| `model_family` | Qwen |
| `provider_or_org` | lmstudio-community local artifact |
| `params_b` | 30 |
| `format_or_runtime` | MLX through LM Studio |
| `claimed_context_window` | unknown |
| `license` | unknown |
| `source_url` | `local-file:data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/metadata.json` |
| `source_date` | 2026-06-03 |
| `discovered_at` | 2026-06-03 |
| `why_interesting` | Installed local model artifact was selected for the first local benchmark attempt and is relevant for coding-model evaluation. |
| `claimed_strengths` | None added from external sources in this packet. |
| `local_fit` | Installed under local LM Studio model storage and attempted through LM Studio on Mac Studio hardware. |
| `hardware_fit` | Attempted on Mac Studio Apple M3 Ultra, 32-core CPU, 256 GB RAM. |
| `risk_notes` | Runtime unavailable during first attempt; no prompt output captured; no eval score exists; license and context window unknown. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Start LM Studio local server, confirm `127.0.0.1:1234/v1/models` responds or record the actual local endpoint, then rerun the local LLM benchmark prompt set. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | `evals/local-llm-benchmark/SPEC.md` via `evals/local-llm-benchmark/harness.py` and `skills/local-llm-eval`. | Preserve the prior failed-runtime attempt as a `retest` record. Create a new `-r2` benchmark run only after the local server is reachable. |

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| None | No candidate was assigned to watchlist in this packet. | Not applicable. |

## Skips

| Candidate | Reason |
| --- | --- |
| None | No supplied candidate clearly warrants `skip`. |

## Needs More Information

| Candidate | Missing information |
| --- | --- |
| None | Runtime is blocked, but the local artifact is known enough to remain in the eval queue. Missing license/context details should be recorded during retest setup. |

## Import Or Task Notes

- Registry updates: none in this pass.
- Benchmark follow-ups: fix LM Studio runtime and create a `20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit-r2` run.
- Dashboard follow-ups: no new dashboard import until the retest produces responses and score/decision JSON.
- Open questions: license, context window, exact local server endpoint if not `127.0.0.1:1234`, and whether LM Studio or another backend should be the preferred retest path.

## Safety Posture

- Used only committed repo-local artifacts.
- No web fetching or web research.
- No model downloads.
- No model runs.
- No cloud APIs or secrets.
- No runtime dependencies added.
- No source claims converted into eval scores.
