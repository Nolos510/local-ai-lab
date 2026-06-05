# AGENTS.md

Guidance for Codex and other automation working in this repository.

## 1. Project Mission

`local-ai-lab` / AI Lab OS is a local-first Apple Silicon AI engineering lab
for reproducible private AI workflows on a Mac Studio with 256 GB unified
memory. The project combines a local RAG/provider harness with a model radar,
benchmark harness, evaluation artifacts, and dashboard workflow for deciding
which local models and project opportunities are worth keeping.

## 2. Current Product Lines

- **Local RAG Backbone + Provider Harness:** CLI/FastAPI ingestion, chunking,
  Qdrant retrieval, prompt assembly, and local model providers.
- **AI Lab OS Dashboard Loop:** radar candidate intake, local benchmark runs,
  draft/confirmed scoring, dashboard import, model comparison, and
  keep/watchlist/retest/skip decisions.

## 3. Non-Negotiable Local-First Rules

- Do not add hidden cloud calls, cloud API clients, model download logic, or
  secrets.
- Keep Open WebUI optional and parallel; the FastAPI RAG harness must not
  depend on it.
- Use Qdrant as the v0 vector database.
- Keep model-provider abstractions small, explicit, and testable.
- Treat model runtimes as native macOS tools by default: Ollama, LM Studio,
  MLX/MLX-LM, and llama.cpp.
- Do not change architecture direction without an ADR in `docs/adr/`.
- Logs must not dump user documents, prompts, retrieved chunks, API keys, or
  private paths by default.

## 4. Dashboard, Benchmark, And Radar Rules

- Prefer small, auditable changes that preserve the current dashboard behavior.
- Keep `apps/model-dashboard` dependency-light. Add runtime dependencies only
  when the app imports and needs them.
- Keep the local LLM benchmark harness stdlib-only unless a dependency clears
  the dependency review gate below.
- Treat `data/dashboard/*.sqlite` and dashboard export folders as local runtime
  state.
- Radar candidates are review records, not eval scores.
- External Radar may gather public metadata on demand, but it must not download
  models, run models, call model APIs, add API clients, or register candidates
  without explicit approval.
- Candidate-only project records belong under `data/project_registry`; do not
  turn GitHub project opportunities into model eval scores.

## 5. Dependency Review Gate

Before adding any dependency, challenge it:

- Can `argparse`, `csv`, `json`, `sqlite3`, `subprocess`, `pathlib`,
  `tempfile`, `time`, `unittest`, or another stdlib module cover the need?
- Is the dependency runtime code, or only a developer/test tool?
- Does the dependency download models, call cloud APIs, require credentials, or
  pull in heavy transitive packages? Reject it unless the user explicitly
  approves a scope change.
- Can the dashboard, harness, or radar lane write JSONL, CSV, Markdown, and
  dashboard imports without it?
- If a dependency is accepted, document the exact missing capability, expected
  import location, transitive risk, and removal plan.

Do not add vendored packages, ad hoc requirements files, or global install
instructions. Keep declared Python dependencies centralized in `pyproject.toml`
and `uv.lock`.

## 6. Python Environment Rules

- Use `uv` as the default workflow for the local RAG/provider app.
- Keep `pyproject.toml`, `uv.lock`, `.python-version`, and `.env.example` in
  sync.
- Do not introduce Conda/Mamba or a primary `requirements.txt` workflow.
- For dashboard-only validation, the stdlib `unittest` and smoke commands are
  valid when dependency installation is not needed.
- If using a venv manually, create it with `python3`, activate it, then use
  `python` or `python -m pip` from the virtualenv.

## 7. Allowed v0 Scope

- CLI and FastAPI entry points.
- Markdown/text ingestion.
- Basic chunking with source metadata.
- Qdrant indexing and retrieval.
- Prompt assembly with citations.
- Ollama and LM Studio/OpenAI-compatible provider harnesses.
- Deterministic/mock providers for tests and offline smoke checks.
- Documentation, tests, CI, roadmaps, and TODOs.

## 8. Forbidden v0 Scope

- Agents or multi-agent orchestration in the RAG runtime.
- Graph RAG.
- Voice/STT/TTS workflows.
- Auth systems.
- Cloud deployment implementation.
- Fine-tuning implementation.
- Large speculative abstractions or framework sprawl.

## 9. Coding And Documentation Standards

- Keep changes narrow and task-scoped.
- Follow existing package boundaries under `src/local_ai_lab/` and
  `apps/model-dashboard/`.
- Prefer simple functions and small protocols over deep inheritance.
- Avoid hidden global state except cached settings.
- Keep public interfaces typed and covered by focused tests.
- Update docs and lab notes when behavior, configuration, validation, or safety
  posture changes.
- Document future work as TODOs or roadmap items, not half-built code.

## 10. Testing Standards

- Add or update tests when behavior changes.
- Prefer unit tests with fakes for provider boundaries.
- Keep live Qdrant or local model checks as smoke/integration steps, not
  default unit-test requirements.
- If a required command cannot run locally, document the exact reason in PR
  notes or handoff notes.
- Do not claim a command passed unless it was actually run.

## 11. Validation Commands

Always-runnable local/code checks for the RAG/provider app:

```bash
uv sync
docker compose config
uv run ruff check .
uv run pytest
```

Local RAG smoke checks requiring Qdrant and indexed docs, but not a real model:

```bash
docker compose up -d qdrant
uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

Live local-model checks:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ask "What is this lab for?"
```

Dashboard and benchmark checks:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
```

To include a localhost server bind/probe check:

```bash
python3 scripts/model_dashboard_smoke.py --probe-server
```

The server probe binds to `127.0.0.1` by default and accepts only loopback
hosts. In sandboxed environments, `--probe-server` may need local bind/probe
approval.

The mock provider means "no real LLM call." It does not remove the Qdrant,
retrieval, settings, embedding, or indexed-document dependencies from the ask
path. Live local-model checks may fail if Ollama, LM Studio, Qdrant, or the
configured local model is missing; document the exact reason instead of treating
it as passed.

## 12. Git Workflow Rules

- Read this file before beginning work.
- Start by inspecting current files and git status.
- Identify ownership boundaries before editing shared modules.
- Coordinate before editing files another agent is actively changing.
- Do not rewrite unrelated files.
- Do not introduce major new dependencies without explanation.
- Prefer one main builder, multiple reviewers, and one integrator.
- Review agents should be read-only unless explicitly asked to patch.
- All PRs must describe what changed, why, how it was tested, and what was not
  tested.

## 13. Definition Of Done

- The change is scoped to the requested task.
- Architecture rules and local-first boundaries are preserved.
- Tests and docs are updated where appropriate.
- Required checks were run or clearly documented as not run.
- Privacy/security impact was reviewed.
- The handoff explains changed files, behavior, validation, and known
  limitations.
