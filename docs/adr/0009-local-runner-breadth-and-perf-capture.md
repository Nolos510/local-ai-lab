# ADR 0009: Local Runner Breadth And Perf Capture

Status: accepted

Date: 2026-06-23

## Context

AI Lab OS needs dashboard performance charts to show live local benchmark data
instead of relying on fixture rows or manually typed throughput values. ADR 0005
created the approval-gated `ai-lab bench execute` surface, but its initial
capture breadth covered only LM Studio CLI and OpenAI-compatible local
endpoints.

The lab's supported local runtime direction includes Ollama, LM Studio,
MLX/MLX-LM, and llama.cpp. These runtimes expose different local interfaces and
different quality of perf metadata. Some expose structured token counts, some
print stats to stderr, and non-streaming subprocess paths do not honestly
measure time to first token.

Model execution remains a material side effect. It can load large local models,
consume RAM, and write raw artifacts. Runner breadth and live performance
capture must not weaken the explicit approval gate or add hidden downloads,
cloud APIs, SDK clients, telemetry, secrets, or heavy dependencies.

## Decision

Keep `ai-lab bench execute` as the single sanctioned local execution wrapper and
broaden its runner choices behind the same approval gate.

The supported runner values are:

- `openai-compatible` for loopback OpenAI-compatible chat endpoints;
- `lmstudio-cli` for installed LM Studio CLI models;
- `ollama` for the local Ollama `/api/generate` endpoint;
- `mlx-lm` for `python -m mlx_lm generate` subprocess capture;
- `llama-cpp` for `llama-cli` subprocess capture.

All runners still require explicit `--candidate`, `--model-id`, `--runner`,
`--run-id`, and `--i-approve-local-run` for non-interactive execution. Without
approval, the wrapper exits before any harness subprocess, local endpoint
request, score export, dashboard import, model call, or model runtime command.

The benchmark harness records only metrics it directly observes:

- `total_latency_seconds` from wall-clock elapsed time around prompt captures;
- `tokens_per_sec` from runtime-reported output tokens/sec when available, or
  from observed output token counts divided by elapsed time where the runner
  returns reliable output token counts;
- `ram_usage_gb` from local macOS `vm_stat` high-water samples and subprocess
  RSS samples through `ps`;
- `ttft_seconds` remains nullable unless a future streaming path measures it
  directly.

The harness remains stdlib-only. It shells out to native local tools already
installed by the operator. It does not install runtimes, download models, look up
remote model metadata, call cloud model APIs, use API keys, or add a profiler
dependency such as `psutil` or `torch`.

## Consequences

Dashboard imports can now carry live local performance data for latency,
throughput, and RAM high-water into `model_runs.csv` and SQLite while preserving
the existing schema/import contract.

Performance values are intentionally sparse when a runtime cannot expose them
cleanly. The llama.cpp runner, for example, records tokens/sec only when
`llama-cli` prints `llama_perf_context_print` timing lines. Missing runtime
stats remain empty instead of being fabricated.

The same approval semantics apply across all local runners, so dashboard or
automation surfaces should continue to call `ai-lab bench execute` or preserve
equivalent safeguards.

Methodology lives in
`evals/local-llm-benchmark/BENCHMARK_METHODOLOGY.md` so operators can reproduce
runs without changing architecture or adding dependencies.
