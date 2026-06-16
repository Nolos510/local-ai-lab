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
- [x] v1 commits through `4cccb2a` are pushed to `origin/main`.
- [ ] Optional: tag the validated v1 release.

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
- [ ] Keep Dolphin-Mistral 24B queued until a concrete local artifact and exact
  runtime id are visible.

## Benchmark Capture

- [x] Preserve Qwen3 Coder CLI retest summaries; omit raw response files from
  the GitHub copy.
- [x] Preserve Qwen3 Coder CLI retest `evidence.md`.
- [x] Do not create scores from runtime inventory or radar claims.
- [ ] Run a second unique model benchmark only after the target model is
  installed/indexed/loaded and has exact local runner metadata.
- [x] Queue second benchmark target instead of creating a fake artifact when
  LM Studio/Ollama inventory checks did not return an exact runnable model.

## Draft And Confirmed Scoring

- [ ] Create `draft-scores.json` only from a separate local judge model, if one
  is available.
- [x] Human-review Qwen3 Coder CLI run against raw responses.
- [x] Write confirmed Qwen3 Coder CLI `scores.json`.
- [x] Write Qwen3 Coder CLI `decision.json`.
- [x] Export confirmed Qwen3 Coder CLI dashboard CSVs.
- [ ] Repeat confirmed scoring for one second unique model.

## Dashboard Loop

- [x] `/radar` links candidate records to source/report/artifact/import state.
- [x] `/artifacts/<run_id>` links artifacts to candidate context and imported
  dashboard model/decision state.
- [x] `/runs` links imported runs back to benchmark artifacts.
- [x] `/models/<id>` links run history back to benchmark artifacts.
- [x] `/lab` shows candidate, artifact, import, and decision state.

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

## Validation Gate

- [x] `python3 -m unittest discover -s apps/model-dashboard/tests`
- [x] `python3 -m unittest discover -s evals/local-llm-benchmark/tests`
- [x] `python3 scripts/model_dashboard_smoke.py`
- [x] `uv run pytest`
- [x] `uv run ruff check .`
- [x] If a confirmed benchmark exists, import it into a temp DB and generate a
  report.
