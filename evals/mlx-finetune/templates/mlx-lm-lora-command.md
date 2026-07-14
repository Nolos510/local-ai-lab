# MLX-LM LoRA Command Template

Status: do not run until approved.

This is a Markdown planning template, not an executable script. Replace every
placeholder with reviewed local paths after dataset, base model, license,
privacy, and runtime approval.

## Required Approvals

- Dataset manifest reviewed.
- Dataset hash recorded.
- Base model already installed locally.
- Adapter output path chosen.
- Eval-before baseline completed.
- Operator explicitly approves local training run.

## Placeholder Command

```bash
# DO NOT RUN UNTIL APPROVED.
# Replace placeholders with local paths only.
python -m mlx_lm.lora \
  --model /absolute/local/path/to/base-model \
  --train \
  --data /absolute/local/path/to/dataset-dir \
  --adapter-path /absolute/local/path/to/output-adapter \
  --iters <approved_iteration_count> \
  --batch-size <approved_batch_size> \
  --learning-rate <approved_learning_rate>
```

## Run Notes To Capture

- MLX-LM version.
- macOS version and hardware snapshot.
- Base model path and hash/checksum status.
- Dataset manifest path and hash.
- Adapter output path.
- Training command after placeholders are resolved.
- Eval-before and eval-after report paths.

## Forbidden In This Template

- Remote model IDs that trigger downloads.
- Model-card code execution.
- API keys or tokens.
- Private dataset paths in committed docs.
- Automatic upload, telemetry, or hub publishing.
