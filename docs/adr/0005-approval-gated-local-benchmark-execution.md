# ADR 0005: Approval-Gated Local Benchmark Execution

Status: accepted

Date: 2026-06-17

## Context

AI Lab OS has a benchmark harness that can create artifacts and capture responses
from local model runtimes. The unified `ai-lab` CLI previously prepared
benchmark artifacts, but did not provide a sanctioned end-to-end execution path.

Executing a local model is still a material side effect. It can allocate memory,
load a large model, write raw response artifacts, and import results into the
dashboard. The project requires that this never happen implicitly from radar
metadata, registry rows, dashboard render paths, or generic status commands.

## Decision

Add `ai-lab bench execute` as the sanctioned local benchmark execution wrapper.

Execution requires all of the following at the command boundary:

- explicit `--candidate`;
- explicit `--model-id`;
- explicit `--runner`;
- explicit `--run-id`;
- explicit `--i-approve-local-run` for non-interactive execution, or an
  interactive `yes` when stdin is a TTY.

Before any harness subprocess, endpoint request, score export, or dashboard
import, the CLI prints a preflight containing:

- candidate id and candidate model label;
- exact local model id supplied by the operator;
- runner;
- run id;
- prompt set id;
- artifact directory;
- capture command or endpoint shape;
- dashboard import target and CSV directory.

If approval is missing, the command exits before invoking any subprocess or
model endpoint. Tests assert this negative case with fake subprocess runners.

The execution wrapper is local-only. It delegates to existing local harness
commands such as `run-local` and `run-lmstudio-cli`; it does not add model
download logic, cloud model APIs, API key requirements, telemetry, or SDK
clients.

## Consequences

The lab now has one auditable local path from candidate metadata to captured raw
responses, exported dashboard CSVs, and optional dashboard import.

The approval gate is deliberately stricter than a convenience prompt. Registry
metadata may help initialize artifact metadata, but it is not sufficient to
infer runnable identity. The operator must provide the exact local model id and
runner for each execution.

Benchmark runs can now carry aggregate `total_latency_seconds` and
`tokens_per_sec` into dashboard CSVs and SQLite. `ttft_seconds` remains nullable
until a future streaming path captures it honestly.

Future dashboard or automation surfaces that execute benchmarks should call this
same approved command shape or preserve equivalent safeguards.
