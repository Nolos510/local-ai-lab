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
- [x] Approval-gated local benchmark execution through the `ai-lab` CLI.
- [x] Disabled-by-default, recoverable local model removal action for LM Studio
  and Ollama inventory entries.
- [x] Midnight Neon dashboard redesign with offline icons, collapsible sidebar,
  and inline SVG performance charts.
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
- [x] Compare imported benchmark runs in the dashboard with inline SVG charts
  for score dimensions and imported performance metadata.
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
- [x] Add approval-gated local benchmark execution to the unified `ai-lab` CLI.
- [ ] Tag a pushed v1 release with validation evidence.

## v2: Retrieval Quality

- [x] Add a real local embedding backend.
- [x] Add retrieval evaluation fixtures and a stdlib scorer for `recall@k` and
  `MRR`.
- [x] Add opt-in hybrid dense plus local lexical retrieval with reciprocal-rank
  fusion.
- [x] Add reranker abstraction with an identity default.
- [x] Add source-aware default citation rendering plus explicit local retrieval
  inspection.
- [ ] Run the retrieval scorer on a real local corpus with BGE-M3 embeddings and
  record the measured recall/MRR evidence.
- [ ] Add a reviewed real local cross-encoder reranker backend behind the
  optional `[rerank]` extra.
- [ ] Add RAG answer/citation evaluation set format and scoring scripts.
- [ ] Track retrieval scores, model/provider choices, and command outputs.

## v3: Benchmarking Lab

- [ ] Benchmark Ollama, MLX-LM, LM Studio, and llama.cpp where practical.
- [x] Track imported TTFT, tokens/sec, and total latency in dashboard compare and
  capability charts.
- [ ] Track memory pressure and swap behavior for approved local benchmark runs.
- [ ] Add benchmark report templates and plotting utilities.
- [ ] Publish reproducible benchmark methodology.
- [ ] Expand the model registry for large 24B, 30B, 70B-class, and specialty
  abliterated/Dolphin candidates that fit the 256 GB RAM environment.
- [ ] Add an evaluation harness for RAG answers and citations.
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
