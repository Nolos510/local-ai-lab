---
name: local-llm-eval
description: Use when evaluating local or open-weight language models with the AI Lab OS benchmark workflow, including raw prompt evidence, dashboard-compatible scores, run metadata, and keep/watchlist/skip recommendations.
---

# Local LLM Eval

Use this skill to turn benchmark runs into comparable local model evaluation records.

## Harness Contract

- Use `evals/local-llm-benchmark/SPEC.md` as the canonical v0.1 prompt set, rubric, artifact, and dashboard import contract when no newer spec is named.
- v0.1 does not define a runner command. Do not invent one. The harness directory defines the benchmark contract only and does not download, install, run, or call any model.
- Expected artifact root: `data/eval_results/<benchmark_run_id>/`.
- Source artifacts: `metadata.json`, `raw_responses.jsonl`, and `evidence.md`.
- Summary artifacts: `report.md` and `dashboard-import/models.csv`, `dashboard-import/model_runs.csv`, `dashboard-import/eval_scores.csv`, `dashboard-import/decisions.csv`.

## Workflow

1. Collect the benchmark source artifacts: `metadata.json`, `raw_responses.jsonl`, `evidence.md`, timing output, hardware notes, and any harness logs.
2. Normalize model and run metadata using dashboard field names where possible: `model_name`, `backend`, `format`, `quantization`, `context_window`, `hardware`, `temperature`, `top_p`, `tokens_per_sec`, and `ram_usage_gb`.
3. Preserve raw prompt evidence before summarizing. Do not invent missing timing, memory, or score values.
4. Score each benchmark dimension on a 0-100 scale: `instruction_following`, `truthfulness_uncertainty`, `reasoning`, `coding_debugging`, `agent_planning`, `local_ai_lab_usefulness`, `research_synthesis`, `business_seo_strategy`, `long_context`, `creativity`, and `speed_practicality`.
5. Calculate `total_score` as the mean of the eleven benchmark dimensions unless the harness provides a documented aggregate.
6. Assign one valid `final_label`: `DAILY_DRIVER`, `CODING_SPECIALIST`, `RESEARCH_SPECIALIST`, `AGENT_PLANNER`, `CREATIVE_WRITER`, `LOCAL_AI_ASSISTANT`, `SEO_BUSINESS_HELPER`, `MULTIMODAL_SPECIALIST`, `SANDBOX_ONLY`, `WATCHLIST`, or `SKIP`.
7. End with a dashboard-ready decision: `keep`, `watchlist`, `retest`, or `skip`, plus best use case, weakness, and retest condition.

## Benchmark Notes

- Treat the benchmark output as the source of truth and the dashboard schema as the summary target.
- Keep raw per-prompt observations separate from dashboard summary fields.
- v0.1 IDs are `benchmark_run_id`, `prompt_set_id`, `rubric_version`, and `prompt_id`; carry benchmark-only IDs into the report source section or `run_notes`.
- The baseline prompt set is `ai-lab-local-llm-core-v0.1`; the rubric version is `ai-lab-local-llm-rubric-v0.1`; prompt IDs run from `LLMCORE-v0.1-001` through `LLMCORE-v0.1-012`.
- Prefer concise evidence quotes or paraphrases over full raw transcripts unless the user asks for full trace preservation.

## Output

Use `templates/report.md` for durable benchmark reports or import-prep notes. The report should mirror the same fields that feed the dashboard import CSVs.
