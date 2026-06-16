# ADR 0003: AI Lab OS consolidation into local-ai-lab

## Status

Accepted

## Context

`local-ai-lab` started as the canonical local RAG/provider harness with strong
governance, provider error handling, LM Studio/Ollama runtime docs, Qdrant,
Open WebUI, tests, and CI discipline.

`ai-lab-os` developed a complementary product loop: model dashboard, local LLM
benchmark harness, model registry, project registry, eval result artifacts,
radar workflow docs, and portfolio/learning evidence.

The project should not remain split across two repos. The final system needs
one private canonical repo that can support local RAG, model runtime testing,
benchmarking, dashboard review, and future portfolio evidence without losing
local-first discipline.

Odysseus was reviewed as product inspiration because it is a broad self-hosted
AI workspace covering chat, agents, research, documents, email, notes, calendar,
local model workflows, comparison, and security posture. It is AGPL-licensed
and much broader than this repo, so it is not a code source for this project.

## Decision

- Use `Nolos510/local-ai-lab` as the canonical repository.
- Treat AI Lab OS as a product lane inside `local-ai-lab`, not as a separate
  repo.
- Keep the existing local RAG/provider harness under `src/local_ai_lab/`.
- Keep the AI Lab OS dashboard under `apps/model-dashboard/`.
- Keep the repeatable benchmark harness under `evals/local-llm-benchmark/`.
- Keep model and project registries under `data/model_registry/` and
  `data/project_registry/`.
- Keep sanitized benchmark summaries, templates, dashboard import CSVs, and
  evidence notes under `data/eval_results/`.
- Omit raw model responses, raw logs, secrets, private paths, and local machine
  metadata from the GitHub copy unless they are intentionally redacted sample
  fixtures.
- Use Odysseus only as product/architecture inspiration. Do not copy Odysseus
  source code, templates, assets, or implementation details.

## Consequences

- The repo becomes a single local AI lab system instead of two overlapping
  scaffolds.
- Dashboard/eval/radar work can share governance, CI, docs, and privacy rules
  with the RAG/provider harness.
- Local benchmark artifacts need stricter hygiene before they are committed.
- Future workspace features inspired by Odysseus must be designed behind this
  repo's local-first architecture instead of imported wholesale.
- Any agent, research, document editor, email/calendar/task, memory, or MCP
  implementation requires a later ADR before code is added.

## Alternatives Considered

### Keep two repos

Rejected because it duplicates architecture decisions, docs, dashboard evidence,
and runtime setup. It also increases the chance that agents modify the wrong
repo.

### Make ai-lab-os canonical

Rejected because `local-ai-lab` already has the cleaner governance, provider
error handling, FastAPI/CLI RAG harness, Qdrant/Open WebUI setup, runtime docs,
tests, and CI posture.

### Import Odysseus directly

Rejected because Odysseus is AGPL-licensed, much broader in scope, and already
implements many features this repo is deliberately postponing. The correct use
is product extraction, not source copying.

### Build a full workspace immediately

Rejected because the current value is a measured local lab, not a speculative
all-in-one platform. Workspace lanes are roadmap items until the RAG/provider
and dashboard/eval loops are stable.

## Follow-up Work

- Keep `docs/product/odysseus-idea-extraction.md` as the idea source map.
- Keep `docs/product/ai-lab-os-build-plan.md` as the staged product plan.
- Add artifact hygiene checks before publishing benchmark exports.
- Add ADRs before implementing research, documents, memory, agents, MCP, or
  email/calendar/task lanes.
- Consider a future public portfolio branch with only curated docs, screenshots,
  and sanitized benchmark summaries.
