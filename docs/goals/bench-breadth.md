# Goal — Benchmark breadth + real perf

- **Branch:** `codex/bench-breadth`
- **Area:** `evals/local-llm-benchmark/`, `src/local_ai_lab/cli/lab.py`
- **Reserved ADR:** 0009

```text
GOAL: Broaden the local benchmark harness to run more local runtimes and capture
real performance metrics, so the dashboard perf charts can show live data.

BRANCH: codex/bench-breadth. AREA: evals/local-llm-benchmark/ and
src/local_ai_lab/cli/lab.py. Do NOT touch apps/model-dashboard internals beyond
the schema/import contract. Reserve ADR 0009.

START HERE: Read AGENTS.md (binding). The approval-gated benchmark execution surface
already exists (ai-lab bench execute, ADR 0005) with runners {lmstudio-cli,
openai-compatible} and perf columns ttft_seconds/total_latency_seconds/
tokens_per_sec. This goal ADDS runtimes + memory capture behind the SAME approval
gate.

HARD CONSTRAINTS:
- Model execution stays behind the existing explicit approval gate (--model-id,
  --runner, --run-id, --i-approve-local-run). With approval absent, NO model call.
- No new heavy/default runtime deps. RAM/memory capture uses stdlib + macOS
  subprocess (vm_stat / ps), NOT psutil/torch.
- All tests use FAKE runners/subprocess (no real model calls). Do not download
  models. No cloud APIs.

LOOPS:
B1: Add an Ollama-native runner (via the local Ollama API/CLI) to the harness and
    to `ai-lab bench execute --runner`. Capture total latency + tokens/sec.
B2: Add an MLX-LM runner (mlx_lm via subprocess). Capture latency + tokens/sec.
B3: Add a llama.cpp (llama-cli) runner where practical. If a runtime isn't
    cleanly capturable, document the limitation rather than fabricating metrics.
B4: Capture RAM / memory-pressure during a run (stdlib + vm_stat/ps), write to
    model_runs.ram_usage_gb. Leave ttft null unless truly measured — never fake it.
B5: Add ADR 0009 (runner breadth + perf capture) + a reproducible benchmark
    methodology note in evals/local-llm-benchmark/. Update docs.

PER LOOP: inspect git status; implement; add fake-based tests; run the FULL gate
(same 5 commands as the repo standard); commit (scope: bench); STOP and report.
The actual run against a real model is a separate user-approved step — do NOT run
one yourself. Begin with B1.
```
