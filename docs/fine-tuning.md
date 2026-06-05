# MLX-LM Fine-Tuning Roadmap

Fine-tuning is intentionally not implemented in v0. The first implementation should be narrow, measurable, and reversible.

## Recommended First Experiment

Train a LoRA adapter with MLX-LM for one specific behavior:

- structured extraction
- domain-specific response style
- tool-selection discipline
- local documentation Q&A tone

## Experiment Metadata

Each run should record:

- base model
- adapter config
- dataset hash
- prompt template version
- eval set version
- training command
- resulting adapter path
- evaluation report path

## TODO

- [ ] Add dataset manifest schema.
- [ ] Add MLX-LM command templates.
- [ ] Add adapter registry document.
- [ ] Add eval-before/eval-after report template.
