"""Read-only capability context for the local dashboard."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ACCEPTABLE_SECURITY_STATES = {
    "approved",
    "local_inventory_reviewed",
    "not_needed_local",
    "reviewed_local",
}
ACCEPTABLE_DOWNLOAD_STATES = {
    "approved",
    "not_needed_local",
    "not_required",
    "local_only",
}


def load_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def candidate_readiness_counts(candidates: list[dict[str, str]]) -> dict[str, int]:
    counts = {
        "total": len(candidates),
        "ready_for_eval": 0,
        "watchlist": 0,
        "needs_more_info": 0,
        "skip": 0,
        "blocked": 0,
        "runnable_ready": 0,
        "blocked_ready": 0,
    }
    for row in candidates:
        status = row.get("status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
        if status == "ready_for_eval":
            if candidate_blocked_reasons(row):
                counts["blocked_ready"] += 1
            else:
                counts["runnable_ready"] += 1
    return counts


def candidate_blocked_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    security_state = (row.get("security_review_status") or "").lower()
    download_state = (row.get("download_approval") or "").lower()
    if not row.get("local_runner"):
        reasons.append("missing local_runner")
    if not row.get("local_model_id"):
        reasons.append("missing local_model_id")
    if security_state not in ACCEPTABLE_SECURITY_STATES:
        reasons.append(f"security_review_status={security_state or 'missing'}")
    if download_state not in ACCEPTABLE_DOWNLOAD_STATES:
        reasons.append(f"download_approval={download_state or 'missing'}")
    return reasons


def benchmark_artifact_counts(eval_results_dir: Path) -> dict[str, int]:
    counts = {
        "total": 0,
        "with_raw_responses": 0,
        "with_scores": 0,
        "with_draft_scores": 0,
        "with_decisions": 0,
        "with_dashboard_import": 0,
    }
    if not eval_results_dir.exists():
        return counts
    for path in eval_results_dir.iterdir():
        if not path.is_dir():
            continue
        counts["total"] += 1
        if (path / "raw_responses.jsonl").exists():
            counts["with_raw_responses"] += 1
        if (path / "scores.json").exists():
            counts["with_scores"] += 1
        if (path / "draft-scores.json").exists():
            counts["with_draft_scores"] += 1
        if (path / "decision.json").exists():
            counts["with_decisions"] += 1
        if (path / "dashboard-import").exists():
            counts["with_dashboard_import"] += 1
    return counts


def load_hardware_profiles(root: Path, *, limit: int = 3) -> list[dict[str, object]]:
    if not root.exists():
        return []
    profiles = []
    for path in sorted(root.glob("*hardware*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        profiles.append(summarize_hardware_profile(path.name, payload))
    return profiles[-limit:]


def summarize_hardware_profile(filename: str, payload: dict[str, object]) -> dict[str, object]:
    os_info = _dict_value(payload, "os")
    machine = _dict_value(payload, "machine")
    macos = _dict_value(payload, "macos")
    python = _dict_value(payload, "python")
    runtimes = _dict_value(payload, "runtimes")
    return {
        "filename": filename,
        "captured_at": str(payload.get("captured_at") or ""),
        "schema_version": str(payload.get("schema_version") or ""),
        "os": " ".join(
            value
            for value in (str(os_info.get("system") or ""), str(os_info.get("release") or ""))
            if value
        ),
        "python": " ".join(
            value
            for value in (
                str(python.get("implementation") or ""),
                str(python.get("version") or ""),
            )
            if value
        ),
        "machine": str(machine.get("machine") or ""),
        "cpu_count": machine.get("cpu_count") or "",
        "chip": macos.get("chip_brand") or "",
        "memory_gb": _memory_gb(macos.get("memory_bytes")),
        "runtimes_present": sorted(
            name
            for name, value in runtimes.items()
            if isinstance(value, dict) and value.get("present")
        ),
    }


def _dict_value(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _memory_gb(value: object) -> str:
    try:
        return f"{int(value) / (1024**3):.1f}"
    except (TypeError, ValueError):
        return ""
