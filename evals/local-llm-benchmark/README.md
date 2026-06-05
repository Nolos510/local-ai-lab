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

Allowed endpoints are `localhost`, loopback IPs, and literal private LAN IPs.
Public hosts and public IP addresses are rejected. Runtime errors are preserved
as raw benchmark evidence instead of being turned into scores.

If LM Studio's OpenAI-compatible server is reachable but returns `401
Unauthorized`, use the installed-model CLI lane for models that appear in local
LM Studio inventory:

```bash
python3 evals/local-llm-benchmark/harness.py run-lmstudio-cli \
  --run-dir data/eval_results/<run_id> \
  --model-id qwen3-coder-30b-a3b-instruct-mlx \
  --force
```

This runs `lms chat <model-id> -p <prompt> --stats --ttl 3600`, captures all
prompt responses into `raw_responses.jsonl`, and preserves CLI output in
`lms-cli-capture.log`. It does not download, install, or fetch models.

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
