# Local LLM Benchmark

Repeatable local benchmark format for AI Lab OS model testing.

Start with `SPEC.md`. The v0.1 spec defines:

- The canonical prompt set: `ai-lab-local-llm-core-v0.1`
- The rubric version: `ai-lab-local-llm-rubric-v0.1`
- Raw response and evaluator evidence expectations
- The 0-100 scoring dimensions used by `skills/local-llm-eval`
- The normalized CSV fields needed by `apps/model-dashboard`

Harness-ready format proposals:

- `manifests/prompt-manifest-v0.1.json`
- `rubrics/rubric-scorecard-v0.1.json`
- `HARNESS_ASSETS.md`

This directory defines the benchmark contract only. It does not download,
install, run, or call any model.

## Dependency Posture

The v0.3 harness should stay Python stdlib-only. JSON Lines, CSV export,
Markdown reports, subprocess capture, file layout, and timing can all be handled
with standard library modules. If Harness Builder proposes a package, challenge
it against `AGENTS.md` before adding anything to `pyproject.toml`.
