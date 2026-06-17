# Approval-Gated Benchmark Execution

Date: 2026-06-17

Status: L3 implemented with fake-runner and fake-endpoint validation. No live
model execution was performed as part of this implementation loop.

## Command

The sanctioned execution path is:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <exact_local_model_id> \
  --runner lmstudio-cli \
  --run-id <benchmark_run_id> \
  --i-approve-local-run
```

For a local OpenAI-compatible endpoint, use:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <exact_local_model_id> \
  --runner openai-compatible \
  --endpoint http://127.0.0.1:1234/v1 \
  --run-id <benchmark_run_id> \
  --i-approve-local-run
```

## Gate

The command refuses to run unless the operator supplies an explicit candidate,
exact local model id, runner, run id, and either `--i-approve-local-run` or an
interactive `yes`.

Before approval, it prints a preflight containing the candidate, model id,
runner, run id, prompt set id, artifact directory, capture shape, dashboard
import target, and dashboard CSV directory.

If approval is missing, it exits before any harness subprocess, model endpoint,
dashboard import, or score export. This is covered by unit tests that fail if a
subprocess is invoked.

## Outputs

After approval, the wrapper delegates to existing local harness commands:

1. `init-run`
2. `run-lmstudio-cli` or `run-local`
3. `export-dashboard`
4. optional dashboard `import-csv`

Captured run metadata can include aggregate `tokens_per_sec`,
`total_latency_seconds`, and `ram_usage_gb`. `ttft_seconds` remains nullable
until a future streaming path captures it directly.

## Not Covered

This machinery does not download models, install runtimes, call cloud APIs,
read secrets, or infer a runnable identity from registry metadata alone. Live
model execution remains a separate user-approved step after verifying the exact
local model id and runtime.
