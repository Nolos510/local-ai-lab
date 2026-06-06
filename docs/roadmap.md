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

- [x] Add a real local embedding provider.
- [ ] Add retrieval evaluation fixtures.
- [ ] Improve citation and source metadata handling.
- [ ] Consider hybrid retrieval after the basic path is measured.
- [ ] Add reranking only when retrieval failure analysis justifies it.

## v2: Evaluation and Benchmarking

- [x] Add a local LLM benchmark harness for model-dashboard artifacts.
- [ ] Add an evaluation harness for RAG answers and citations.
- [ ] Track latency, retrieval scores, model/provider choices, and command outputs.
- [x] Add benchmark reports for the first Qwen3 Coder LM Studio CLI run.
- [ ] Add a second unique model benchmark; next queued target is
  Dolphin-Mistral 24B after security and exact local runtime-id approval.
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
