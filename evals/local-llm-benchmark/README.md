# Local LLM Benchmark

Repeatable local benchmark format and stdlib artifact harness for AI Lab OS
model testing.

Start with `SPEC.md`. The v0.1 spec defines:

- The canonical prompt set: `ai-lab-local-llm-core-v0.1`
- The rubric version: `ai-lab-local-llm-rubric-v0.1`
- Raw response and evaluator evidence expectations
- The 0-100 scoring dimensions used by `skills/local-llm-eval`
- The normalized CSV fields needed by `apps/model-dashboard`

Harness-ready format proposals:

- `manifests/prompt-manifest-v0.1.json`
- `rubrics/rubric-scorecard-v0.1.json`
- `HARNESS_ASSETS.md`

The checked-in harness scaffolds local artifacts, records raw responses from
manual input or approved local endpoints, asks a separate local judge for draft
score suggestions, and writes dashboard-compatible CSV files. It does not
download models, install models, call cloud APIs, use secrets, or add API
clients.

## Local Files

- `prompts/ai-lab-local-llm-core-v0.1.json` is the canonical prompt set.
- `rubrics/ai-lab-local-llm-rubric-v0.1.json` is the local scoring rubric.
- `harness.py` is a Python stdlib-only capture/export CLI.
- `BENCHMARK_METHODOLOGY.md` is the approved reproducible local run procedure.

## Methodology

Use `BENCHMARK_METHODOLOGY.md` for approved local runs that should populate
dashboard performance charts with live latency, throughput, and RAM data. Live
execution remains behind `ai-lab bench execute --i-approve-local-run`; tests and
implementation loops use fake endpoints or fake subprocesses only.

## Harness Flow

Create a local run directory:

```bash
python3 evals/local-llm-benchmark/harness.py init-run \
  --benchmark-run-id 20260603-example-model-llamacpp-q4 \
  --model-name "Example Local Model" \
  --backend "llama.cpp" \
  --format GGUF \
  --quantization Q4_K_M \
  --temperature 0.2 \
  --top-p 0.9
```

This writes:

```text
data/eval_results/<benchmark_run_id>/
  metadata.json
  response-template.jsonl
  raw_responses.jsonl
  runtime-metrics.json
  scores-template.json
  decision-template.json
  evidence.md
  dashboard-import/
    models.csv
    model_runs.csv
    eval_scores.csv
    decisions.csv
```

Run prompts manually in the chosen local backend, then create a filled response
JSONL using `response-template.jsonl` as the starting schema. Capture the raw
model text in `raw_response`; do not summarize or edit it.

For a local OpenAI-compatible backend such as LM Studio or Ollama, the harness
can capture the prompt set directly:

```bash
python3 evals/local-llm-benchmark/harness.py run-local \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --endpoint http://127.0.0.1:1234/v1 \
  --model "Example Local Model" \
  --force
```

Allowed endpoints are `localhost` and loopback IPs such as `127.0.0.1` or
`::1`. Private LAN and public hosts/IPs are rejected. Runtime errors are
preserved as raw benchmark evidence instead of being turned into scores.

For an Ollama-native run, use the local Ollama API lane. The default endpoint is
`http://127.0.0.1:11434`, and the harness posts to `/api/generate` with
`stream: false`:

```bash
python3 evals/local-llm-benchmark/harness.py run-ollama \
  --run-dir data/eval_results/<run_id> \
  --model-id llama3.2:latest \
  --force
```

The Ollama runner records measured per-prompt latency plus Ollama-reported
`prompt_eval_count`, `eval_count`, and `eval_duration` when available.
Aggregate `total_latency_seconds` and `tokens_per_sec` are written through the
same dashboard CSV contract as the other runners. `ttft_seconds` remains empty
because this non-streaming lane does not measure time to first token.

For an MLX-LM run, use the subprocess lane. It invokes the local Python
environment with `mlx_lm` installed; it does not install packages or download
models:

```bash
python3 evals/local-llm-benchmark/harness.py run-mlx-lm \
  --run-dir data/eval_results/<run_id> \
  --model-id mlx-community/Example-Model-4bit \
  --force
```

The MLX-LM runner measures wall-clock latency around each
`python -m mlx_lm generate` call. When the CLI prints prompt/generation token
counts and tokens-per-second labels, the harness records them in
`raw_responses.jsonl` and exports aggregate `total_latency_seconds` and
`tokens_per_sec` to `model_runs.csv`. `ttft_seconds` remains empty because this
non-streaming subprocess lane does not measure time to first token.

For a llama.cpp run, use the `llama-cli` subprocess lane. The `--model-id`
argument is passed to `llama-cli -m`; in typical GGUF workflows it should be the
local model path or another value your local `llama-cli` build accepts. The
harness does not install llama.cpp, download models, or resolve remote model
names:

```bash
python3 evals/local-llm-benchmark/harness.py run-llama-cpp \
  --run-dir data/eval_results/<run_id> \
  --model-id /path/to/model.gguf \
  --force
```

The llama.cpp runner measures wall-clock latency around each
`llama-cli -m <model-id> -p <prompt> -n <tokens>` call. It records prompt token
count, output token count, and tokens/sec only when `llama-cli` prints
`llama_perf_context_print` timing lines. If those lines are missing or hidden by
a local build flag, the token fields remain empty instead of being approximated.
`ttft_seconds` remains empty because this non-streaming subprocess lane does not
measure time to first token.

Automatic capture runners also record observed RAM high-water data into
`ram_usage_gb` when the local machine exposes it. Endpoint runners sample
macOS `vm_stat` around each prompt. Subprocess runners also sample child RSS via
`ps` while the command is running. These are local measurements only; the harness
does not install profilers or infer missing model memory.

Every run also writes `runtime-metrics.json`. This artifact preserves richer
local-only operational measurements without changing the dashboard CSV schema:
raw prompt count, error count, latency min/max/sum, input/output token totals,
observed RAM high-water, `vm_stat` used memory, and `vm_stat` swap counters when
available. Missing values stay `null`; do not infer swap or memory pressure from
model size.

If LM Studio's OpenAI-compatible server is reachable but returns `401
Unauthorized`, use the installed-model CLI lane for models that appear in local
LM Studio inventory:

```bash
python3 evals/local-llm-benchmark/harness.py run-lmstudio-cli \
  --run-dir data/eval_results/<run_id> \
  --model-id qwen3-coder-30b-a3b-instruct-mlx \
  --force
```

This runs
`lms chat <model-id> -p <prompt> --stats --ttl 3600 --yes --dont-fetch-catalog`,
captures all prompt responses into `raw_responses.jsonl`, and writes a
metadata-only `lms-cli-capture.log` with return codes, timing, token counts,
stop reason, and sanitized error summaries. It does not download, install, or
fetch models.

Normalize human-supplied responses into the run artifact:

```bash
python3 evals/local-llm-benchmark/harness.py record-responses \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --responses-jsonl data/eval_results/20260603-example-model-llamacpp-q4/manual-responses.jsonl
```

For assisted scoring, point a separate local judge endpoint at the completed run.
This writes `draft-scores.json` with `score_status: draft`; it does not overwrite
the official `scores.json` template.

```bash
python3 evals/local-llm-benchmark/harness.py suggest-scores \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --endpoint http://127.0.0.1:1234/v1 \
  --judge-model "Local Judge Model"
```

After human review, create filled score and decision JSON files from the
templates, then export confirmed dashboard CSVs:

```bash
python3 evals/local-llm-benchmark/harness.py export-dashboard \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --scores-json data/eval_results/20260603-example-model-llamacpp-q4/scores.json \
  --decision-json data/eval_results/20260603-example-model-llamacpp-q4/decision.json
```

To inspect unconfirmed judge suggestions in the dashboard, export the draft
scores instead:

```bash
python3 evals/local-llm-benchmark/harness.py export-dashboard \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --scores-json data/eval_results/20260603-example-model-llamacpp-q4/draft-scores.json
```

`eval_scores.csv` and `decisions.csv` are header-only until filled score and
decision files are provided. This avoids importing placeholder zero scores as
real benchmark results.

Generate a sanitized Markdown report for review or release evidence:

```bash
python3 evals/local-llm-benchmark/harness.py render-report \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4
```

The default output is `benchmark-report.md` inside the run directory. It reports
artifact paths, raw-response counts, SHA256 hashes, dashboard CSV row counts,
runtime metrics, scores, and decisions. It intentionally does not paste raw
model responses into the report.

## Dependency Posture

The harness should stay Python stdlib-only. JSON Lines, CSV export, Markdown
reports, local HTTP capture, file layout, and timing can all be handled with
standard library modules. If Harness Builder proposes a package, challenge it
against `AGENTS.md` before adding anything to `pyproject.toml`.

## Validation

Harness tests are included in the repository-level pytest configuration:

```bash
python -m pytest -q
```
