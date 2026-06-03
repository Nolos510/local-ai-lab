# AI Lab OS Roadmap

## Completed MVP Baseline

- Created the AI Lab OS monorepo structure.
- Added a dependency-free Python dashboard for local model performance tracking.
- Added SQLite persistence, CSV import/export, fixture data, scoring helpers, report generation, and unit tests.
- Added local-first docs and a task record for the dashboard MVP.

## Phase 1: Local Model Tracking

- Expand the Local Model Performance Dashboard with richer filters and model detail history.
- Add import scripts for benchmark output from LM Studio, Ollama, MLX, llama.cpp/GGUF, whisper.cpp, and ComfyUI where practical.
- Standardize the local model registry under `data/model_registry`.

## Phase 2: Evaluation Harness

- Build `evals/local-llm-benchmark` around repeatable local prompts and rubric scoring.
- Capture speed, RAM use, context handling, instruction following, coding, research synthesis, and agent planning.
- Keep raw runs and summarized results importable into the dashboard.
- Keep the v0.3 harness stdlib-only unless a dependency passes the documented dependency review gate.

## Phase 3: AI Lab Radar

- Use `automations/ai-lab-radar` to track newly interesting local and open-weight models.
- Store radar findings as review candidates instead of auto-downloading anything.
- Connect radar output to the model registry and task queue.
- Current scaffold defines candidate schema, report template, and local-first boundaries.

## Phase 4: Workflow Skills and Briefs

- Flesh out the skill library for local LLM evals, research briefs, code review, PRD-to-task conversion, resume bullets, and SEO audits.
- Test each skill on one real repo, research, or writing task.
- Add examples from successful runs once the workflows prove useful.
- Refine the templates after repeated use.
- Consider metadata polish if the skill library becomes shared outside this repo.
- Add weekly briefs for lab, finance, technology, and geopolitics once the local data model is stable.

## Phase 5: Evidence and Portfolio

- Turn completed tasks into docs under `docs/portfolio` and `docs/resume-evidence`.
- Export concise project evidence from benchmark results, dashboard reports, and implementation notes.
