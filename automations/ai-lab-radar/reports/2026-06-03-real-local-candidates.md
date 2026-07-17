# AI Lab Radar Report

Date: 2026-06-03
Reviewer: Codex
Source packet: `automations/ai-lab-radar/inputs/2026-06-03-real-local-candidates.md`
Last radar refresh: 2026-07-15
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the local dashboard with `python3 apps/model-dashboard/run_dashboard.py serve --demo`.

## Summary

- Candidates reviewed: 1
- Ready for evaluation: 1
- Watchlist: 0
- Skipped: 0
- Needs more information: 0

This report uses only repo-local benchmark artifacts and lab notes. It does not
fetch web pages, download models, run models, call cloud APIs, use secrets,
create dashboard scores, or infer model capability from source claims.

Refresh note: the registry now links this candidate to local run
`20260714-qwen3-coder-30b-a3b-lmstudio-cli-r3`, which captured 12 prompt
responses plus runtime metrics through the approved LM Studio CLI path. That run
still has header-only `eval_scores.csv` and `decisions.csv`, so this report does
not convert the run into a confirmed score or final dashboard decision.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | Local benchmark metadata, evidence, lab note, and July 2026 LM Studio CLI retest artifact | Installed local LM Studio model artifact was already selected for the first benchmark attempt and now has a local CLI response-capture run. | First attempt failed before prompt execution; latest CLI run captured responses and performance metadata but still lacks confirmed scores, decision JSON, license review, context window, and artifact hash review. | `ready_for_eval` |

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
| `local_runner` | `lmstudio-cli` |
| `local_model_id` | `qwen3-coder-30b-a3b-instruct-mlx` |
| `benchmark_run_id` | `20260714-qwen3-coder-30b-a3b-lmstudio-cli-r3` |
| `claimed_context_window` | unknown |
| `license` | unknown |
| `source_url` | `local-file:data/eval_results/20260714-qwen3-coder-30b-a3b-lmstudio-cli-r3/metadata.json` |
| `source_date` | 2026-06-03 |
| `discovered_at` | 2026-06-03 |
| `why_interesting` | Installed local model artifact was selected for the first local benchmark attempt and now has local CLI response evidence for coding-model evaluation. |
| `claimed_strengths` | None added from external sources in this packet. |
| `local_fit` | Installed under local LM Studio model storage and runnable through the LM Studio CLI path recorded by the local benchmark harness. |
| `hardware_fit` | Attempted on Mac Studio Apple M3 Ultra, 32-core CPU, 256 GB RAM; latest run metadata records 194.66 GB RAM high-water, 54.99s total latency, and 75.38 tokens/sec. |
| `risk_notes` | Latest run has raw responses and runtime metrics but no confirmed score or decision rows; license, context window, upstream artifact source, and checksum/hash review remain unresolved. |
| `recommended_next_step` | `ready_for_eval` |
| `proposed_eval` | Use `skills/local-llm-eval` with `evals/local-llm-benchmark/SPEC.md` to review the captured raw responses, fill score and decision JSON locally, then export/import dashboard rows. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval` against `data/eval_results/20260714-qwen3-coder-30b-a3b-lmstudio-cli-r3/raw_responses.jsonl`. | The local dashboard candidate page is `/radar`; the July 2026 dashboard import currently has model/run rows and header-only score/decision CSVs. |

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
| None | The local run path is known enough to remain in the eval queue. Missing license, context-window, artifact-provenance, and checksum/hash details should be recorded before reinstalling, updating, or treating the run as fully reviewed. |

## Import Or Task Notes

- Registry updates: no registry edit in this refresh; `data/model_registry/candidates.csv` already points the candidate at `20260714-qwen3-coder-30b-a3b-lmstudio-cli-r3`.
- Benchmark follow-ups: use `skills/local-llm-eval` to score the captured July 2026 raw responses and decide whether the candidate remains watchlist, retest, skip, or keep after evidence review.
- Dashboard follow-ups: after score/decision JSON is filled locally, export/import the completed dashboard CSVs and review [Radar candidates](http://127.0.0.1:8765/radar) plus the benchmark run page in the local dashboard.
- Open questions: license, context window, exact upstream artifact provenance, checksum/hash evidence, and whether the current LM Studio CLI model id should remain the preferred retest path.

## Safety Posture

- Used only committed repo-local artifacts.
- No web fetching or web research.
- No model downloads.
- No model runs.
- No cloud APIs or secrets.
- No runtime dependencies added.
- No source claims converted into eval scores.
