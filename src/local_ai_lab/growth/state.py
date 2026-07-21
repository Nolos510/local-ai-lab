"""Ignored, privacy-narrow Growth inventory and progress state."""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from local_ai_lab.growth.catalog import SAFE_ID_RE

PROGRESS_STATUSES = {"queued", "in_progress", "completed", "skipped"}
SAFE_EVIDENCE_PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]*$")
INVENTORY_SOURCES = {
    "repo_skills",
    "codex_home_skills",
    "codex_plugin_cli",
    "codex_mcp_cli",
    "repo_claude_skills",
    "claude_home_skills",
    "claude_plugin_cli",
    "claude_mcp_cli",
}
ECOSYSTEMS = {"repo", "codex", "claude"}


class StateError(ValueError):
    """Personal state is malformed or would violate the privacy boundary."""


def empty_state() -> dict[str, Any]:
    return {"schema_version": "growth-state-v1", "inventory": [], "progress": []}


def _safe_evidence_path(value: str) -> bool:
    path = Path(value)
    return (
        bool(value)
        and "\\" not in value
        and not path.is_absolute()
        and ".." not in path.parts
        and all(SAFE_EVIDENCE_PART_RE.fullmatch(part) for part in path.parts)
    )


def validate_state(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "inventory",
        "progress",
    }:
        raise StateError("growth state has an invalid envelope")
    if payload.get("schema_version") != "growth-state-v1":
        raise StateError("growth state has an invalid schema version")
    inventory = payload.get("inventory")
    progress = payload.get("progress")
    if not isinstance(inventory, list) or not isinstance(progress, list):
        raise StateError("growth state collections are invalid")
    inventory_keys: set[tuple[str, str, str, str]] = set()
    required_inventory = {
        "id",
        "kind",
        "ecosystem",
        "source",
        "available",
        "configured",
        "installed",
        "enabled",
        "referenced",
        "evidenced",
    }
    for entry in inventory:
        if not isinstance(entry, dict) or set(entry) != required_inventory:
            raise StateError("growth inventory entry is malformed")
        if not isinstance(entry["id"], str) or not SAFE_ID_RE.fullmatch(entry["id"]):
            raise StateError("growth inventory id is invalid")
        if not isinstance(entry["kind"], str) or not SAFE_ID_RE.fullmatch(entry["kind"]):
            raise StateError("growth inventory kind is invalid")
        if entry["ecosystem"] not in ECOSYSTEMS or entry["source"] not in INVENTORY_SOURCES:
            raise StateError("growth inventory source is invalid")
        bool_fields = required_inventory - {"id", "kind", "ecosystem", "source"}
        if any(not isinstance(entry[field], bool) for field in bool_fields):
            raise StateError("growth inventory status is invalid")
        key = (entry["ecosystem"], entry["source"], entry["kind"], entry["id"])
        if key in inventory_keys:
            raise StateError("growth inventory contains a duplicate entry")
        inventory_keys.add(key)
    progress_ids: set[str] = set()
    for entry in progress:
        if not isinstance(entry, dict) or set(entry) != {"item_id", "status", "evidence"}:
            raise StateError("growth progress entry is malformed")
        item_id = entry.get("item_id")
        if not isinstance(item_id, str) or not SAFE_ID_RE.fullmatch(item_id):
            raise StateError("growth progress id is invalid")
        if item_id in progress_ids or entry.get("status") not in PROGRESS_STATUSES:
            raise StateError("growth progress status is invalid")
        evidence = entry.get("evidence")
        if evidence is not None and (
            not isinstance(evidence, str) or not _safe_evidence_path(evidence)
        ):
            raise StateError("growth progress evidence is invalid")
        progress_ids.add(item_id)
    return payload


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError("could not read private growth state") from exc
    return validate_state(payload)


def write_state_atomic(path: Path, payload: dict[str, Any]) -> None:
    validate_state(payload)
    temp_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".growth-state-v1-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            os.chmod(temp_path, 0o600)
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        if temp_path is not None:
            with suppress(OSError):
                temp_path.unlink(missing_ok=True)
        raise StateError("could not atomically write private growth state") from exc


def normalize_evidence(path: Path, *, repo_root: Path) -> str:
    try:
        relative = path.resolve(strict=True).relative_to(repo_root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise StateError("evidence must be an existing repo-relative artifact") from exc
    if not path.resolve().is_file():
        raise StateError("evidence must be an existing repo-relative artifact")
    value = relative.as_posix()
    if not _safe_evidence_path(value):
        raise StateError("evidence path is not safe to store")
    return value


def update_progress(
    state_path: Path,
    *,
    item_id: str,
    status: str,
    evidence_path: Path | None,
    repo_root: Path,
) -> dict[str, Any]:
    if not SAFE_ID_RE.fullmatch(item_id):
        raise StateError("growth item id is invalid")
    if status not in PROGRESS_STATUSES:
        raise StateError("growth progress status is invalid")
    state = load_state(state_path)
    evidence = normalize_evidence(evidence_path, repo_root=repo_root) if evidence_path else None
    by_id = {entry["item_id"]: entry for entry in state["progress"]}
    existing = by_id.get(item_id)
    if evidence is None and existing is not None:
        evidence = existing.get("evidence")
    by_id[item_id] = {"item_id": item_id, "status": status, "evidence": evidence}
    state["progress"] = [by_id[key] for key in sorted(by_id)]
    write_state_atomic(state_path, state)
    return state
