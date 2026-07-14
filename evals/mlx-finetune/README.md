# MLX-LM Fine-Tuning Scaffold

This directory defines offline conventions for future MLX-LM LoRA experiments.
It does not train, download, install, or preprocess private files.

Use it to prepare reviewable experiment metadata before any fine-tuning run:

1. Create a dataset manifest from
   `templates/dataset-manifest.example.json`.
2. Register the planned adapter in a copy of
   `templates/adapter-registry.csv`.
3. Fill the command template in
   `templates/mlx-lm-lora-command.md` with local paths, but do not run it until
   the dataset, base model, and local runtime have approval.
4. Compare eval-before/eval-after results with
   `templates/eval-before-after-report.md`.

Validate scaffold files offline:

```bash
python3 evals/mlx-finetune/validate_manifest.py dataset \
  evals/mlx-finetune/templates/dataset-manifest.example.json

python3 evals/mlx-finetune/validate_manifest.py adapter-registry \
  evals/mlx-finetune/templates/adapter-registry.csv
```

## Local-First Boundaries

- No model downloads.
- No training command execution.
- No dataset processing of private paths.
- No cloud APIs, SDKs, telemetry, secrets, or credentials.
- All paths are explicit placeholders until user-approved local artifacts exist.
