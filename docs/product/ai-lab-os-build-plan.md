# AI Lab OS Build Plan

This is the staged plan for turning `local-ai-lab` into the canonical local AI
lab and AI Lab OS workspace.

## Current Canonical Layout

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

## Stage 0: Consolidation And Hygiene

Status: in progress.

- Use `local-ai-lab` as the canonical private repo.
- Fold reviewed AI Lab OS modules into the canonical layout.
- Keep `src/local_ai_lab/` focused on RAG/provider/API code.
- Keep dashboard/eval/radar modules separate from the RAG harness.
- Remove raw response logs and private local paths from the GitHub copy.
- Keep Odysseus as product inspiration only; copy no AGPL code.

Exit criteria:

- Combined tests run through `uv run pytest`.
- Dashboard smoke test runs.
- Raw/generated benchmark artifacts are either omitted or explicitly sanitized.
- Architecture docs and ADRs describe the merge.

## Stage 1: Workspace Cockpit

Goal: make `/lab` the operating dashboard for daily local AI lab work.

Build:

- Lab health summary.
- Provider/runtime readiness summary.
- Model inventory status from registries and doctor checks.
- Benchmark artifact status.
- Radar candidates and next actions.
- Recent decisions and reports.

Do not build:

- Agents.
- MCP.
- Browser automation.
- Cloud services.

## Stage 2: Model Compare

Goal: compare local models on repeatable prompts with reviewable evidence.

Build:

- Same-prompt comparison across two local models.
- Blind review mode where practical.
- Vote, tie, reveal, and decision history.
- Links to prompt IDs, model IDs, runtime profiles, scores, and artifacts.

Guardrails:

- No hidden downloads.
- No hidden cloud calls.
- No raw prompts/responses committed without review.

## Stage 3: Model Cookbook

Goal: make model selection and runtime setup obvious on Apple Silicon.

Status: thin read-only slice implemented through `/cookbook`.

Build:

- Hardware-aware fit guidance from existing registry metadata.
- Runtime readiness from existing local runner/model ID fields.
- Exact remediation commands for inspecting LM Studio and Ollama model IDs.
- Status labels such as loadable, benchmarked, security review, blocked, and
  needs runtime ID.

Guardrails:

- Do not infer license/safety claims without source evidence.
- Do not turn candidate records into eval scores.
- Do not scan local runtimes or run models from this page.

## Stage 4: Degraded-State Reporting

Goal: make partial local lab failures clear and actionable.

Build status checks for:

- Qdrant.
- Open WebUI.
- Ollama endpoint and selected model.
- LM Studio endpoint and selected model ID.
- Dashboard DB.
- Benchmark artifact completeness.
- Sanitization status for GitHub-safe summaries.

## Stage 5: RAG And Dashboard Integration

Goal: connect the RAG backbone and dashboard without collapsing boundaries.

Build:

- Dashboard links to RAG smoke status.
- RAG eval artifacts visible in reports.
- Citation quality metrics.
- Retrieval failure notes.

Keep separate:

- RAG API implementation under `src/local_ai_lab/`.
- Dashboard UI under `apps/model-dashboard/`.
- Benchmark harness under `evals/local-llm-benchmark/`.

## Later Workspace Lanes

Each lane requires a new ADR before implementation:

- Deep research with source capture and report output.
- Document intelligence/editor workflows.
- Memory and reusable workflow skills.
- Agents and MCP tool orchestration.
- Browser automation.
- Email/calendar/tasks.
- Cloud portability implementation.

## Validation Commands

Core checks:

```bash
uv sync
docker compose config
uv run ruff check .
uv run pytest
```

Dashboard/eval checks:

```bash
python3 scripts/model_dashboard_smoke.py
python3 -m unittest discover -s evals/local-llm-benchmark/tests
```

Manual smoke checks:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
python3 apps/model-dashboard/run_dashboard.py serve --demo
```

Open the dashboard at:

```text
http://127.0.0.1:8765/lab
```
