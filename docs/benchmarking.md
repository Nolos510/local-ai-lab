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
- [ ] Add local run recorder.
- [ ] Add report templates under `reports/benchmarks`.
- [ ] Add plots after the first stable benchmark data exists.
