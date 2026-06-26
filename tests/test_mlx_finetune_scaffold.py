import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD_DIR = REPO_ROOT / "evals" / "mlx-finetune"
VALIDATOR = SCAFFOLD_DIR / "validate_manifest.py"
DATASET_TEMPLATE = SCAFFOLD_DIR / "templates" / "dataset-manifest.example.json"
ADAPTER_REGISTRY = SCAFFOLD_DIR / "templates" / "adapter-registry.csv"
COMMAND_TEMPLATE = SCAFFOLD_DIR / "templates" / "mlx-lm-lora-command.md"
EVAL_TEMPLATE = SCAFFOLD_DIR / "templates" / "eval-before-after-report.md"


def run_validator(*args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_dataset_manifest_template_validates_offline():
    result = run_validator("dataset", str(DATASET_TEMPLATE))

    assert result.returncode == 0, result.stderr
    assert "validation passed" in result.stdout


def test_adapter_registry_template_validates_offline():
    result = run_validator("adapter-registry", str(ADAPTER_REGISTRY))

    assert result.returncode == 0, result.stderr
    assert "validation passed" in result.stdout


def test_dataset_manifest_rejects_remote_source_and_bad_hash(tmp_path):
    bad_manifest = tmp_path / "bad-dataset.json"
    data = json.loads(DATASET_TEMPLATE.read_text(encoding="utf-8"))
    data["local_source_path"] = "https://example.com/private.jsonl"
    data["dataset_hash"] = "sha256:not-a-real-hash"
    bad_manifest.write_text(json.dumps(data), encoding="utf-8")

    result = run_validator("dataset", str(bad_manifest))

    assert result.returncode == 2
    assert "dataset_hash" in result.stderr

    data["dataset_hash"] = "sha256:" + ("a" * 64)
    bad_manifest.write_text(json.dumps(data), encoding="utf-8")
    result = run_validator("dataset", str(bad_manifest))

    assert result.returncode == 2
    assert "local_source_path" in result.stderr


def test_command_template_is_non_executable_markdown_only():
    text = COMMAND_TEMPLATE.read_text(encoding="utf-8")
    mode = os.stat(COMMAND_TEMPLATE).st_mode

    assert "DO NOT RUN UNTIL APPROVED" in text
    assert "/absolute/local/path/to/base-model" in text
    assert not (mode & 0o111)
    assert not list(SCAFFOLD_DIR.rglob("*.sh"))


def test_eval_before_after_template_tracks_regressions_and_decision():
    text = EVAL_TEMPLATE.read_text(encoding="utf-8")

    assert "Before Scores" in text
    assert "After Scores" in text
    assert "Regression Notes" in text
    assert "Decision: keep / retest / reject" in text
