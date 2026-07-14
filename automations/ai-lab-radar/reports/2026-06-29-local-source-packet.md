# AI Lab Radar Report

Date: 2026-06-30
Reviewer: Codex automation
Source packet: `automations/ai-lab-radar/inputs/2026-06-29-local-source-packet.md`

## Summary

- Candidates reviewed: 2 model candidates and 1 project-registry item
- Ready for evaluation: 2 model candidates
- Watchlist: 0
- Skipped: 0
- Needs more information: 0
- Dashboard link: [apps/model-dashboard](../../../apps/model-dashboard)

This run used only the approved repo-local source packet and existing
repo-local registry, benchmark, and security-review evidence. No web pages were
fetched, no repositories were cloned, no models were downloaded or run, no APIs
or secrets were used, and no dashboard scores or decisions were created.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | Existing `data/model_registry/candidates.csv` row plus `automations/ai-lab-radar/inputs/2026-06-03-real-local-candidates.md` | Already-local LM Studio MLX artifact with prior benchmark and retest evidence; useful as a current local coding/research comparison baseline. | License review remains `needs_review`; local inventory approval does not approve reinstall, update, mirror, or alternate artifacts. Prior retest notes include workflow-advice and privacy-guidance concerns. | `ready_for_eval` for controlled retest/comparison only. |
| Dolphin-Mistral-24B-Venice-Edition | Existing `data/model_registry/candidates.csv` row plus `automations/ai-lab-radar/security-reviews/2026-06-05-dolphin-mistral-24b-venice-edition.md` | Already-local LM Studio artifact with exact local model id; plausible specialty 24B candidate for local comparison. | Low-refusal/uncensored framing needs safety, stability, and license review before daily-driver use. Approval is limited to the exact local LM Studio id. | `ready_for_eval` for explicit local-run approval through LM Studio CLI. |

## Ready For Eval

| Candidate | Proposed benchmark | Dashboard notes |
| --- | --- | --- |
| Qwen3-Coder-30B-A3B-Instruct-MLX-4bit | Run `evals/local-llm-benchmark/SPEC.md` via `skills/local-llm-eval` only after exact local model id and security gate approval are verified. | Use existing candidate row and local benchmark artifact lineage; do not change dashboard scores from this packet alone. |
| Dolphin-Mistral-24B-Venice-Edition | Run `evals/local-llm-benchmark/SPEC.md` via `skills/local-llm-eval` through LM Studio CLI after explicit local-run approval. | The registry row now points proposed eval wording at `skills/local-llm-eval`; no score or final decision was created. |

## Project Scope Note

| Project | Registry scope | Radar action |
| --- | --- | --- |
| llama.cpp | `data/project_registry`, not `data/model_registry` | Keep as a runtime integration review candidate. Do not turn this project row into a model eval score, model registry row, or dashboard model decision. |

## Import Or Task Notes

- Registry updates: tightened the Dolphin-Mistral proposed eval wording to
  explicitly reference `skills/local-llm-eval`.
- Benchmark follow-ups: choose one ready-for-eval local candidate and prepare a
  local benchmark run under `data/eval_results/<benchmark_run_id>/` using
  `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`.
- Dashboard follow-ups: if a benchmark run is completed later, export
  dashboard CSVs through the local harness and validate with
  `python3 scripts/model_dashboard_smoke.py`.
- Open questions: license review remains unresolved for both local artifacts;
  no reinstall, update, alternate artifact, or download is approved by this
  report.
