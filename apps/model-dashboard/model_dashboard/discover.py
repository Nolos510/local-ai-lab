"""Local-only Discover graduation and upstream re-surface state."""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from .components import _dashboard_runs_by_benchmark_id, _latest_decisions_by_model_id

SAFE_CANDIDATE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")


def load_upstream_state(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {"version": 1, "candidates": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), dict):
        return {"version": 1, "candidates": {}}
    return payload


def _write_upstream_state(path: Path, state: dict[str, object]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_name = handle.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            with suppress(FileNotFoundError):
                Path(temporary_name).unlink()


def candidate_lifecycle_rows(conn, candidates, upstream_state_path: Path):
    runs = _dashboard_runs_by_benchmark_id(conn)
    decisions = _latest_decisions_by_model_id(conn)
    state = load_upstream_state(upstream_state_path)
    candidate_states = state.get("candidates", {})
    if not isinstance(candidate_states, dict):
        candidate_states = {}
    rows = []
    for source_row in candidates:
        row = dict(source_row)
        benchmark_run_id = str(row.get("benchmark_run_id") or "").strip()
        run = runs.get(benchmark_run_id)
        graduated = bool(
            run
            and (
                run["score_status"] == "confirmed"
                or run["model_id"] in decisions
            )
        )
        update = candidate_states.get(str(row.get("candidate_id") or ""), {})
        update = dict(update) if isinstance(update, dict) else {}
        row["_graduated"] = graduated
        row["_upstream_update"] = (
            update if graduated and bool(update.get("update_pending")) else {}
        )
        rows.append(row)
    return rows


def dismiss_upstream_update(path: Path, candidate_id: str) -> None:
    candidate_id = str(candidate_id or "").strip()
    if not SAFE_CANDIDATE_ID_RE.fullmatch(candidate_id):
        raise ValueError("Invalid candidate id.")
    state = load_upstream_state(path)
    candidates = state.get("candidates", {})
    if not isinstance(candidates, dict):
        raise ValueError("Upstream state is invalid.")
    record = candidates.get(candidate_id)
    if not isinstance(record, dict) or not record.get("update_pending"):
        raise ValueError("No pending upstream update exists for this candidate.")
    record["update_pending"] = False
    record["dismissed_at"] = datetime.now(timezone.utc).isoformat()  # noqa: UP017
    record["cleared_reason"] = "dismissed"
    candidates[candidate_id] = record
    state["candidates"] = candidates
    _write_upstream_state(Path(path), state)
