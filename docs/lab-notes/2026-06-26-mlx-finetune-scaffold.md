# V4 MLX-LM Fine-Tuning Scaffold

Date: 2026-06-26

This pass adds a scaffold for future MLX-LM LoRA experiments. It is metadata and
documentation only.

## Added

- `evals/mlx-finetune/SPEC.md`
- dataset manifest template;
- adapter registry template;
- Markdown-only MLX-LM LoRA command template;
- eval-before/eval-after report template;
- offline stdlib validator;
- pytest coverage for scaffold validation and command-template safety.

## Boundaries

- No training command executes.
- No model downloads or installs are added.
- No dataset contents are read or processed.
- No private file paths, prompts, records, secrets, or telemetry are committed.
- Fine-tuning remains separate from the v0 RAG/provider harness.

## Next Approval Gate

Before the first local experiment, require:

1. reviewed dataset manifest with hash and privacy classification;
2. reviewed base model and local runtime path;
3. eval-before baseline artifact;
4. explicit operator approval for local training;
5. eval-after report with regression notes and keep/retest decision.
