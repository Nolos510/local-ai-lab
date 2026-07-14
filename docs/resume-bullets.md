# AI Lab OS Resume Bullets

Use these as source material. Pick the bullets that match the role and keep the
claims aligned with the current repository state.

## One-Line Summary

- Built AI Lab OS, a local-first Apple Silicon AI evaluation workflow for model
  discovery, security review, benchmark evidence, dashboard comparison, and
  keep/watchlist/retest/skip decisions.

## Software Engineering

- Designed and implemented a dependency-light Python dashboard using stdlib HTTP
  serving, SQLite, CSV import/export, inline SVG charts, and route/action tests
  for local AI benchmark review.
- Delivered a dark "Midnight Neon" dashboard redesign with a collapsible
  sidebar, offline icon set, inline SVG charts, and no external dashboard assets.
- Consolidated 11 dashboard navigation destinations into four workflow surfaces
  (Home, Discover, My Models, and Benchmark) while retaining stable detail
  routes and local-only behavior.
- Built a dependency-free Fit Advisor that labels parameter/quantization-based
  memory estimates, preserves unknown states, incorporates sanitized machine
  memory, and distinguishes observed benchmark throughput from estimated fit.
- Built confirmed-score-only task leader views across five practical task groups
  with deterministic ties, no panel when confirmed evidence is absent, and an
  honest single-model warning; current comparative evidence remains limited to
  two confirmed models.
- Built a unified `ai-lab` CLI for repo-local lab operations including status,
  radar listing, sanitized hardware snapshots, benchmark matrix planning,
  approval-gated benchmark execution, benchmark artifact prep, dashboard
  import/report, and dashboard launch.
- Added an approval-gated batch benchmark queue that enumerates exact local model
  ids, runners, and run ids before execution, refuses incomplete batches, keeps
  later runs moving after a per-model failure, and emits a final result summary.
- Added a read-only dashboard capability view that summarizes hardware profile
  examples, candidate readiness, benchmark artifact counts, score/run signals,
  performance signals, and next benchmark commands without runtime network
  calls.
- Implemented installed-model inventory handling for LM Studio and Ollama that
  distinguishes loaded, indexed, filesystem-only, registered, unregistered, and
  ambiguous model states.
- Added a disabled-by-default, recoverable model removal path that sends LM
  Studio folders to macOS Trash, calls `ollama rm` for Ollama, and rejects
  out-of-root filesystem targets.
- Maintained a full validation gate covering dashboard and benchmark unittests,
  dashboard smoke, repo-wide pytest, and Ruff lint.

## AI / Evaluation Engineering

- Built a local benchmark artifact workflow that preserves raw responses,
  evidence notes, score templates, confirmed scores, decisions, and dashboard
  CSV imports for reproducible model evaluation.
- Completed confirmed local benchmark imports for Qwen3 Coder and
  Dolphin-Mistral 24B, including preserved raw-response evidence, performance
  metadata, score status, and keep/watchlist decision records.
- Measured local BGE-M3 retrieval at `recall@5 = 1.0` and `MRR = 1.0` on a
  four-query repo-docs corpus, explicitly documenting that the tiny sample
  validates the evaluation path rather than general retrieval quality.
- Added versioned runtime-metric artifacts and sanitized benchmark reports for
  captured latency, token counts, RAM high-water, and available macOS
  memory/swap counters without inferring missing observations.
- Added a metadata-only MLX-LM LoRA experiment scaffold with dataset manifests,
  adapter registry, command/eval templates, and an offline validator; no
  fine-tuning run or private dataset processing is claimed.
- Separated radar candidates, installed runtime inventory, demo fixtures,
  benchmark artifacts, imported runs, and confirmed model decisions to prevent
  false rankings.
- Added candidate readiness and benchmark matrix planning so local benchmark
  targets can be reviewed before any model execution occurs.
- Added approval-gated local benchmark execution requiring explicit model id,
  runner, run id, and approval before any local model call is made.
- Scoped batch benchmark approval to a printed candidate/model/runner/run-id
  enumeration and blocked the entire queue when required local metadata was
  incomplete.
- Surfaced imported benchmark performance metadata in Compare and Capability
  views for tokens/sec, TTFT, and total latency with empty states when no
  approved run has provided those values.
- Created a security-review workflow for AI model recommendations covering
  provenance, license posture, artifact format, checksum status, runtime path,
  isolation notes, and approval state.

## Product / AI Ops

- Turned model discovery into a practical product loop: source packet, candidate
  registry, security gate, benchmark artifact, raw evidence, confirmed scoring,
  dashboard comparison, and final decision.
- Added GitHub Project Radar to evaluate AI-adjacent repositories by priority,
  business tie-in, local fit, learning value, and risk notes.
- Built dashboard views for lab cockpit, capability context, radar candidates,
  specialty abliterated/Dolphin models, project radar, installed inventory,
  model runs, compare, reports, and storage decisions.

## Security-Aware

- Enforced local-first guardrails: no hidden cloud calls, no model download logic
  in radar, no committed secrets, no runtime API SDK dependency drift, and
  disabled write actions by default.
- Added dashboard action safeguards for local-only workflows, including explicit
  server flags, action tokens, capped POST bodies, and loopback-only runtime
  controls.
- Added delete-action safeguards for local model cleanup: disabled by default,
  two-step confirmation, server-derived paths, path containment, and no `rm -rf`.
- Documented model vetting practices that treat popularity as context rather
  than approval before downloading or executing local AI artifacts.

## Interview Talking Points

- Why installed model inventory is not the same as benchmarked model quality.
- How demo fixture isolation prevents misleading dashboard rankings.
- Why radar candidates must not automatically become scores or decisions.
- How local-first constraints shaped the CLI, dashboard, benchmark, and security
  review architecture.
- What v1.0.0 proves: a local-first product loop from approved candidate to
  benchmark artifact, confirmed score, dashboard import, model comparison, and
  release evidence.
- How fit estimates, observed throughput, and confirmed task leaders answer
  different questions without presenting estimates or a two-model sample as
  broad comparative truth.
