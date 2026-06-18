"""Recoverable local model removal helpers for the dashboard.

This module contains the only code path that can remove a locally detected
model. It never deletes files directly: LM Studio folders are handed to Finder's
Trash, and Ollama models are removed through the Ollama CLI.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class RemovalError(RuntimeError):
    """Raised when a model removal request fails validation or execution."""


@dataclass(frozen=True)
class RemovalTarget:
    runtime: str
    model_id: str
    path: Path
    root: Path
    action: str
    size_bytes: int


@dataclass(frozen=True)
class RemovalResult:
    target: RemovalTarget
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _contained_path(path, root):
    root_path = Path(root).expanduser().resolve()
    target_path = Path(path).expanduser().resolve()
    try:
        target_path.relative_to(root_path)
    except ValueError as exc:
        raise RemovalError(f"Refusing removal outside model root: {target_path}") from exc
    return target_path, root_path


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file() and not item.is_symlink():
            total += item.stat().st_size
    return total


def resolve_target(model, lmstudio_root, ollama_root) -> RemovalTarget:
    runtime = str(model.get("runtime") or "")
    model_id = str(model.get("model_id") or "")
    if runtime == "LM Studio":
        raw_path = model.get("local_path") or model.get("source_path")
        if not raw_path:
            raise RemovalError("LM Studio model is missing a local path.")
        target_path, root = _contained_path(raw_path, lmstudio_root)
        return RemovalTarget(
            runtime=runtime,
            model_id=model_id,
            path=target_path,
            root=root,
            action="Move folder to macOS Trash",
            size_bytes=_directory_size(target_path),
        )
    if runtime == "Ollama":
        if not model_id:
            raise RemovalError("Ollama model is missing a model id.")
        raw_path = model.get("local_path")
        if not raw_path:
            raise RemovalError("Ollama model is missing a manifest path.")
        target_path, root = _contained_path(raw_path, ollama_root)
        return RemovalTarget(
            runtime=runtime,
            model_id=model_id,
            path=target_path,
            root=root,
            action="Run ollama rm",
            size_bytes=_directory_size(target_path),
        )
    raise RemovalError(f"Unsupported model runtime for removal: {runtime}")


def _applescript_string(value) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _trash_lmstudio_model(target: RemovalTarget, timeout: int) -> RemovalResult:
    if platform.system() != "Darwin":
        raise RemovalError("LM Studio Trash removal is available only on macOS.")
    script = f'tell application "Finder" to delete POSIX file "{_applescript_string(target.path)}"'
    command = ("osascript", "-e", script)
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    return RemovalResult(
        target=target,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _remove_ollama_model(target: RemovalTarget, timeout: int) -> RemovalResult:
    ollama_path = shutil.which("ollama") or "ollama"
    command = (ollama_path, "rm", target.model_id)
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    return RemovalResult(
        target=target,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def remove_target(target: RemovalTarget, timeout: int = 60) -> RemovalResult:
    if target.runtime == "LM Studio":
        return _trash_lmstudio_model(target, timeout)
    if target.runtime == "Ollama":
        return _remove_ollama_model(target, timeout)
    raise RemovalError(f"Unsupported model runtime for removal: {target.runtime}")
