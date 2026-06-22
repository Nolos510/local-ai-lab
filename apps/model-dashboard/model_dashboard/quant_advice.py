"""Read-only local quant advice loader for the dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_saved_quant_advice(advice_dir: Path, *, limit: int = 12) -> list[dict[str, str]]:
    if not advice_dir.exists():
        return []

    rows: list[dict[str, str]] = []
    for path in sorted(advice_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.extend(_rows_from_payload(payload, path.name))
        if len(rows) >= limit:
            break
    return rows[:limit]


def _rows_from_payload(payload: dict[str, Any], filename: str) -> list[dict[str, str]]:
    base_repo_id = str(payload.get("base_repo_id") or "")
    candidate_id = str(payload.get("candidate_id") or "")
    rows: list[dict[str, str]] = []
    for option in payload.get("options") or []:
        if not isinstance(option, dict):
            continue
        rows.append(
            {
                "base_repo_id": base_repo_id,
                "candidate_id": candidate_id,
                "artifact_repo_id": str(option.get("artifact_repo_id") or ""),
                "runtime": str(option.get("runtime") or ""),
                "quantization": str(option.get("quantization") or ""),
                "recommendation": str(option.get("recommendation") or ""),
                "approval_state": str(option.get("approval_state") or ""),
                "next_step": _next_step(option),
                "source_file": filename,
            }
        )
    return rows


def _next_step(option: dict[str, Any]) -> str:
    recommendation = str(option.get("recommendation") or "")
    approval_state = str(option.get("approval_state") or "")
    if recommendation == "needs_quantized_artifact":
        return "Choose an approved GGUF artifact source before benchmarking."
    if approval_state == "ready_for_local_benchmark":
        return "Run a local benchmark with the exact registered model id."
    return "Review source, license, provenance, and local model id before any run."
