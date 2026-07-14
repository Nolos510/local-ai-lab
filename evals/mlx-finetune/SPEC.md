# MLX-LM Fine-Tuning Scaffold Spec

Version: `mlx-finetune-scaffold-v0.1`

## Purpose

Define the metadata and review artifacts required before any local MLX-LM LoRA
fine-tuning experiment is allowed. This is a planning scaffold only.

## Dataset Manifest

Required fields:

- `dataset_id`
- `local_source_path`
- `dataset_hash`
- `task_type`
- `license_provenance_notes`
- `privacy_classification`
- `train_validation_split_notes`

Recommended optional fields:

- `record_count`
- `format`
- `created_at`
- `reviewer`
- `allowed_use`
- `forbidden_use`

`dataset_hash` should use a stable digest such as `sha256:<64 hex chars>` once
the dataset is finalized. Private or internal datasets must not be committed.

## Adapter Registry

Required columns:

- `adapter_id`
- `base_model`
- `adapter_path`
- `dataset_manifest_path`
- `prompt_template_version`
- `eval_report_path`
- `approval_state`
- `created_at`
- `notes`

Allowed `approval_state` values:

- `planned`
- `dataset_reviewed`
- `training_approved`
- `trained_local`
- `eval_pending`
- `approved_for_serving`
- `rejected`

## Command Template

The MLX-LM command template is Markdown only. It must contain explicit local path
placeholders and a visible "do not run until approved" warning. It must not be an
executable script.

## Eval Before/After

Every adapter experiment should link to either:

- the local benchmark prompt set under `evals/local-llm-benchmark/prompts/`; or
- a RAG answer/citation eval set under `evals/rag-answer/`.

The report captures before score, after score, regression notes, and
keep/retest decision. Adapter improvements are not accepted unless regressions
are reviewed.
