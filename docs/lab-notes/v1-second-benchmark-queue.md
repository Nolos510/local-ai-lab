# v1 Second Benchmark Queue

Date: 2026-06-05
Closed: 2026-06-25

## Summary

The second real benchmark queue is closed for v1. The project started this note
with one real confirmed scored benchmark:

```text
data/eval_results/20260605-qwen3-coder-30b-a3b-lmstudio-cli-r1/
```

The second official v1 benchmark is now represented by sanitized evidence for:

```text
20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2
```

See:

```text
docs/lab-notes/2026-06-25-dolphin-mistral-v1-benchmark.md
```

## Original Blocker

The first local inventory checks did not provide an exact second benchmark
target:

- `~/.lmstudio/bin/lms ls --json` timed out while starting or connecting to the
  local LM Studio daemon.
- `~/.lmstudio/bin/lms ps --json` timed out while starting or connecting to the
  local LM Studio daemon.
- `ollama list` crashed locally before returning an inventory table.

Because the dashboard now treats installed inventory, radar candidates, and
scored benchmarks as separate states, no fake benchmark artifact was created.

## Closed Queue Decision

- Dolphin-Mistral 24B was approved only for the exact already-local LM Studio
  CLI id `dolphin-mistral-24b-venice-edition`.
- The official r2 run has 12 raw response records, 0 runtime errors, confirmed
  score `65.45`, and decision `watchlist`.
- Raw responses remain local/ignored; committed evidence is sanitized.
- Do not average the earlier Dolphin run into an official score until an
  explicit aggregation feature exists.

## Next Queue Policy

- If another exact installed/indexed model becomes visible first, it can become
  benchmark #2 after the same security and registry checks.

## Commands To Recheck

```bash
~/.lmstudio/bin/lms ls --json
~/.lmstudio/bin/lms ps --json
ollama list
```

For the next queued candidate, update `data/model_registry/candidates.csv` with:

```text
local_runner
local_model_id
default_endpoint, if endpoint-based
runtime_availability
security_review_path
```

Then run the benchmark harness, preserve raw responses, write confirmed scores
and decision artifacts, export dashboard CSVs, import into a temp dashboard DB,
and commit sanitized evidence separately.
