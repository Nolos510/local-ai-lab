# Local LLM Eval

Reusable instructions for turning local benchmark runs into comparable AI Lab OS evaluation records.

Use this when comparing model quality, speed, memory behavior, stability, and whether a model belongs in the lab as a daily driver, specialist, watchlist item, sandbox-only model, or skip.

The v0.1 benchmark contract lives in `evals/local-llm-benchmark/SPEC.md`. It does not include a runner command yet; use the spec, raw artifacts, and dashboard-import CSV layout as the source of truth.

Expected output: a benchmark report with source artifacts from `data/eval_results/<benchmark_run_id>/`, normalized run metadata, 0-100 rubric scores, raw-evidence notes, a valid final label, and a keep/watchlist/retest/skip decision.
