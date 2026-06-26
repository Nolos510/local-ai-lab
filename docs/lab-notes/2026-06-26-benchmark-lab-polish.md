# V3 Benchmark Lab Polish

Date: 2026-06-26

This pass improves benchmark evidence without changing dashboard schema or
touching the active dashboard UI branch.

## Changes

- Added `runtime-metrics.json` to benchmark run artifacts.
- Preserved richer memory/swap data outside dashboard CSVs:
  - raw prompt count;
  - error count;
  - latency min/max/sum;
  - token totals;
  - observed RAM high-water;
  - macOS `vm_stat` used-memory and swap counters when available.
- Added `render-report` to produce sanitized Markdown benchmark reports from
  existing artifacts.
- Added runtime-metrics references to dashboard run notes while keeping the
  existing `model_runs.csv` fields stable.
- Documented metadata-only planning for 24B, 30B, 70B, and specialty model
  queues.

## Runner Audit

The current live runner lanes remain:

- `openai-compatible`
- `lmstudio-cli`
- `ollama`
- `mlx-lm`
- `llama-cpp`

Live execution stays behind `uv run ai-lab bench execute` approval. The command
must refuse before local endpoint or subprocess execution unless
`--i-approve-local-run` is provided or an interactive operator explicitly
confirms the run.

## Guardrails

- No model downloads, installs, cloud APIs, SDKs, secrets, or telemetry were
  added.
- Dashboard CSV schema remains unchanged.
- Missing runtime measurements stay `null`; no memory, swap, token, or TTFT
  values are inferred.
- Candidate queue guidance is metadata-only and does not create scores,
  decisions, or new registry rows.

## Follow-Up

- Run future live benchmarks only after exact local runtime IDs and security
  review approval.
- Add charting or aggregation only after stable multi-run benchmark data exists.
