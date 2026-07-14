# MLX-LM Fine-Tuning Roadmap

Fine-tuning remains separate from the v0 RAG harness. The current repo includes
an offline scaffold under `evals/mlx-finetune/`; it does not train, download,
install, or preprocess private files.

Use the scaffold to make a future MLX-LM LoRA experiment narrow, measurable, and
reversible before any local training is approved.

## Recommended First Experiment

Train a LoRA adapter with MLX-LM for one specific behavior:

- structured extraction
- domain-specific response style
- tool-selection discipline
- local documentation Q&A tone

## Experiment Metadata

Each run should record:

- base model
- adapter path
- dataset hash
- dataset manifest path
- prompt template version
- privacy classification
- license/provenance notes
- eval set version
- training command after placeholders are resolved
- evaluation report path
- approval state

## Scaffold Files

- `evals/mlx-finetune/SPEC.md`: required metadata conventions.
- `evals/mlx-finetune/templates/dataset-manifest.example.json`: dataset
  manifest fields and hash convention.
- `evals/mlx-finetune/templates/adapter-registry.csv`: adapter registry columns
  and approval states.
- `evals/mlx-finetune/templates/mlx-lm-lora-command.md`: Markdown-only local
  command template with approval warnings.
- `evals/mlx-finetune/templates/eval-before-after-report.md`: before/after eval
  and regression review template.

## Offline Validation

```bash
python3 evals/mlx-finetune/validate_manifest.py dataset \
  evals/mlx-finetune/templates/dataset-manifest.example.json

python3 evals/mlx-finetune/validate_manifest.py adapter-registry \
  evals/mlx-finetune/templates/adapter-registry.csv
```

The validator checks metadata shape only. It does not read dataset contents,
import MLX-LM, execute commands, or call a model.

## Approval Rules

- Do not run training until dataset privacy, license/provenance, base model,
  local paths, and eval-before baseline are approved.
- Do not use remote model IDs that trigger downloads.
- Do not commit private dataset paths, private records, prompts, retrieved
  chunks, API keys, or secrets.
- Keep adapter evaluation tied to either the local benchmark prompt set or the
  RAG answer/citation eval set.
- Record regressions before any keep or serving decision.

## TODO

- [x] Add dataset manifest schema.
- [x] Add MLX-LM command templates.
- [x] Add adapter registry document.
- [x] Add eval-before/eval-after report template.
- [ ] Run the first approved local experiment after dataset/base-model review.
