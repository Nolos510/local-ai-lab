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

## TODO

- [ ] Define benchmark manifest format.
- [ ] Add local run recorder.
- [ ] Add report templates under `reports/benchmarks`.
- [ ] Add plots after the first stable benchmark data exists.
