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

The checked-in harness scaffolds local artifacts, records human-supplied raw
responses, and writes dashboard-compatible CSV files. It does not download,
install, run, or call any model.

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

Normalize human-supplied responses into the run artifact:

```bash
python3 evals/local-llm-benchmark/harness.py record-responses \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --responses-jsonl data/eval_results/20260603-example-model-llamacpp-q4/manual-responses.jsonl
```

After manual scoring, create filled score and decision JSON files from the
templates, then export dashboard CSVs:

```bash
python3 evals/local-llm-benchmark/harness.py export-dashboard \
  --run-dir data/eval_results/20260603-example-model-llamacpp-q4 \
  --scores-json data/eval_results/20260603-example-model-llamacpp-q4/scores.json \
  --decision-json data/eval_results/20260603-example-model-llamacpp-q4/decision.json
```

`eval_scores.csv` and `decisions.csv` are header-only until filled score and
decision files are provided. This avoids importing placeholder zero scores as
real benchmark results.

## Dependency Posture

The harness should stay Python stdlib-only. JSON Lines, CSV export,
Markdown reports, subprocess capture, file layout, and timing can all be handled
with standard library modules. If Harness Builder proposes a package, challenge
it against `AGENTS.md` before adding anything to `pyproject.toml`.

## Validation

Harness tests are included in the repository-level pytest configuration:

```bash
python -m pytest -q
```
