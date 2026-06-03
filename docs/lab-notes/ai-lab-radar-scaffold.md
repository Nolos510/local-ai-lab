# AI Lab Radar Scaffold

Date: 2026-06-03

## Context

An earlier automation attempt reported a read-only workspace and could not
create `automations/ai-lab-radar`. This session has workspace write access, so
the radar scaffold was added directly in the repository.

The reusable local LLM benchmark is already present under
`evals/local-llm-benchmark`, so there is no May 12 benchmark content to port in
this pass.

## What Changed

- Added `automations/ai-lab-radar/README.md`.
- Added `automations/ai-lab-radar/candidate-schema.md`.
- Added `automations/ai-lab-radar/templates/radar-report.md`.
- Added `data/model_registry/README.md`.
- Added this lab note.

## Safety Posture

- Documentation scaffold only.
- No model download logic.
- No cloud API calls.
- No web crawler or network client code.
- No new runtime dependencies.
- Radar output is treated as candidate review material, not an install request.

## Follow-Up

- Add a tiny candidate CSV or JSON normalizer only after the candidate schema has
  been used on real source notes.
- Connect ready-for-eval candidates to `evals/local-llm-benchmark` and
  `skills/local-llm-eval`.
- Keep private radar notes out of tracked files unless the user explicitly marks
  them safe to commit.
