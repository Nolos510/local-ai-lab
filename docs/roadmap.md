# Roadmap

## v0: Local RAG Backbone + Provider Harness

Goal: prove a small local-first RAG path on Apple Silicon.

- [ ] Keep CLI/FastAPI native through `uv`.
- [ ] Keep Qdrant and optional Open WebUI in Docker.
- [ ] Keep Ollama, LM Studio, MLX/MLX-LM, and llama.cpp native on macOS.
- [ ] Support ingestion, chunking, retrieval, prompt assembly, local provider calls, and citations.
- [ ] Add honest smoke checks for implemented commands.
- [ ] Keep Open WebUI optional and parallel.

## v1: Retrieval Quality

- [ ] Add a real local embedding provider.
- [ ] Add retrieval evaluation fixtures.
- [ ] Improve citation and source metadata handling.
- [ ] Consider hybrid retrieval after the basic path is measured.
- [ ] Add reranking only when retrieval failure analysis justifies it.

## v2: Evaluation and Benchmarking

- [ ] Add an evaluation harness for RAG answers and citations.
- [ ] Track latency, retrieval scores, model/provider choices, and command outputs.
- [ ] Add benchmark reports for local Apple Silicon model runtimes.
- [ ] Compare Ollama, LM Studio, MLX-LM, and llama.cpp where appropriate.

## v3: MLX-LM Fine-Tuning Experiments

- [ ] Add dataset manifest conventions.
- [ ] Add LoRA/adapter experiment templates.
- [ ] Track base model, adapter config, dataset hash, prompt version, and eval results.
- [ ] Keep fine-tuning experiments separate from the v0 RAG harness.

## Later

- [ ] Document cloud portability profiles before implementation.
- [ ] Add observability only after local request flows are stable.
- [ ] Add agent workflows only after the non-agent RAG backbone is measured and reliable.
