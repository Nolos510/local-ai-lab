# Local Qwen3 30B LM Studio Candidate Report

Date: 2026-06-05
Reviewer: Codex
Source packet:
`automations/ai-lab-radar/inputs/2026-06-05-local-qwen3-30b-instruct-lmstudio.md`

## Summary

The user clarified that the visible LM Studio model appears to be
`Qwen3-30B-A3B-Instruct`, not an abliterated model. This report registers that
as a separate vanilla Qwen3 candidate while keeping the existing abliterated
Qwen3 30B radar candidate on watchlist until a matching local artifact exists.

## Candidate Review

| Candidate | Status | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| `Qwen3-30B-A3B-Instruct` | `ready_for_eval` | Large non-abliterated Qwen3 comparison point for the 256 GB RAM lab. | Exact local endpoint model id is not yet confirmed; CLI inventory currently exposes only `qwen3-coder-30b-a3b-instruct-mlx`. | Confirm exact endpoint id, then run `20260605-qwen3-30b-a3b-instruct-lmstudio-r1`. |
| `Qwen3-30B-A3B-Abliterated` | `watchlist` | Potential specialty/low-refusal Qwen3 lane candidate. | Not currently visible in local LM Studio inventory. | Do not benchmark until a matching local artifact or endpoint exists. |

## Disposition

- `Qwen3-30B-A3B-Instruct`: `ready_for_eval`
- `Qwen3-30B-A3B-Abliterated`: `watchlist`

## Import Rules

- Candidate records are not scores.
- Runtime inventory checks are not benchmark evidence.
- No dashboard score or decision should be created until raw responses,
  confirmed scores, and a decision artifact exist for the proposed run.

## Local-First Check

No model downloads, cloud APIs, API SDKs, external model calls, or secrets were
added. The local endpoint returned `401 Unauthorized`, so no raw prompt capture
was attempted for the unresolved vanilla model.
