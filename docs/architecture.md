# Architecture

`local-ai-lab` is a local-first Apple Silicon AI engineering lab. The
architecture optimizes for private local workflows, reproducible experiments,
dashboard-driven model decisions, and clean future portability.

## Hardware Target

- Apple Silicon Mac Studio.
- 256 GB unified memory.
- Large local storage.
- Local-first and privacy-first workflows.

## Product Lanes

- **Local RAG Backbone + Provider Harness:** CLI/FastAPI ingestion, chunking,
  Qdrant retrieval, prompt assembly, local model providers, and citations.
- **AI Lab OS Dashboard Loop:** radar candidate intake, benchmark artifacts,
  scoring summaries, dashboard import, comparison, and keep/watchlist/retest/skip
  decisions.

## v0 Target

v0 is the Local RAG Backbone + Provider Harness.

```text
CLI / FastAPI
  -> ingestion
  -> chunking
  -> Qdrant retrieval
  -> prompt assembly
  -> local model provider
  -> answer + citations
```

## Runtime Boundaries

Docker is used for infrastructure services only:

- Qdrant
- Open WebUI

Native macOS model runtimes:

- Ollama
- LM Studio OpenAI-compatible server
- MLX / MLX-LM
- llama.cpp

Open WebUI is optional and parallel. The FastAPI RAG harness must not depend on
Open WebUI.

## Canonical Layout

```text
src/local_ai_lab/              RAG/provider/API core
apps/model-dashboard/          AI Lab OS dashboard
evals/local-llm-benchmark/     Repeatable eval harness
data/model_registry/           Model candidates
data/project_registry/         Project opportunities
data/eval_results/             Sanitized benchmark summaries and templates
docs/                          Architecture, runtime, portfolio, lab notes
reports/                       Benchmark/eval/postmortem outputs
infra/                         Qdrant/Open WebUI
```

## Python Boundary

The Python application uses:

- `uv`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.env.example`

The CLI and FastAPI harness stay native through `uv` for v0. The dashboard and
local benchmark harness remain dependency-light and use standard-library
modules where practical.

## v0 Constraints

- Keep abstractions simple and testable.
- Avoid framework sprawl.
- Do not add agents, graph RAG, MCP, browser automation, voice, auth, frontend apps, cloud deployment, or fine-tuning implementation yet.
- Do not add research, document editor, email/calendar/task, memory, or MCP lanes without a new ADR.
- Document future cloud portability before implementing it.

## Odysseus-Inspired Roadmap Boundary

Odysseus is product inspiration only. This repo should adopt useful ideas such
as a workspace cockpit, model compare, model cookbook, degraded-state reporting,
and a local admin-style security model. It must not copy Odysseus AGPL source
code or implement broad workspace features without later ADRs.

## Architecture Governance

- `AGENTS.md` is the operating agreement for all agents.
- ADRs in `docs/adr/` record architecture decisions.
- Architecture direction must not change without a new ADR.
- `docs/product/odysseus-idea-extraction.md` records imported product ideas.
- `docs/product/ai-lab-os-build-plan.md` records the staged build plan.
