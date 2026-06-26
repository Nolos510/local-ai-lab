# Local Benchmark Methodology

This note defines the reproducible local benchmark procedure for AI Lab OS. It
uses the existing stdlib harness and the approval-gated `ai-lab bench execute`
wrapper. It does not download models, install runtimes, call cloud APIs, use
secrets, or infer a runnable model id from registry metadata.

## Scope

Use this methodology for local candidate runs that should produce dashboard
import artifacts with live latency, throughput, and RAM measurements.

Supported runner values:

- `openai-compatible`
- `lmstudio-cli`
- `ollama`
- `mlx-lm`
- `llama-cpp`

Every live run is a separate operator-approved action. Implementation and test
loops use fake subprocesses or fake endpoints only.

The approval gate covers all current runner lanes: `openai-compatible`,
`lmstudio-cli`, `ollama`, `mlx-lm`, and `llama-cpp`. A command that lacks
`--i-approve-local-run` must refuse before shelling out to local runtimes or
posting to a local endpoint.

## Preflight

1. Inspect the candidate row:

   ```bash
   uv run ai-lab bench matrix --limit 20
   ```

2. Confirm the exact local runtime and model identity outside the benchmark
   harness. Examples include `lms ls`, `ollama list`, a known MLX local path, or
   a local GGUF file path for `llama-cli`.

3. Record local hardware context when useful for later comparison:

   ```bash
   uv run ai-lab hardware snapshot --out docs/lab-notes/<run-id>-hardware.json
   ```

4. Choose a stable `run-id`. Prefer an ISO-like date prefix plus candidate and
   runtime, for example:

   ```text
   20260623-qwen3-8b-ollama-r1
   ```

5. Confirm that the model is already installed locally. Do not use this
   benchmark flow to download, install, or resolve models.

## Approved Execution

Run through `ai-lab bench execute`. The command prints a preflight and refuses
to continue unless `--i-approve-local-run` is present, or an interactive TTY
operator types `yes`.

Ollama:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <ollama_model_id> \
  --runner ollama \
  --run-id <run_id> \
  --i-approve-local-run
```

LM Studio CLI:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <lm_studio_model_id> \
  --runner lmstudio-cli \
  --run-id <run_id> \
  --i-approve-local-run
```

OpenAI-compatible loopback endpoint:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <local_model_id> \
  --runner openai-compatible \
  --endpoint http://127.0.0.1:1234/v1 \
  --run-id <run_id> \
  --i-approve-local-run
```

MLX-LM:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <mlx_model_or_path> \
  --runner mlx-lm \
  --run-id <run_id> \
  --i-approve-local-run
```

llama.cpp:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id /path/to/model.gguf \
  --runner llama-cpp \
  --run-id <run_id> \
  --i-approve-local-run
```

Optional flags such as `--max-tokens`, `--timeout`, `--endpoint`,
`--lms-path`, `--mlx-python`, and `--llama-cli-path` should be recorded in the
run notes or evidence when they differ from defaults.

## Captured Metrics

`total_latency_seconds` is the sum of measured per-prompt wall-clock latency for
the prompt set.

`tokens_per_sec` is recorded only when the runner exposes output token counts or
tokens/sec cleanly:

- OpenAI-compatible endpoints use `usage.completion_tokens` when present.
- Ollama uses `eval_count` and `eval_duration`.
- LM Studio CLI uses printed `--stats` labels.
- MLX-LM uses printed prompt/generation token and tokens/sec labels.
- llama.cpp uses `llama_perf_context_print` eval timing lines.

`ram_usage_gb` is the observed high-water value from local macOS `vm_stat`
sampling plus subprocess RSS sampling through `ps` where applicable. Treat it as
a local operational measurement, not a universal model-size claim.

`runtime-metrics.json` keeps artifact-level operational detail that does not
belong in the stable dashboard CSV schema yet: raw prompt count, error count,
latency min/max/sum, token totals, observed RAM high-water, `vm_stat` used
memory, and `vm_stat` swap counters when available. Missing fields stay `null`.
Do not infer memory pressure, swap, or TTFT from model size or total latency.

`ttft_seconds` stays empty unless a future streaming runner measures time to
first token directly. Do not infer TTFT from total latency.

## Artifacts

Each run writes:

```text
data/eval_results/<run_id>/
  metadata.json
  raw_responses.jsonl
  runtime-metrics.json
  evidence.md
  benchmark-report.md
  dashboard-import/
    models.csv
    model_runs.csv
    eval_scores.csv
    decisions.csv
```

Raw responses remain local benchmark evidence. Do not paste private raw output
into public notes. Draft local-judge scores must remain draft until human
review confirms scores and decisions.

Render a sanitized benchmark report after capture/export:

```bash
python3 evals/local-llm-benchmark/harness.py render-report \
  --run-dir data/eval_results/<run_id>
```

The report includes counts, hashes, metrics, scores, decisions, and dashboard
CSV row counts only.

## Import And Review

After reviewing raw artifacts, import dashboard CSVs explicitly:

```bash
uv run ai-lab import --run <run_id>
```

Then review the dashboard performance charts and run detail pages locally:

```bash
uv run ai-lab dashboard --port 8765
```

## Repeatability Notes

For comparable runs, keep the same prompt set, runtime, model id, quantization,
context settings, sampling parameters, max token limit, and hardware state.
Record runtime versions when available. If a runner omits token stats or memory
sampling is unavailable, leave the corresponding CSV fields empty and document
the limitation in `evidence.md`.
