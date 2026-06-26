# v1 Release Checklist

Date opened: 2026-06-05
Last updated: 2026-06-25

## Goal

Ship AI Lab OS v1 as a local product loop:

```text
candidate -> benchmark artifact -> raw responses -> scores -> dashboard import -> decision
```

## Branch Baseline

- [x] `main` is the local working branch.
- [x] `origin/main` and `origin/master` were aligned before v1 work began.
- [x] v1 commits through `4cccb2a` are pushed to `origin/main`.
- [x] Dashboard IA work was landed on `main` through `7d90256`.
- [x] Final Dolphin release commit is the `origin/main` push target.
- [x] `v1.0.0` release tag target is the final validated Dolphin release
  commit.

## Candidate Approval

- [x] Do not benchmark `Qwen3-30B-A3B-Abliterated` unless a matching local
  artifact or endpoint exists.
- [x] Register separate vanilla candidate:
  `20260605-qwen3-30b-a3b-instruct-lmstudio`.
- [x] Keep the abliterated Qwen3 30B candidate on watchlist until runtime
  identity is confirmed.
- [x] Confirm the exact LM Studio id for the installed Qwen3 Coder artifact:
  `qwen3-coder-30b-a3b-instruct-mlx`.
- [x] Confirm vanilla `Qwen3-30B-A3B-Instruct` is not installed or visible in
  `lms ls --json` / `lms ps --json`; keep it unscored.
- [x] Approve Dolphin-Mistral 24B for benchmark execution against the exact
  already-local LM Studio CLI id `dolphin-mistral-24b-venice-edition`.
- [x] Keep Dolphin-Mistral 24B unapproved for reinstall, update, alternate
  artifact selection, or download.

## Benchmark Capture

- [x] Preserve Qwen3 Coder CLI retest `raw_responses.jsonl`.
- [x] Preserve Qwen3 Coder CLI retest `evidence.md`.
- [x] Do not create scores from runtime inventory or radar claims.
- [x] Run a second unique model benchmark only after the target model is
  installed/indexed/loaded and has exact local runner metadata.
- [x] Use `20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2` as
  the official second benchmark source.
- [x] Preserve earlier Dolphin run only as repeatability context; do not average
  official scores until an aggregation feature exists.

## Draft And Confirmed Scoring

- [x] Create `draft-scores.json` only from a separate local judge model, if one
  is available. Live Dolphin draft scoring was skipped because the loopback LM
  Studio endpoint returned `401 Unauthorized` and no separate judge token was
  provided.
- [x] Human-review Qwen3 Coder CLI run against raw responses.
- [x] Write confirmed Qwen3 Coder CLI `scores.json`.
- [x] Write Qwen3 Coder CLI `decision.json`.
- [x] Export confirmed Qwen3 Coder CLI dashboard CSVs.
- [x] Repeat confirmed scoring for one second unique model:
  `Dolphin-Mistral-24B-Venice-Edition`.

## Dashboard Loop

- [x] `/radar` links candidate records to source/report/artifact/import state.
- [x] `/artifacts/<run_id>` links artifacts to candidate context and imported
  dashboard model/decision state.
- [x] `/runs` links imported runs back to benchmark artifacts.
- [x] `/models/<id>` links run history back to benchmark artifacts.
- [x] `/lab` shows candidate, artifact, import, and decision state.
- [x] Dolphin r2 imports resolve through `/radar`, `/specialty`, `/runs`,
  `/compare`, `/models/<id>`, `/artifacts/<run_id>`, and `/lab`.

## Portfolio Package

- [x] Add v1 portfolio case study.
- [x] Add resume bullet draft.
- [x] Add learning roadmap tied to the project.
- [x] Add architecture diagram.
- [x] Capture dashboard screenshots for lab, radar, projects, and reports.

## Local-First Guardrails

- [x] No model downloads were added.
- [x] No cloud/API SDKs were added.
- [x] No secrets were committed.
- [x] No tracked SQLite runtime database was added.
- [x] Candidate records remain separate from eval scores.
- [x] Raw Dolphin response artifacts remain local/ignored and are represented in
  Git only by sanitized validation evidence.

## Validation Gate

- [x] `python3 -m unittest discover -s apps/model-dashboard/tests`
- [x] `python3 -m unittest discover -s evals/local-llm-benchmark/tests`
- [x] `python3 scripts/model_dashboard_smoke.py`
- [x] `uv run pytest`
- [x] `uv run ruff check .`
- [x] If a confirmed benchmark exists, import it into a temp DB and generate a
  report.
