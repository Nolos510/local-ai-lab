# v1 Second Benchmark Queue

Date: 2026-06-05

## Summary

The second real benchmark is queued, not run. The project currently has one real
confirmed scored benchmark:

```text
data/eval_results/20260605-qwen3-coder-30b-a3b-lmstudio-cli-r1/
```

The next preferred large-model target remains:

```text
20260605-dolphin-mistral-24b-venice-edition
```

## Why It Was Not Run Yet

Fresh local inventory checks did not provide an exact second benchmark target:

- `~/.lmstudio/bin/lms ls --json` timed out while starting or connecting to the
  local LM Studio daemon.
- `~/.lmstudio/bin/lms ps --json` timed out while starting or connecting to the
  local LM Studio daemon.
- `ollama list` crashed locally before returning an inventory table.

Because the dashboard now treats installed inventory, radar candidates, and
scored benchmarks as separate states, no fake benchmark artifact was created.

## Current Queue Decision

- Keep Dolphin-Mistral 24B queued behind security/runtime approval.
- Do not score Dolphin-Mistral 24B until a concrete local artifact, exact local
  runtime ID, and security review are available.
- If another exact installed/indexed model becomes visible first, it can become
  benchmark #2 after the same security and registry checks.

## Commands To Recheck

```bash
~/.lmstudio/bin/lms ls --json
~/.lmstudio/bin/lms ps --json
ollama list
```

If an exact model ID appears, update `data/model_registry/candidates.csv` with:

```text
local_runner
local_model_id
default_endpoint, if endpoint-based
runtime_availability
security_review_path
```

Then run the benchmark harness, preserve raw responses, write confirmed scores
and decision artifacts, export dashboard CSVs, import into a temp dashboard DB,
and commit the second benchmark separately.
