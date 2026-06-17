"""Read-only benchmark planning matrix for AI Lab OS candidates."""

from __future__ import annotations

import csv
import json
from pathlib import Path

DEFAULT_STATUSES = ("ready_for_eval",)
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
        return list(csv.DictReader(handle))


def _normalized(value: str | None) -> str:
    return (value or "").strip()


def _normalized_lower(value: str | None) -> str:
    return _normalized(value).lower()


def _blocked_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    status = _normalized_lower(row.get("status"))
    runner = _normalized(row.get("local_runner"))
    local_model_id = _normalized(row.get("local_model_id"))
    security_state = _normalized_lower(row.get("security_review_status"))
    download_state = _normalized_lower(row.get("download_approval"))

    if status in {"blocked", "skip"}:
        reasons.append(f"status={status}")
    if not runner:
        reasons.append("missing local_runner")
    if not local_model_id:
        reasons.append("missing local_model_id")
    if security_state not in ACCEPTABLE_SECURITY_STATES:
        reasons.append(f"security_review_status={security_state or 'missing'}")
    if download_state not in ACCEPTABLE_DOWNLOAD_STATES:
        reasons.append(f"download_approval={download_state or 'missing'}")
    return reasons


def _benchmark_run_id(row: dict[str, str]) -> str:
    existing = _normalized(row.get("benchmark_run_id"))
    if existing:
        return existing
    candidate_id = _normalized(row.get("candidate_id"))
    if not candidate_id:
        return ""
    return f"{candidate_id}-r1"


def _next_step(row: dict[str, str], blocked_reasons: list[str]) -> str:
    if blocked_reasons:
        if any(reason == "missing local_model_id" for reason in blocked_reasons):
            return "Confirm exact local runtime model id before benchmarking."
        if any(reason.startswith("security_review_status=") for reason in blocked_reasons):
            return "Complete security review before benchmarking."
        if any(reason.startswith("download_approval=") for reason in blocked_reasons):
            return "Approve local artifact/download gate before benchmarking."
        return "Resolve blocked candidate state before benchmarking."
    proposed_eval = _normalized(row.get("proposed_eval"))
    return proposed_eval or "Ready to initialize benchmark artifact."


def matrix_row(row: dict[str, str]) -> dict[str, object]:
    blocked_reasons = _blocked_reasons(row)
    return {
        "candidate_id": _normalized(row.get("candidate_id")),
        "model_name": _normalized(row.get("model_name")),
        "runner": _normalized(row.get("local_runner")),
        "local_model_id": _normalized(row.get("local_model_id")),
        "benchmark_run_id": _benchmark_run_id(row),
        "security_review_status": _normalized(row.get("security_review_status")),
        "download_approval": _normalized(row.get("download_approval")),
        "readiness": "blocked" if blocked_reasons else "ready",
        "blocked_reasons": blocked_reasons,
        "preflight_notes": _next_step(row, blocked_reasons),
    }


def build_matrix(
    rows: list[dict[str, str]],
    *,
    statuses: list[str] | None = None,
    runner: str | None = None,
    limit: int = 0,
) -> list[dict[str, object]]:
    normalized_statuses = [
        _normalized_lower(status)
        for status in (statuses if statuses is not None else list(DEFAULT_STATUSES))
    ]
    include_all_statuses = "all" in normalized_statuses
    runner_filter = _normalized_lower(runner)

    filtered_rows: list[dict[str, str]] = []
    for row in rows:
        row_status = _normalized_lower(row.get("status"))
        row_runner = _normalized_lower(row.get("local_runner"))
        status_filtered = (
            normalized_statuses
            and not include_all_statuses
            and row_status not in normalized_statuses
        )
        if status_filtered:
            continue
        if runner_filter and row_runner != runner_filter:
            continue
        filtered_rows.append(row)

    if limit > 0:
        filtered_rows = filtered_rows[:limit]
    return [matrix_row(row) for row in filtered_rows]


def format_json(matrix: list[dict[str, object]]) -> str:
    return json.dumps(matrix, indent=2, sort_keys=True)


def _md_cell(value: object) -> str:
    text = "; ".join(str(item) for item in value) if isinstance(value, list) else str(value)
    return text.replace("\n", " ").replace("|", "\\|") or "-"


def format_markdown(matrix: list[dict[str, object]]) -> str:
    lines = [
        "# Benchmark Matrix",
        "",
        "Read-only candidate plan. This command does not run models or initialize benchmark runs.",
        "",
    ]
    if not matrix:
        lines.append("No candidate rows matched the selected filters.")
        return "\n".join(lines)

    columns = [
        ("candidate_id", "Candidate"),
        ("model_name", "Model"),
        ("runner", "Runner"),
        ("local_model_id", "Local model id"),
        ("benchmark_run_id", "Benchmark run id"),
        ("security_review_status", "Security"),
        ("download_approval", "Download gate"),
        ("readiness", "Readiness"),
        ("blocked_reasons", "Blocked reasons"),
        ("preflight_notes", "Preflight notes"),
    ]
    lines.append("| " + " | ".join(title for _, title in columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in matrix:
        lines.append("| " + " | ".join(_md_cell(row[key]) for key, _ in columns) + " |")
    return "\n".join(lines)
