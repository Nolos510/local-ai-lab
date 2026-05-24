# Roadmap

## v0: Runnable Local RAG Baseline

- [x] uv Python project layout
- [x] Qdrant and Open WebUI Docker Compose services
- [x] CLI ingestion and ask commands
- [x] FastAPI `/ask` endpoint
- [x] deterministic local embedding provider
- [x] Ollama and LM Studio provider abstractions
- [x] starter docs and tests

## v1: Retrieval Quality

- [ ] Add a real local embedding backend, likely BGE-M3.
- [ ] Add sparse or hybrid retrieval in Qdrant.
- [ ] Add reranker abstraction and BGE/Jina reranker integrations.
- [ ] Add source-aware citation rendering and retrieval inspection reports.
- [ ] Add RAG evaluation set format and scoring scripts.

## v2: Benchmarking Lab

- [ ] Benchmark Ollama, MLX-LM, LM Studio, and vllm-metal where practical.
- [ ] Track TTFT, tokens/sec, total latency, memory pressure, and swap behavior.
- [ ] Add benchmark report templates and plotting utilities.
- [ ] Publish reproducible benchmark methodology.

## v3: MLX-LM Fine-Tuning Experiments

- [ ] Add dataset manifest format.
- [ ] Add LoRA/QLoRA experiment templates.
- [ ] Track dataset hash, base model, adapter config, prompt template, and eval results.
- [ ] Document adapter export and serving options.

## Later

- [ ] Add cloud portability profile for Qdrant, API, and hosted model endpoints.
- [ ] Add optional observability stack.
- [ ] Add LangGraph/DSPy only after stable eval targets exist.
