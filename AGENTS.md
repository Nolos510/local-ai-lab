# AGENTS.md

Operating agreement for AI agents working in `local-ai-lab`.

## 1. Project Mission

`local-ai-lab` is a local-first Apple Silicon AI engineering lab for reproducible private AI workflows on a Mac Studio with 256 GB unified memory. The project prioritizes local inference, local retrieval, evaluation, benchmarking, documentation, and future cloud portability without compromising privacy-first defaults.

## 2. Current Milestone

v0: Local RAG Backbone + Provider Harness.

Target flow:

```text
CLI / FastAPI
  -> ingestion
  -> chunking
  -> Qdrant retrieval
  -> prompt assembly
  -> local model provider
  -> answer + citations
```

## 3. Non-Negotiable Architecture Rules

- Keep the FastAPI RAG harness independent from Open WebUI.
- Treat Open WebUI as optional and parallel, not a runtime dependency.
- Use Qdrant as the v0 vector database.
- Keep model-provider abstractions small, explicit, and testable.
- Do not change architecture direction without an ADR in `docs/adr/`.
- Prefer one clear implementation path over competing frameworks.

## 4. Allowed v0 Scope

- CLI and FastAPI entry points.
- Markdown/text ingestion.
- Basic chunking with source metadata.
- Qdrant indexing and retrieval.
- Prompt assembly with citations.
- Ollama and LM Studio/OpenAI-compatible provider harnesses.
- Deterministic/mock providers for tests and offline smoke checks.
- Documentation, tests, CI, roadmaps, and TODOs.

## 5. Forbidden v0 Scope

- Agents or multi-agent orchestration.
- Graph RAG.
- MCP or browser automation.
- Voice/STT/TTS workflows.
- Auth systems.
- Frontend apps beyond optional Open WebUI configuration.
- Cloud deployment implementation.
- Fine-tuning implementation.
- Large speculative abstractions or framework sprawl.

## 6. Python Environment Rules

- Use `uv` as the default Python workflow.
- Keep `pyproject.toml`, `uv.lock`, `.python-version`, and `.env.example` in sync.
- Do not introduce Conda/Mamba or primary `requirements.txt` workflows.
- All Python commands in docs should run through `uv`.
- Do not add major dependencies without explaining why the existing stack is insufficient.

## 7. Docker and Local Runtime Rules

- Docker is for infrastructure services in v0: Qdrant and optional Open WebUI.
- Model runtimes stay native on macOS: Ollama, LM Studio, MLX/MLX-LM, and llama.cpp.
- Do not containerize Ollama, LM Studio, MLX, or llama.cpp as the default path.
- Future Docker/cloud portability may be documented but not implemented in v0.

## 8. Coding Standards

- Keep changes narrow and task-scoped.
- Follow existing package boundaries under `src/local_ai_lab/`.
- Prefer simple functions and small protocols over deep inheritance.
- Avoid hidden global state except cached settings.
- Keep public interfaces typed and covered by focused tests.
- Do not rewrite unrelated files or reformat broad areas without cause.

## 9. Documentation Standards

- Update docs when behavior, configuration, architecture, or workflow changes.
- Use ADRs for architecture decisions that affect runtime boundaries, provider strategy, storage, or dependency direction.
- Keep docs concise, operational, and command-oriented.
- Document future work as TODOs or roadmap items, not half-built code.

## 10. Testing Standards

- Add or update tests when behavior changes.
- Prefer unit tests with fakes for provider boundaries.
- Keep live Qdrant or local model checks as smoke/integration steps, not default unit-test requirements.
- If a required command cannot run locally, document the exact reason in PR notes.

## 11. Privacy and Security Rules

- No hidden cloud calls.
- Do not commit secrets.
- `.env.example` must contain only safe placeholder values.
- Logs must not dump user documents, prompts, retrieved chunks, API keys, or private paths by default.
- Local-first assumptions must remain intact.
- Telemetry must be opt-in or disabled by default where applicable.

## 12. Git Workflow Rules

- Read this file before beginning work.
- Keep changes narrow and task-scoped.
- Do not rewrite unrelated files.
- Do not introduce major new dependencies without explanation.
- Do not change architecture direction without an ADR.
- Do not merge your own work.
- Prefer one main builder, multiple reviewers, and one integrator.
- Review agents should be read-only unless explicitly asked to patch.
- All PRs must describe what changed, why, how it was tested, and what was not tested.

## 13. Agent Workflow Rules

- Start by inspecting current files and git status.
- Identify ownership boundaries before editing shared modules.
- Coordinate before editing files another agent is actively changing.
- Do not duplicate abstractions that already exist.
- Do not claim a command passed unless it was actually run.
- If blocked, record the blocker and the safest next step.

## 14. Required Checks Before Completion

Always-runnable local/code checks:

```bash
uv sync
docker compose config
uv run ruff check .
uv run pytest
LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

Live local-stack checks:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ingest --path data/sample_docs
uv run local-ai-lab ask "What is this lab for?"
```

`uv run local-ai-lab doctor` performs live Qdrant and selected model-provider checks. It may fail when Qdrant, Ollama, LM Studio, or the configured local model is not running. If Ollama is selected and reachable but the configured model is missing, `doctor` must keep returning nonzero; document that exact model-availability reason instead of treating it as passed.

If a command is not implemented, not relevant, blocked by local services, or cannot run in the current environment, explicitly document that in PR notes. Do not imply it passed.

## 15. Definition of Done

- The change is scoped to the requested task.
- Architecture rules and v0 boundaries are preserved.
- Tests and docs are updated where appropriate.
- Required checks were run or clearly documented as not run.
- Privacy/security impact was reviewed.
- The PR explains changed files, behavior, validation, and known limitations.
