"""Stdlib-only Growth catalog and private-state helpers for the dashboard.

This module intentionally does not import the CLI inventory adapters. Dashboard
renders read only fixed catalog JSON files and the already-sanitized private
state written by an explicit ``ai-lab growth scan`` command.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import stat
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlsplit

CATALOG_FILES = (
    ("skills.json", "skill"),
    ("extensions.json", "extension"),
    ("learning.json", "learning"),
)
RISK_FIELDS = (
    "code_exec",
    "fs",
    "network",
    "creds",
    "private_data",
    "writes",
    "hooks",
    "background",
    "provenance",
    "license",
    "version_pin",
    "rollback",
)
REQUIRED_ITEM_FIELDS = {
    "id",
    "catalog_kind",
    "type",
    "name",
    "official",
    "provenance",
    "source_url",
    "availability",
    "review_date",
    "career_lenses",
    "practical_value",
    "marketability",
    "effort_tier",
    "cost",
    "prereqs",
    "capability_gaps",
    "risk_facts",
    "status",
    "review_state",
    "proof_artifact",
    "proof_project",
    "next_action",
    "inventory_aliases",
}
CAREER_LENSES = {"AIA", "AUT", "MLD"}
EFFORT_TIERS = {"1-3", "4-6", "7-10"}
CATALOG_STATUSES = {"Now", "Next", "Later", "Watch", "Blocked"}
REVIEW_STATES = {
    "unreviewed",
    "metadata_reviewed",
    "trial_approved",
    "blocked",
    "retired",
}
AVAILABILITY_STATES = {
    "available",
    "pending",
    "link_requires_verification",
    "unknown",
    "unavailable",
}
PROGRESS_STATUSES = {"queued", "in_progress", "completed", "skipped"}
ECOSYSTEMS = {"repo", "codex", "claude"}
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
INVENTORY_KINDS_BY_CATALOG = {
    "skill": frozenset({"skill"}),
    "extension": frozenset({"extension", "plugin", "mcp", "connector"}),
    "learning": frozenset({"learning", "cert", "course", "lesson", "reading", "track"}),
}
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:@-]{0,127}$")
SAFE_PATH_PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PRIVATE_PATH_RE = re.compile(r"(?:/users/|/home/|[a-z]:\\users\\)", re.IGNORECASE)
SECRET_LITERAL_RE = re.compile(
    r"(?:^|[^A-Za-z0-9])(?:sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{12,}|"
    r"github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{8,}|AKIA[A-Z0-9]{12,})"
)


class GrowthDataError(ValueError):
    """Growth data is malformed or would cross a privacy boundary."""


def contains_private_literal(value):
    text = str(value or "")
    return bool(PRIVATE_PATH_RE.search(text) or SECRET_LITERAL_RE.search(text))


def _safe_relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and all(SAFE_PATH_PART_RE.fullmatch(part) for part in path.parts)
        and not contains_private_literal(value)
    )


def _safe_public_url(value):
    if value is None:
        return True
    if not isinstance(value, str) or contains_private_literal(value):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def _safe_text(value):
    return isinstance(value, str) and bool(value) and not contains_private_literal(value)


def _safe_text_list(value):
    return isinstance(value, list) and all(
        isinstance(entry, str) and not contains_private_literal(entry) for entry in value
    )


def _validate_item(item, expected_kind):
    if not isinstance(item, dict) or set(item) != REQUIRED_ITEM_FIELDS:
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    item_id = item.get("id")
    if not isinstance(item_id, str) or not SAFE_ID_RE.fullmatch(item_id):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if item.get("catalog_kind") != expected_kind:
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if not all(
        _safe_text(item.get(field))
        for field in (
            "type",
            "name",
            "provenance",
            "practical_value",
            "marketability",
            "proof_project",
            "next_action",
        )
    ):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if item.get("official") not in (True, False, None):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if not _safe_public_url(item.get("source_url")):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if item.get("availability") not in AVAILABILITY_STATES:
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if not isinstance(item.get("review_date"), str) or not DATE_RE.fullmatch(
        item["review_date"]
    ):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    lenses = item.get("career_lenses")
    if (
        not _safe_text_list(lenses)
        or not lenses
        or not set(lenses) <= CAREER_LENSES
    ):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if item.get("effort_tier") not in EFFORT_TIERS:
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    cost = item.get("cost")
    if cost is not None and not _safe_text(cost):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    for field in ("prereqs", "capability_gaps"):
        if not _safe_text_list(item.get(field)):
            raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    aliases = item.get("inventory_aliases")
    if not isinstance(aliases, list) or any(
        not isinstance(alias, str) or not SAFE_ID_RE.fullmatch(alias) for alias in aliases
    ):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    risks = item.get("risk_facts")
    if not isinstance(risks, dict) or set(risks) != set(RISK_FIELDS):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if any(not _safe_text(risks[field]) for field in RISK_FIELDS):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if item.get("status") not in CATALOG_STATUSES:
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if item.get("review_state") not in REVIEW_STATES:
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    if not _safe_relative_path(item.get("proof_artifact")):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    return item


def load_catalogs(catalog_dir):
    """Load the three fixed reviewed catalogs without scanning the host."""
    items = []
    for filename, expected_kind in CATALOG_FILES:
        try:
            payload = json.loads((Path(catalog_dir) / filename).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GrowthDataError("Tracked Growth catalogs could not be read safely.") from exc
        if (
            not isinstance(payload, dict)
            or set(payload) != {"schema_version", "catalog_kind", "items"}
            or payload.get("schema_version") != "growth-catalog-v1"
            or payload.get("catalog_kind") != expected_kind
            or not isinstance(payload.get("items"), list)
        ):
            raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
        items.extend(_validate_item(item, expected_kind) for item in payload["items"])
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise GrowthDataError("Tracked Growth catalogs could not be read safely.")
    return items


def empty_state():
    return {"schema_version": "growth-state-v1", "inventory": [], "progress": []}


def validate_state(payload):
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "inventory",
        "progress",
    }:
        raise GrowthDataError("Private Growth state could not be read safely.")
    if payload.get("schema_version") != "growth-state-v1":
        raise GrowthDataError("Private Growth state could not be read safely.")
    inventory = payload.get("inventory")
    progress = payload.get("progress")
    if not isinstance(inventory, list) or not isinstance(progress, list):
        raise GrowthDataError("Private Growth state could not be read safely.")
    inventory_fields = {
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
    inventory_keys = set()
    for entry in inventory:
        if not isinstance(entry, dict) or set(entry) != inventory_fields:
            raise GrowthDataError("Private Growth state could not be read safely.")
        if not isinstance(entry["id"], str) or not SAFE_ID_RE.fullmatch(entry["id"]):
            raise GrowthDataError("Private Growth state could not be read safely.")
        if not isinstance(entry["kind"], str) or not SAFE_ID_RE.fullmatch(entry["kind"]):
            raise GrowthDataError("Private Growth state could not be read safely.")
        if entry["ecosystem"] not in ECOSYSTEMS or entry["source"] not in INVENTORY_SOURCES:
            raise GrowthDataError("Private Growth state could not be read safely.")
        bool_fields = inventory_fields - {"id", "kind", "ecosystem", "source"}
        if any(not isinstance(entry[field], bool) for field in bool_fields):
            raise GrowthDataError("Private Growth state could not be read safely.")
        key = (entry["ecosystem"], entry["source"], entry["kind"], entry["id"])
        if key in inventory_keys:
            raise GrowthDataError("Private Growth state could not be read safely.")
        inventory_keys.add(key)
    progress_ids = set()
    for entry in progress:
        if not isinstance(entry, dict) or set(entry) != {"item_id", "status", "evidence"}:
            raise GrowthDataError("Private Growth state could not be read safely.")
        item_id = entry.get("item_id")
        if not isinstance(item_id, str) or not SAFE_ID_RE.fullmatch(item_id):
            raise GrowthDataError("Private Growth state could not be read safely.")
        if item_id in progress_ids or entry.get("status") not in PROGRESS_STATUSES:
            raise GrowthDataError("Private Growth state could not be read safely.")
        evidence = entry.get("evidence")
        if evidence is not None and (
            not isinstance(evidence, str) or not _safe_relative_path(evidence)
        ):
            raise GrowthDataError("Private Growth state could not be read safely.")
        progress_ids.add(item_id)
    return payload


def load_state(path, *, repo_root=None):
    if repo_root is not None:
        _validate_state_target(path, repo_root)
    state_path = Path(path)
    if not state_path.exists():
        return empty_state()
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GrowthDataError("Private Growth state could not be read safely.") from exc
    return validate_state(payload)


def _validate_state_target(path, repo_root):
    try:
        state_path = Path(path)
        root = Path(repo_root).resolve(strict=True)
        if (
            state_path.name != "growth-state-v1.json"
            or state_path.parent.name != ".local-ai-lab"
            or state_path.parent.parent.resolve(strict=True) != root
            or state_path.parent.is_symlink()
            or state_path.is_symlink()
        ):
            raise GrowthDataError("Private Growth state target is invalid.")
    except OSError as exc:
        raise GrowthDataError("Private Growth state target is invalid.") from exc


def write_state_atomic(path, payload, *, repo_root):
    """Atomically replace only the ignored Growth state target.

    All mutations are relative to no-follow directory descriptors. Renaming the
    private directory during a write therefore cannot redirect the write to a
    symlink target outside the repository.
    """
    _validate_state_target(path, repo_root)
    validate_state(payload)
    state_path = Path(path)
    root = Path(repo_root).resolve(strict=True)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    root_fd = None
    state_dir_fd = None
    temporary_name = None
    try:
        root_fd = os.open(root, directory_flags | nofollow)
        with suppress(FileExistsError):
            os.mkdir(".local-ai-lab", 0o700, dir_fd=root_fd)
        state_dir_fd = os.open(
            ".local-ai-lab",
            directory_flags | nofollow,
            dir_fd=root_fd,
        )
        directory_stat = os.fstat(state_dir_fd)
        path_stat = os.stat(state_path.parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(directory_stat.st_mode)
            or (directory_stat.st_dev, directory_stat.st_ino)
            != (path_stat.st_dev, path_stat.st_ino)
        ):
            raise GrowthDataError("Private Growth state target is invalid.")
        os.fchmod(state_dir_fd, 0o700)

        try:
            target_stat = os.stat(
                state_path.name,
                dir_fd=state_dir_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            target_stat = None
        if target_stat is not None and not stat.S_ISREG(target_stat.st_mode):
            raise GrowthDataError("Private Growth state target is invalid.")

        temporary_name = f".growth-state-v1-{secrets.token_hex(12)}.tmp"
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
            0o600,
            dir_fd=state_dir_fd,
        )
        with os.fdopen(temporary_fd, mode="w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            state_path.name,
            src_dir_fd=state_dir_fd,
            dst_dir_fd=state_dir_fd,
        )
        temporary_name = None
        os.fsync(state_dir_fd)
    except GrowthDataError:
        raise
    except OSError as exc:
        raise GrowthDataError("Private Growth state could not be written safely.") from exc
    finally:
        if temporary_name is not None and state_dir_fd is not None:
            with suppress(OSError):
                os.unlink(temporary_name, dir_fd=state_dir_fd)
        if state_dir_fd is not None:
            os.close(state_dir_fd)
        if root_fd is not None:
            os.close(root_fd)


def _existing_repo_file(value, repo_root):
    if not isinstance(value, str) or not _safe_relative_path(value):
        return False
    try:
        root = Path(repo_root).resolve(strict=True)
        path = (root / value).resolve(strict=True)
        path.relative_to(root)
    except (OSError, ValueError):
        return False
    return path.is_file()


def _normalize_evidence(value, repo_root):
    if not isinstance(value, str) or not _safe_relative_path(value):
        raise GrowthDataError("Evidence must be an existing repo-relative artifact.")
    normalized = Path(value).as_posix()
    if not _existing_repo_file(normalized, repo_root):
        raise GrowthDataError("Evidence must be an existing repo-relative artifact.")
    return normalized


def update_progress(
    state_path,
    *,
    catalog_items,
    item_id,
    status,
    evidence,
    repo_root,
):
    """Catalog-gate and atomically update personal progress only."""
    if item_id not in {item["id"] for item in catalog_items}:
        raise GrowthDataError("Growth progress item is not in the reviewed catalog.")
    if status not in PROGRESS_STATUSES:
        raise GrowthDataError("Growth progress status is invalid.")
    state = load_state(state_path, repo_root=repo_root)
    progress_by_id = {entry["item_id"]: entry for entry in state["progress"]}
    prior = progress_by_id.get(item_id, {})
    normalized_evidence = (
        _normalize_evidence(evidence, repo_root) if evidence else prior.get("evidence")
    )
    progress_by_id[item_id] = {
        "item_id": item_id,
        "status": status,
        "evidence": normalized_evidence,
    }
    state["progress"] = [progress_by_id[key] for key in sorted(progress_by_id)]
    write_state_atomic(state_path, state, repo_root=repo_root)
    return state


def item_views(catalog_items, state, *, repo_root):
    """Join public catalog rows to matched sanitized state without exposing raw IDs."""
    progress_by_id = {entry["item_id"]: entry for entry in state["progress"]}
    matched_inventory_keys = set()
    views = []
    for item in catalog_items:
        aliases = {item["id"], *item["inventory_aliases"]}
        compatible_kinds = INVENTORY_KINDS_BY_CATALOG[item["catalog_kind"]]
        matching_inventory = []
        for index, entry in enumerate(state["inventory"]):
            if entry["id"] in aliases and entry["kind"] in compatible_kinds:
                matching_inventory.append(entry)
                matched_inventory_keys.add(index)
        progress = progress_by_id.get(item["id"])
        proof_exists = _existing_repo_file(item["proof_artifact"], repo_root)
        progress_evidence_exists = bool(
            progress
            and progress.get("evidence")
            and _existing_repo_file(progress["evidence"], repo_root)
        )
        view = dict(item)
        view.update(
            {
                "_inventory": tuple(matching_inventory),
                "_detected": bool(matching_inventory),
                "_scan_evidenced": any(
                    entry["evidenced"] for entry in matching_inventory
                ),
                "_proof_exists": proof_exists,
                "_progress_status": progress.get("status") if progress else None,
                "_progress_evidence_recorded": bool(
                    progress and progress.get("evidence")
                ),
                "_progress_evidence_exists": progress_evidence_exists,
                "_evidenced": proof_exists or progress_evidence_exists,
            }
        )
        views.append(view)
    return views, len(state["inventory"]) - len(matched_inventory_keys)


def inventory_counts(state):
    fields = (
        "available",
        "configured",
        "installed",
        "enabled",
        "referenced",
        "evidenced",
    )
    return {
        "total": len(state["inventory"]),
        **{
            field: sum(1 for entry in state["inventory"] if entry[field])
            for field in fields
        },
    }


__all__ = (
    "CATALOG_STATUSES",
    "CAREER_LENSES",
    "EFFORT_TIERS",
    "GrowthDataError",
    "PROGRESS_STATUSES",
    "RISK_FIELDS",
    "contains_private_literal",
    "empty_state",
    "inventory_counts",
    "item_views",
    "load_catalogs",
    "load_state",
    "update_progress",
    "validate_state",
    "write_state_atomic",
)
