# v1 Release Checklist

Date opened: 2026-06-05

## Goal

Ship AI Lab OS v1 as a local product loop:

```text
candidate -> benchmark artifact -> raw responses -> scores -> dashboard import -> decision
```

## Branch Baseline

- [x] `main` is the local working branch.
- [x] `origin/main` and `origin/master` were aligned before v1 work began.
- [ ] v1 commits are pushed to `origin/main`.
- [ ] Optional: tag the validated v1 release.

## Candidate Approval

- [x] Do not benchmark `Qwen3-30B-A3B-Abliterated` unless a matching local
  artifact or endpoint exists.
- [x] Register separate vanilla candidate:
  `20260605-qwen3-30b-a3b-instruct-lmstudio`.
- [x] Keep the abliterated Qwen3 30B candidate on watchlist until runtime
  identity is confirmed.
- [ ] Confirm the exact LM Studio endpoint model id for
  `Qwen3-30B-A3B-Instruct`.

## Benchmark Capture

- [ ] Confirm authorized local endpoint access to
  `http://127.0.0.1:1234/v1/models`.
- [ ] Run `20260605-qwen3-30b-a3b-instruct-lmstudio-r1` only after the exact
  model id is visible.
- [ ] Preserve `raw_responses.jsonl`.
- [ ] Preserve `evidence.md`.
- [ ] Do not create scores from runtime inventory or radar claims.

## Draft And Confirmed Scoring

- [ ] Create `draft-scores.json` only from a separate local judge model, if one
  is available.
- [ ] Human-review draft scores against raw responses.
- [ ] Write confirmed `scores.json`.
- [ ] Write `decision.json`.
- [ ] Export confirmed dashboard CSVs.

## Dashboard Loop

- [x] `/radar` links candidate records to source/report/artifact/import state.
- [x] `/artifacts/<run_id>` links artifacts to candidate context and imported
  dashboard model/decision state.
- [x] `/runs` links imported runs back to benchmark artifacts.
- [x] `/models/<id>` links run history back to benchmark artifacts.
- [x] `/lab` shows candidate, artifact, import, and decision state.

## Local-First Guardrails

- [x] No model downloads were added.
- [x] No cloud/API SDKs were added.
- [x] No secrets were committed.
- [x] No tracked SQLite runtime database was added.
- [x] Candidate records remain separate from eval scores.

## Validation Gate

- [x] `python3 -m unittest discover -s apps/model-dashboard/tests`
- [x] `python3 -m unittest discover -s evals/local-llm-benchmark/tests`
- [x] `python3 scripts/model_dashboard_smoke.py`
- [x] `uv run pytest`
- [x] `uv run ruff check .`
- [x] If a confirmed benchmark exists, import it into a temp DB and generate a
  report.
