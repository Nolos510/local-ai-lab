"""Sanitized, read-only inventory adapters for repo, Codex, and Claude hosts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from local_ai_lab.growth.catalog import SAFE_ID_RE

MAX_OUTPUT_BYTES = 1_000_000
CLI_TIMEOUT_SECONDS = 15.0
ECOSYSTEMS = {"repo", "codex", "claude", "all"}


class InventoryError(RuntimeError):
    """An inventory source failed without retaining its untrusted raw output."""

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _sensitive_tokens(home_dir: Path, env: Mapping[str, str]) -> frozenset[str]:
    values = {home_dir.name, env.get("USER", ""), env.get("LOGNAME", "")}
    return frozenset(value.casefold() for value in values if len(value) >= 3)


def _safe_identifier(value: object, *, sensitive_tokens: frozenset[str]) -> str | None:
    if not isinstance(value, str) or not SAFE_ID_RE.fullmatch(value):
        return None
    folded = value.casefold()
    if any(token in folded for token in sensitive_tokens):
        return None
    return value


def _catalog_match(
    identifier: str,
    catalog_items: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    for item in catalog_items:
        if identifier == item.get("id") or identifier in item.get("inventory_aliases", ()):
            return item
    return None


def _proof_exists(item: dict[str, Any] | None, *, repo_root: Path) -> bool:
    if item is None:
        return False
    proof = item.get("proof_artifact")
    if not isinstance(proof, str):
        return False
    try:
        path = (repo_root / proof).resolve()
        path.relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return False
    return path.is_file()


def _record(
    *,
    identifier: str,
    kind: str,
    ecosystem: str,
    source: str,
    catalog_items: Sequence[dict[str, Any]],
    repo_root: Path,
    available: bool = True,
    configured: bool = False,
    installed: bool = False,
    enabled: bool = False,
) -> dict[str, object]:
    match = _catalog_match(identifier, catalog_items)
    return {
        "id": identifier,
        "kind": kind,
        "ecosystem": ecosystem,
        "source": source,
        "available": available,
        "configured": configured,
        "installed": installed,
        "enabled": enabled,
        "referenced": match is not None,
        "evidenced": _proof_exists(match, repo_root=repo_root),
    }


def _scan_skill_directory(
    path: Path,
    *,
    ecosystem: str,
    source: str,
    catalog_items: Sequence[dict[str, Any]],
    repo_root: Path,
    sensitive_tokens: frozenset[str],
) -> list[dict[str, object]]:
    if not path.is_dir():
        return []
    try:
        children = sorted(path.iterdir(), key=lambda child: child.name.casefold())
    except OSError as exc:
        raise InventoryError(
            f"could not read the {ecosystem} skill inventory",
            exit_code=1,
        ) from exc
    records = []
    for child in children:
        identifier = _safe_identifier(child.name, sensitive_tokens=sensitive_tokens)
        if identifier is None or not child.is_dir() or not (child / "SKILL.md").is_file():
            continue
        records.append(
            _record(
                identifier=identifier,
                kind="skill",
                ecosystem=ecosystem,
                source=source,
                catalog_items=catalog_items,
                repo_root=repo_root,
                installed=True,
            )
        )
    return records


def _minimal_subprocess_env(home_dir: Path, env: Mapping[str, str]) -> dict[str, str]:
    safe_env = {
        "HOME": str(home_dir),
        "PATH": env.get("PATH", os.defpath),
        "NO_COLOR": "1",
    }
    codex_home = env.get("CODEX_HOME")
    if codex_home:
        safe_env["CODEX_HOME"] = codex_home
    return safe_env


def _run_json_command(
    argv: list[str],
    *,
    source_label: str,
    runner: Callable[..., Any],
    env: Mapping[str, str],
) -> object:
    try:
        result = runner(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
            env=dict(env),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise InventoryError(f"{source_label} inventory command failed", exit_code=1) from exc
    if result.returncode != 0:
        raise InventoryError(f"{source_label} inventory command failed", exit_code=1)
    stdout = result.stdout
    if (
        not isinstance(stdout, str)
        or len(stdout.encode("utf-8", errors="ignore")) > MAX_OUTPUT_BYTES
    ):
        raise InventoryError(f"{source_label} inventory response was invalid", exit_code=1)
    try:
        return json.loads(stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InventoryError(f"{source_label} inventory response was invalid", exit_code=1) from exc


def _collection(payload: object, *, kind: str) -> list[tuple[str | None, object, str]]:
    if isinstance(payload, list):
        return [(None, entry, "listed") for entry in payload]
    if not isinstance(payload, dict):
        raise InventoryError(f"{kind} inventory response was malformed", exit_code=1)
    if kind == "plugin" and any(key in payload for key in ("installed", "available")):
        grouped: list[tuple[str | None, object, str]] = []
        for group in ("installed", "available"):
            values = payload.get(group, [])
            if not isinstance(values, list):
                raise InventoryError(f"{kind} inventory response was malformed", exit_code=1)
            grouped.extend((None, entry, group) for entry in values)
        return grouped
    keys = (
        ("plugins", "installed_plugins", "items", "data")
        if kind == "plugin"
        else ("mcp", "mcp_servers", "mcpServers", "servers", "items", "data")
    )
    selected: object | None = None
    for key in keys:
        if key in payload:
            selected = payload[key]
            break
    if selected is None and payload and all(isinstance(value, dict) for value in payload.values()):
        selected = payload
    if selected is None:
        if not payload:
            return []
        raise InventoryError(f"{kind} inventory response was malformed", exit_code=1)
    if isinstance(selected, list):
        return [(None, entry, "listed") for entry in selected]
    if isinstance(selected, dict):
        return [(str(key), value, "listed") for key, value in selected.items()]
    raise InventoryError(f"{kind} inventory response was malformed", exit_code=1)


def _explicit_bool(entry: Mapping[str, object], field: str, *, default: bool = False) -> bool:
    value = entry.get(field)
    return value if isinstance(value, bool) else default


def _parse_cli_inventory(
    payload: object,
    *,
    kind: str,
    ecosystem: str,
    source: str,
    catalog_items: Sequence[dict[str, Any]],
    repo_root: Path,
    sensitive_tokens: frozenset[str],
) -> list[dict[str, object]]:
    records = []
    for fallback_id, raw_entry, collection_state in _collection(payload, kind=kind):
        if isinstance(raw_entry, str):
            candidate = raw_entry
            entry: Mapping[str, object] = {}
        elif isinstance(raw_entry, dict):
            entry = raw_entry
            candidate = next(
                (
                    value
                    for key in ("id", "name", "slug", "server_name", "plugin_id")
                    if isinstance((value := entry.get(key)), str)
                ),
                fallback_id,
            )
        else:
            continue
        identifier = _safe_identifier(candidate, sensitive_tokens=sensitive_tokens)
        if identifier is None:
            continue
        if kind == "plugin":
            installed = _explicit_bool(
                entry,
                "installed",
                default=collection_state != "available",
            )
            configured = _explicit_bool(entry, "configured")
        else:
            installed = _explicit_bool(entry, "installed")
            configured = _explicit_bool(entry, "configured", default=True)
        records.append(
            _record(
                identifier=identifier,
                kind=kind,
                ecosystem=ecosystem,
                source=source,
                catalog_items=catalog_items,
                repo_root=repo_root,
                available=_explicit_bool(entry, "available", default=True),
                configured=configured,
                installed=installed,
                enabled=_explicit_bool(entry, "enabled"),
            )
        )
    return records


def _scan_host_cli(
    executable: str,
    *,
    ecosystem: str,
    catalog_items: Sequence[dict[str, Any]],
    repo_root: Path,
    sensitive_tokens: frozenset[str],
    runner: Callable[..., Any],
    subprocess_env: Mapping[str, str],
) -> list[dict[str, object]]:
    records = []
    for kind, source, argv_tail in (
        ("plugin", f"{ecosystem}_plugin_cli", ["plugin", "list", "--json"]),
        ("mcp", f"{ecosystem}_mcp_cli", ["mcp", "list", "--json"]),
    ):
        payload = _run_json_command(
            [executable, *argv_tail],
            source_label=f"{ecosystem} {kind}",
            runner=runner,
            env=subprocess_env,
        )
        records.extend(
            _parse_cli_inventory(
                payload,
                kind=kind,
                ecosystem=ecosystem,
                source=source,
                catalog_items=catalog_items,
                repo_root=repo_root,
                sensitive_tokens=sensitive_tokens,
            )
        )
    return records


def _deduplicate(records: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    deduplicated: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for record in records:
        key = (
            str(record["ecosystem"]),
            str(record["source"]),
            str(record["kind"]),
            str(record["id"]),
        )
        existing = deduplicated.get(key)
        if existing is None:
            deduplicated[key] = dict(record)
            continue
        for field in (
            "available",
            "configured",
            "installed",
            "enabled",
            "referenced",
            "evidenced",
        ):
            existing[field] = bool(existing[field]) or bool(record[field])
    return [deduplicated[key] for key in sorted(deduplicated)]


def scan_inventory(
    *,
    repo_root: Path,
    catalog_items: Sequence[dict[str, Any]],
    ecosystem: str = "all",
    home_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] | None = None,
    runner: Callable[..., Any] | None = None,
) -> list[dict[str, object]]:
    """Scan only requested local sources and return privacy-narrow normalized records."""
    if ecosystem not in ECOSYSTEMS:
        raise InventoryError("unsupported inventory ecosystem", exit_code=2)
    env = dict(os.environ if environ is None else environ)
    home = Path.home() if home_dir is None else home_dir
    find_executable = shutil.which if which is None else which
    run = subprocess.run if runner is None else runner
    sensitive_tokens = _sensitive_tokens(home, env)
    subprocess_env = _minimal_subprocess_env(home, env)
    records: list[dict[str, object]] = []

    if ecosystem in {"repo", "all"}:
        records.extend(
            _scan_skill_directory(
                repo_root / "skills",
                ecosystem="repo",
                source="repo_skills",
                catalog_items=catalog_items,
                repo_root=repo_root,
                sensitive_tokens=sensitive_tokens,
            )
        )

    if ecosystem in {"codex", "all"}:
        executable = find_executable("codex")
        if executable is None:
            raise InventoryError("codex CLI is not available for inventory", exit_code=2)
        codex_home = Path(env["CODEX_HOME"]) if env.get("CODEX_HOME") else home / ".codex"
        records.extend(
            _scan_skill_directory(
                codex_home / "skills",
                ecosystem="codex",
                source="codex_home_skills",
                catalog_items=catalog_items,
                repo_root=repo_root,
                sensitive_tokens=sensitive_tokens,
            )
        )
        records.extend(
            _scan_host_cli(
                executable,
                ecosystem="codex",
                catalog_items=catalog_items,
                repo_root=repo_root,
                sensitive_tokens=sensitive_tokens,
                runner=run,
                subprocess_env=subprocess_env,
            )
        )

    if ecosystem in {"claude", "all"}:
        executable = find_executable("claude")
        if executable is None:
            if ecosystem == "claude":
                raise InventoryError("claude CLI is not available for inventory", exit_code=2)
        else:
            for path, source in (
                (repo_root / ".claude" / "skills", "repo_claude_skills"),
                (home / ".claude" / "skills", "claude_home_skills"),
            ):
                records.extend(
                    _scan_skill_directory(
                        path,
                        ecosystem="claude",
                        source=source,
                        catalog_items=catalog_items,
                        repo_root=repo_root,
                        sensitive_tokens=sensitive_tokens,
                    )
                )
            records.extend(
                _scan_host_cli(
                    executable,
                    ecosystem="claude",
                    catalog_items=catalog_items,
                    repo_root=repo_root,
                    sensitive_tokens=sensitive_tokens,
                    runner=run,
                    subprocess_env=subprocess_env,
                )
            )

    return _deduplicate(records)
