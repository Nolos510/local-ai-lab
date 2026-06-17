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
- [x] Unified `ai-lab` CLI for local status, radar listing, hardware snapshot,
  benchmark matrix planning, benchmark artifact prep, dashboard import/report,
  and dashboard launch.
- [x] Read-only dashboard capability view with candidate readiness, artifact
  counts, hardware profile context, and benchmark matrix guidance.
- [x] Portfolio case study and resume evidence pack.

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
- [x] Compare at least two models in the dashboard with inline SVG charts for
  score, throughput, RAM, and score dimensions.
- [ ] Link candidate -> source packet/report -> benchmark artifact -> dashboard
  result.
- [ ] Keep candidate-only records visually separate from eval scores.
- [x] Add a unified `ai-lab` CLI for status, radar, benchmark prep, import,
  report, and dashboard launch.
- [x] Add `ai-lab hardware snapshot` for sanitized local hardware/runtime
  context.
- [x] Add `ai-lab bench matrix` for read-only benchmark queue planning.
- [x] Add a read-only dashboard capability view.
- [x] Gate dashboard tests, eval harness tests, dashboard smoke, and repo-wide
  ruff in CI.
- [x] Convert current work into portfolio/resume evidence.
- [ ] Add approval-gated local benchmark execution to the unified `ai-lab` CLI.
- [ ] Tag a pushed v1 release with validation evidence.

## v2: Retrieval Quality

- [x] Add a real local embedding backend.
- [ ] Add retrieval evaluation fixtures.
- [ ] Add sparse or hybrid retrieval in Qdrant.
- [ ] Add reranker abstraction and BGE/Jina reranker integrations.
- [ ] Add source-aware citation rendering and retrieval inspection reports.
- [ ] Add RAG evaluation set format and scoring scripts.
- [ ] Consider hybrid retrieval after the basic path is measured.
- [ ] Add reranking only when retrieval failure analysis justifies it.

## v3: Benchmarking Lab

- [ ] Benchmark Ollama, MLX-LM, LM Studio, and llama.cpp where practical.
- [ ] Track TTFT, tokens/sec, total latency, memory pressure, and swap behavior.
- [ ] Add first-class dashboard fields and charts for TTFT and total latency
  after the approval-gated execution path lands.
- [ ] Add benchmark report templates and plotting utilities.
- [ ] Publish reproducible benchmark methodology.
- [ ] Expand the model registry for large 24B, 30B, 70B-class, and specialty
  abliterated/Dolphin candidates that fit the 256 GB RAM environment.
- [ ] Add an evaluation harness for RAG answers and citations.
- [ ] Track retrieval scores, model/provider choices, and command outputs.
- [ ] Add a second unique model benchmark after security and exact local
  runtime-id approval.

## v4: MLX-LM Fine-Tuning Experiments

- [ ] Add dataset manifest conventions.
- [ ] Add LoRA/adapter experiment templates.
- [ ] Track dataset hash, base model, adapter config, prompt version, and eval
  results.
- [ ] Document adapter export and serving options.
- [ ] Keep fine-tuning experiments separate from the v0 RAG harness.

## Later

- [ ] Add cloud portability profiles for Qdrant, API, and hosted model
  endpoints.
- [ ] Add optional observability stack.
- [ ] Add agent workflows only after the non-agent RAG backbone is measured and
  reliable.
- [ ] Add LangGraph/DSPy only after stable eval targets exist.
- [ ] Turn completed tasks into portfolio and resume evidence.
