---
name: local-llm-eval
description: Use when evaluating local or open-weight language models with repeatable prompts, rubric scoring, speed and memory notes, and keep/delete recommendations for AI Lab OS.
---

# Local LLM Eval

Use this skill to turn ad hoc local model testing into comparable evaluation notes.

## Workflow

1. Confirm the model, backend, quantization, hardware, and task mix.
2. Run or inspect repeatable prompts before judging quality.
3. Capture latency, tokens per second, memory pressure, failures, and stability notes when available.
4. Score results against the requested rubric or a simple 1-5 task-fit scale.
5. End with a clear keep, retest, or delete recommendation and the reason.

## Output

Prefer the template in `templates/report.md` when the user wants a durable record.
