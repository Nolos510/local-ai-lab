# Answers Sprint: Fit Advisor, Task Leaders, And Batch Queue

Date: 2026-07-14

## Summary

The answers sprint turned existing local hardware, model metadata, confirmed
scores, and benchmark runner records into three direct operator answers:

1. **Can this machine run it?** A Fit Advisor surfaces a labeled memory
   estimate on Home, Discover, and My Models.
2. **Which scored model leads for this task?** Home and Benchmark show task
   leaders derived only from confirmed eval rows.
3. **How can the evidence set grow?** `ai-lab bench queue` runs an explicitly
   enumerated, approval-gated batch of ready local candidates.

The sprint added no default runtime dependencies, cloud calls, model downloads,
secrets, or automatic model registration.

## Fit Advisor

The dependency-free estimator uses:

```text
estimated weights GB = parameters (billions) * quantization bits / 8 * 1.1
estimated memory GB = estimated weights GB + 8 GB context/runtime allowance
available budget GB = machine memory GB - 16 GB system reserve
```

Results are classified as `comfortable`, `fits`, `tight`, or `exceeds` against
the available budget. Missing or malformed parameter/quantization metadata
returns `unknown`; it is not silently guessed. The UI labels capacity values as
estimates and shows observed tokens/sec separately only when an imported real
benchmark run provides it.

## Confirmed Task Leaders

The recommender groups existing score dimensions into Coding, Reasoning &
agents, Research & writing, Long context, and Fast & practical. Draft scores are
excluded and exact ties remain visible. The UI omits the panel when no confirmed
scores exist and adds an explicit warning when only one model is scored.

At this date the repository has confirmed scored evidence for only two unique
models: Qwen3 Coder and Dolphin-Mistral 24B. Task leaders are therefore a view of
those two local evidence records, not a recommendation across the wider model
market.

## Approval-Gated Batch Queue

`uv run ai-lab bench queue` requires at least two selected
`ready_for_eval` candidates. Before execution it prints the complete candidate,
exact local model id, runner, and run-id enumeration. One
`--i-approve-local-run` flag applies only to that printed batch.

The queue refuses the full batch before any model call when a selected row has
missing or invalid runtime metadata. Once approved, candidates run sequentially;
one failed run does not prevent later candidates from running. The final summary
reports per-run status plus latency and tokens/sec when those measurements exist
in the generated local artifact.

No live batch was executed as part of this documentation refresh.

## Validation

The final repository gate for the sprint documentation was:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

These checks exercise the estimator boundaries and rendering, confirmed/draft
score filtering and tie behavior, queue preflight/approval and partial-failure
handling, dashboard smoke path, and repository lint. They do not call a live
model or prove that any untested candidate fits or performs well.
