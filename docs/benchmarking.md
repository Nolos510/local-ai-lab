# Benchmarking Roadmap

The benchmark harness should measure local AI systems as systems, not just models.

## Metrics

- time to first token
- steady-state tokens per second
- total latency
- prompt tokens
- completion tokens
- memory pressure
- swap usage
- retrieved chunk quality
- answer quality by evaluation set

## Candidate Runtime Matrix

- Ollama / llama.cpp
- LM Studio
- MLX-LM
- vllm-metal later

## Artifact-Level Runtime Metrics

Benchmark artifacts now include `runtime-metrics.json` in addition to the stable
dashboard CSVs. Keep exporting `ram_usage_gb` to `model_runs.csv`, but place
richer local operational detail in the artifact and report:

- raw prompt count and error count;
- latency min/max/sum;
- input/output token totals;
- observed RAM high-water GB;
- macOS `vm_stat` used-memory and swap counters when available.

Missing values stay `null`. Do not infer memory pressure, swap behavior, token
counts, or TTFT from model size or source claims.

## Metadata-Only Large Model Queue

The 256 GB Mac Studio can plan larger local tests, but queue entries remain
metadata until a concrete local artifact clears review. Do not download, install,
or run a model from this planning list.

Suggested queue bands:

- 24B class: Dolphin/Mistral specialty candidates and other already-indexed
  LM Studio models with exact local IDs.
- 30B class: Qwen3 A3B variants, including separate vanilla versus abliterated
  candidates only when the exact local runtime ID matches the registry row.
- 70B class: high-value GGUF/MLX candidates only after source, license, checksum,
  quantization, storage, and runtime path review.
- Specialty models: abliterated/Dolphin/uncensored candidates require extra
  safety notes, refusal-behavior notes, and non-daily-driver risk labeling before
  any keep decision.

Required queue metadata before benchmark approval:

- candidate ID and model name;
- source packet/report paths;
- security review path and approval state;
- exact local runner and model ID/path;
- runtime availability evidence from LM Studio, Ollama, MLX-LM, or llama.cpp;
- planned benchmark run ID and reason to evaluate.

## Metadata-Only Lab Loop Smoke

This smoke path verifies the local AI Lab OS operating surface without executing
a model. It reads the candidate registry, prints the benchmark matrix,
initializes a prepared benchmark artifact, imports the generated model/run CSVs
into a temporary dashboard database, and launches the dashboard against that
temporary database.

```bash
rm -rf /tmp/ai-lab-quickstart-eval /tmp/ai-lab-quickstart-dashboard.sqlite /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab radar list --status ready_for_eval --limit 5
uv run ai-lab bench matrix --limit 5
uv run ai-lab bench run --candidate 20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit --run-id quickstart-qwen3-coder-prep --output-root /tmp/ai-lab-quickstart-eval
uv run ai-lab import --run quickstart-qwen3-coder-prep --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab report --db /tmp/ai-lab-quickstart-dashboard.sqlite --out /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab status --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab dashboard --db /tmp/ai-lab-quickstart-dashboard.sqlite --port 8767
```

The expected imported state is `models=1`, `runs=1`, `scores=0`, and
`decisions=0`. This is useful for onboarding and UI validation, but it is not a
scored benchmark. It does not call LM Studio, Ollama, llama.cpp, MLX, or any
model endpoint; it does not create raw responses, scores, or keep/watch
decisions. Stop the dashboard server with `Ctrl-C` when finished.

Only `ai-lab bench execute` performs local benchmark capture, and it requires an
exact local model id, runner, run id, and explicit approval flag.

## TODO

- [ ] Define benchmark manifest format.
- [x] Add local run recorder.
- [x] Add artifact-level runtime metrics and sanitized benchmark report renderer.
- [ ] Add plots after the first stable benchmark data exists.
