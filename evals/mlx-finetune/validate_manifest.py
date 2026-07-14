#!/usr/bin/env python3
"""Offline validators for MLX-LM fine-tuning scaffold files.

The validator checks metadata shape only. It does not read dataset contents,
execute training commands, download models, or import MLX-LM.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REQUIRED_DATASET_FIELDS = {
    "dataset_id",
    "local_source_path",
    "dataset_hash",
    "task_type",
    "license_provenance_notes",
    "privacy_classification",
    "train_validation_split_notes",
}

REQUIRED_ADAPTER_COLUMNS = {
    "adapter_id",
    "base_model",
    "adapter_path",
    "dataset_manifest_path",
    "prompt_template_version",
    "eval_report_path",
    "approval_state",
    "created_at",
    "notes",
}

ALLOWED_APPROVAL_STATES = {
    "planned",
    "dataset_reviewed",
    "training_approved",
    "trained_local",
    "eval_pending",
    "approved_for_serving",
    "rejected",
}

HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ValidationError(ValueError):
    """Raised when a scaffold artifact does not match the offline convention."""


def _non_empty(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def validate_dataset_manifest(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(
        field for field in REQUIRED_DATASET_FIELDS if not _non_empty(data.get(field))
    )
    if missing:
        raise ValidationError(
            "dataset manifest missing required fields: {}".format(", ".join(missing))
        )
    dataset_hash = str(data["dataset_hash"]).strip()
    if not HASH_PATTERN.match(dataset_hash):
        raise ValidationError("dataset_hash must match sha256:<64 lowercase hex chars>")
    local_source_path = str(data["local_source_path"]).strip()
    if "://" in local_source_path:
        raise ValidationError("local_source_path must be a local path, not a URL")
    return data


def validate_adapter_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = sorted(REQUIRED_ADAPTER_COLUMNS - set(reader.fieldnames or []))
        if missing_columns:
            raise ValidationError(
                "adapter registry missing columns: {}".format(", ".join(missing_columns))
            )
        rows = list(reader)
    if not rows:
        raise ValidationError("adapter registry must contain at least one row")
    for index, row in enumerate(rows, start=2):
        missing = sorted(
            field for field in REQUIRED_ADAPTER_COLUMNS if not _non_empty(row.get(field))
        )
        if missing:
            raise ValidationError(
                "adapter registry row {} missing fields: {}".format(index, ", ".join(missing))
            )
        approval_state = row["approval_state"].strip()
        if approval_state not in ALLOWED_APPROVAL_STATES:
            raise ValidationError(
                f"adapter registry row {index} has unknown approval_state: {approval_state}"
            )
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate MLX-LM scaffold metadata offline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dataset_parser = subparsers.add_parser("dataset", help="Validate a dataset manifest JSON.")
    dataset_parser.add_argument("path", type=Path)
    dataset_parser.set_defaults(func=lambda args: validate_dataset_manifest(args.path))

    registry_parser = subparsers.add_parser(
        "adapter-registry", help="Validate an adapter registry CSV."
    )
    registry_parser.add_argument("path", type=Path)
    registry_parser.set_defaults(func=lambda args: validate_adapter_registry(args.path))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (OSError, json.JSONDecodeError, csv.Error, ValidationError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
