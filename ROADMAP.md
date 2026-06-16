# Roadmap

## Completed Baseline

- [x] AI Lab OS monorepo structure.
- [x] Local model performance dashboard with SQLite, CSV import/export,
  fixtures, scoring helpers, reports, and smoke tests.
- [x] Local RAG/provider app scaffold with CLI, FastAPI, deterministic test
  providers, Qdrant integration, and doctor checks.
- [x] AI Lab Radar candidate intake, source packets, reports, and local-first
  guardrails.
- [x] Local LLM benchmark harness skeleton.
- [x] First scored local Qwen benchmark artifact.
- [x] Confirmed Qwen3 Coder LM Studio CLI benchmark artifact.
- [x] Radar candidate dashboard view.
- [x] GitHub project radar view.

## v0: Runnable Local RAG Baseline

- [x] uv Python project layout.
- [x] Qdrant and Open WebUI Docker Compose services.
- [x] CLI ingestion and ask commands.
- [x] FastAPI `/ask` endpoint.
- [x] Deterministic local embedding provider.
- [x] Ollama and LM Studio provider abstractions.
- [x] Starter docs and tests.

## v1: Local AI Lab Product Loop

- [ ] Approve one radar candidate from source packet to registry.
- [ ] Run one additional real scored local benchmark; next queued large-model
  target is Dolphin-Mistral 24B after security review and exact local runtime
  id confirmation.
- [ ] Capture all prompt responses with source evidence.
- [ ] Add local-judge draft score suggestions without overwriting confirmed
  scores.
- [ ] Import confirmed benchmark CSVs into the dashboard.
- [ ] Compare at least two models in the dashboard.
- [ ] Link candidate -> source packet/report -> benchmark artifact -> dashboard
  result.
- [ ] Keep candidate-only records visually separate from eval scores.
- [ ] Tag a pushed v1 release with validation evidence.

## v2: Retrieval Quality

- [ ] Add a real local embedding backend, likely BGE-M3.
- [ ] Add sparse or hybrid retrieval in Qdrant.
- [ ] Add reranker abstraction and BGE/Jina reranker integrations.
- [ ] Add source-aware citation rendering and retrieval inspection reports.
- [ ] Add RAG evaluation set format and scoring scripts.

## v3: Benchmarking Lab

- [ ] Benchmark Ollama, MLX-LM, LM Studio, and llama.cpp where practical.
- [ ] Track TTFT, tokens/sec, total latency, memory pressure, and swap behavior.
- [ ] Add benchmark report templates and plotting utilities.
- [ ] Publish reproducible benchmark methodology.
- [ ] Expand the model registry for large 24B, 30B, 70B-class, and specialty
  abliterated/Dolphin candidates that fit the 256 GB RAM environment.

## v4: MLX-LM Fine-Tuning Experiments

- [ ] Add dataset manifest format.
- [ ] Add LoRA/QLoRA experiment templates.
- [ ] Track dataset hash, base model, adapter config, prompt template, and eval
  results.
- [ ] Document adapter export and serving options.

## Later

- [ ] Add cloud portability profiles for Qdrant, API, and hosted model
  endpoints.
- [ ] Add optional observability stack.
- [ ] Add LangGraph/DSPy only after stable eval targets exist.
- [ ] Add workspace cockpit degraded-state reporting.
- [ ] Add model cookbook hardware-fit guidance for Apple Silicon.
- [ ] Add blind model comparison with vote, reveal, tie, and history.
- [ ] Add deep research, document intelligence, memory/skills, email/calendar,
  task, browser, or MCP lanes only after ADR approval.
- [ ] Turn completed tasks into portfolio and resume evidence.
