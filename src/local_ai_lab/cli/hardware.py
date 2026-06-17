from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]
CommandResolver = Callable[[str], str | None]

RUNTIME_COMMANDS = ("ollama", "lms", "mlx_lm", "llama-cli")
VERSION_FLAGS = {
    "ollama": ["--version"],
    "lms": ["--version"],
    "mlx_lm": ["--version"],
    "llama-cli": ["--version"],
}
SYSCTL_KEYS = {
    "chip_brand": "machdep.cpu.brand_string",
    "memory_bytes": "hw.memsize",
}


def default_command_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )


def collect_hardware_snapshot(
    *,
    command_runner: CommandRunner = default_command_runner,
    command_resolver: CommandResolver = shutil.which,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or datetime.now(UTC)
    snapshot: dict[str, Any] = {
        "schema_version": "hardware-snapshot-v0.1",
        "captured_at": timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "machine": {
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
        "macos": _collect_macos_sysctl(command_runner),
        "runtimes": _collect_runtime_versions(command_runner, command_resolver),
    }
    return snapshot


def write_snapshot(path: Path, payload: dict[str, Any], *, repo_root: Path) -> Path:
    output_path = _resolve_repo_local_output(path, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_snapshot(payload), encoding="utf-8")
    return output_path


def format_snapshot(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _collect_macos_sysctl(command_runner: CommandRunner) -> dict[str, str | int | None]:
    values: dict[str, str | int | None] = {
        "chip_brand": None,
        "memory_bytes": None,
    }
    if platform.system() != "Darwin":
        return values
    for output_key, sysctl_key in SYSCTL_KEYS.items():
        value = _run_text(command_runner, ["sysctl", "-n", sysctl_key])
        if value is None:
            continue
        if output_key == "memory_bytes":
            try:
                values[output_key] = int(value)
            except ValueError:
                values[output_key] = None
        else:
            values[output_key] = value
    return values


def _collect_runtime_versions(
    command_runner: CommandRunner,
    command_resolver: CommandResolver,
) -> dict[str, dict[str, str | bool | None]]:
    runtimes: dict[str, dict[str, str | bool | None]] = {}
    for command_name in RUNTIME_COMMANDS:
        executable = command_resolver(command_name)
        present = executable is not None
        version = None
        if present:
            version = _run_text(command_runner, [command_name, *VERSION_FLAGS[command_name]])
        runtimes[command_name] = {
            "present": present,
            "version": version,
        }
    return runtimes


def _run_text(command_runner: CommandRunner, command: list[str]) -> str | None:
    try:
        result = command_runner(command)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = (result.stdout or result.stderr or "").strip()
    return output.splitlines()[0].strip() if output else None


def _resolve_repo_local_output(path: Path, *, repo_root: Path) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    resolved_repo = repo_root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_repo)
    except ValueError as exc:
        raise ValueError(f"--out must stay inside the repository: {path}") from exc
    return resolved_candidate
