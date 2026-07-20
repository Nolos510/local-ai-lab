# Evidence Disposition

Measured 2026-07-18 against `d345266 + preserved working-tree patch` after the
owner review pass and automatic evidence reconciliation. This report excludes
raw prompts, raw responses, credentials, tokens, and private filesystem paths.

## Current Authority

| State | Real runs | Meaning |
|---|---:|---|
| Confirmed | 23 | Authoritative score evidence across nine models |
| Valid draft or review pending | 3 | Eligible for independent review or human disposition |
| Rejected or quarantined | 10 | Preserved for audit and excluded from active rankings |
| Non-generative | 1 | BGE embedding evidence routed outside the LLM rubric |
| Ambiguously unscored | 0 | No run remains in an unexplained score state |

## Active Human Decisions

Only two artifacts currently require human judgment. Both contain valid primary
and independent score records whose metrics differ beyond the configured
thresholds:

- `20260621-qwen3-coder-30b-a3b-instruct-mlx-4bit-dashboard-test`
- `20260621-qwen3-coder-30b-a3b-instruct-mlx-4bit-dashboard-test-r2`

The review state `judge disagreement` means both score records are structurally
valid, but at least one label, metric, or total delta exceeds the configured
agreement threshold. It does not mean either judge is automatically wrong.

## Machine Review Pending

`20260625-gemma-4-12b-qat-dashboard-test` was repaired without rerunning its
model capture. The original all-zero primary score and later invalid reviewer
attempts are preserved under `score-attempts/`. The current primary draft is
nonzero and valid, but the configured independent reviewer did not satisfy the
structured score contract after bounded retries. It remains outside rankings
until a compatible independent reviewer succeeds.

## Quarantined Evidence

Seven generative artifacts are automatically quarantined with
`rerun_capture`. Their raw capture is missing or contains provider/runtime
errors:

- `20260625-mistral-dolphin-mix-cine-open-ne-nsfw-dashboard-test`
- `20260625-mistral-dolphin-mix-cine-open-ne-nsfw-dashboard-test-r2`
- `20260623-qwen3-coder-30b-a3b-instruct-mlx-4bit-dashboard-test`
- `20260625-qwen3-6-27b-obliteratus-dashboard-test`
- `20260625-qwen3-6-27b-obliteratus-dashboard-test-r2`
- `20260625-qwen3-6-35b-a3b-dashboard-test-r3`
- `20260717-qwen3-6-27b-obliteratus-dashboard-test`

Three owner-rejected generative artifacts remain audit-only and cannot be
reimported or confirmed:

- `20260625-mistral-dolphin-mix-cine-open-ne-nsfw-dashboard-test-r3`
- `20260717-gemma-4-12b-qat-dashboard-test`
- `20260717-mistral-dolphin-mix-cine-open-ne-nsfw-dashboard-test`

`20260717-bge-m3-latest-dashboard-test` is classified as embedding evidence and
is excluded from generative scoring. It requires the future retrieval benchmark
instead of an LLM rescore.

## Workflow Contract

1. Structurally invalid, all-zero, role-mismatched, or failed-capture evidence
   is quarantined automatically and never asks the owner for confirmation.
2. Prior judge attempts and raw captures remain on disk for audit.
3. Automated score and reviewer repair is bounded; repeated invalid output is
   routed to a different reviewer or fresh capture rather than an infinite loop.
4. Only valid judge agreement or disagreement reaches the human review queue.
5. Rejected evidence cannot return to rankings through startup or manual import.
6. A confirmed score and a portfolio keep/watch/retest/remove decision remain
   separate authorities.

## Remaining Exit Work

- Disposition the two valid Qwen judge disagreements.
- Obtain a compatible independent review for the repaired Gemma draft.
- Run fresh captures for the seven automatic `rerun_capture` artifacts only when
  their models remain worth testing.
- Add retrieval-specific evidence for BGE-M3.
- Rerun or re-import seven confirmed runs missing throughput or peak RAM.
- Backfill or rerun 24 runs missing complete run configuration.
- Record portfolio decisions for seven confirmed models that still lack one.
