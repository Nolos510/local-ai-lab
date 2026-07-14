"""Recoverable local model removal helpers for the dashboard.

This module contains the only code path that can remove a locally detected
model. It never deletes files directly: LM Studio folders and MLX-LM cache
snapshots are handed to Finder's Trash, and Ollama models are removed through
the Ollama CLI.
"""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

LMSTUDIO_WEIGHT_SUFFIXES = (".gguf", ".safetensors", ".bin", ".mlx", ".npz")
OLLAMA_MODEL_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*"
    r"(?::[A-Za-z0-9][A-Za-z0-9._-]*)?$"
)


class RemovalError(RuntimeError):
    """Raised when a model removal request fails validation or execution."""


@dataclass(frozen=True)
class RemovalTarget:
    runtime: str
    model_id: str
    path: Path | None
    root: Path | None
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


def _lmstudio_folder_target(path, root):
    target_path, root_path = _contained_path(path, root)
    if target_path.is_file() or target_path.suffix.lower() in LMSTUDIO_WEIGHT_SUFFIXES:
        target_path, root_path = _contained_path(target_path.parent, root_path)
    if target_path == root_path:
        raise RemovalError("Refusing to remove the LM Studio model root.")
    if not target_path.exists():
        raise RemovalError(
            "LM Studio model folder is no longer present; refresh inventory before removing."
        )
    if not target_path.is_dir():
        raise RemovalError(f"LM Studio removal target is not a folder: {target_path}")
    return target_path, root_path


def _path_parts(value):
    if value in (None, ""):
        return ()
    return tuple(
        part
        for part in Path(str(value)).expanduser().parts
        if part not in ("", "/", ".")
    )


def _casefold_descendant(root, parts):
    if not parts or any(part == ".." for part in parts):
        return None
    current = Path(root).expanduser()
    for part in parts:
        if not current.is_dir():
            return None
        matches = [item for item in current.iterdir() if item.name.casefold() == part.casefold()]
        if len(matches) != 1:
            return None
        current = matches[0]
    return current


def _lmstudio_indexed_path_parts(model):
    candidates = []

    def add(parts):
        clean = tuple(part for part in parts if part not in ("", "/", "."))
        if len(clean) >= 2 and ".." not in clean and clean not in candidates:
            candidates.append(clean)

    for field in ("local_path", "source_path"):
        parts = _path_parts(model.get(field))
        for start in range(max(0, len(parts) - 4), len(parts) - 1):
            add(parts[start:])

    publisher = str(model.get("publisher") or "").strip()
    identifiers = []
    for field in ("indexed_model_id", "model_id"):
        value = str(model.get(field) or "").strip()
        if value and value not in identifiers:
            identifiers.append(value)
    for identifier in identifiers:
        parts = _path_parts(identifier)
        if publisher and len(parts) == 1:
            add((publisher, parts[0]))
        add(parts)
    return candidates


def _resolve_lmstudio_folder(model, root):
    raw_paths = []
    outside_root = False
    for field in ("local_path", "source_path"):
        raw_path = model.get(field)
        if raw_path in (None, "") or raw_path in raw_paths:
            continue
        raw_paths.append(raw_path)
        path = Path(str(raw_path)).expanduser()
        if not path.is_absolute():
            path = Path(root).expanduser() / path
        try:
            return _lmstudio_folder_target(path, root)
        except RemovalError as exc:
            if "outside model root" in str(exc):
                outside_root = True

    matches = []
    for parts in _lmstudio_indexed_path_parts(model):
        candidate = _casefold_descendant(root, parts)
        if candidate is None:
            continue
        try:
            target = _lmstudio_folder_target(candidate, root)
        except RemovalError:
            continue
        if target not in matches:
            matches.append(target)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RemovalError("Multiple LM Studio folders match this indexed row; refresh inventory.")
    if outside_root:
        raise RemovalError("LM Studio path resolves outside the configured models root.")
    raise RemovalError("Path not found under LM Studio root.")


def _validated_ollama_model_id(model_id):
    value = str(model_id or "")
    if not value:
        raise RemovalError("Ollama row is missing an exact model id.")
    if not OLLAMA_MODEL_ID_RE.fullmatch(value):
        raise RemovalError("Ollama model id is invalid; refresh inventory before removing.")
    return value


def _hf_snapshot_target(path, root):
    if not path:
        raise RemovalError("Hugging Face cache snapshot path was not reported.")
    try:
        target_path, root_path = _contained_path(path, root)
    except RemovalError as exc:
        raise RemovalError(
            "MLX snapshot resolves outside the Hugging Face hub cache root."
        ) from exc
    relative = target_path.relative_to(root_path)
    if (
        len(relative.parts) != 3
        or not relative.parts[0].startswith("models--")
        or relative.parts[1] != "snapshots"
    ):
        raise RemovalError("MLX removal target is not a Hugging Face cache snapshot directory.")
    if not target_path.exists():
        raise RemovalError("MLX snapshot was not found under the Hugging Face hub cache root.")
    if not target_path.is_dir():
        raise RemovalError("MLX removal target is not a snapshot directory.")
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


def resolve_target(model, lmstudio_root, ollama_root, hf_cache_root=None) -> RemovalTarget:
    runtime = str(model.get("runtime") or "")
    model_id = str(model.get("model_id") or "")
    if runtime == "LM Studio":
        target_path, root = _resolve_lmstudio_folder(model, lmstudio_root)
        return RemovalTarget(
            runtime=runtime,
            model_id=model_id,
            path=target_path,
            root=root,
            action="Move folder to macOS Trash",
            size_bytes=_directory_size(target_path),
        )
    if runtime == "Ollama":
        model_id = _validated_ollama_model_id(model_id)
        return RemovalTarget(
            runtime=runtime,
            model_id=model_id,
            path=None,
            root=None,
            action="Run ollama rm",
            size_bytes=0,
        )
    if runtime == "MLX-LM":
        if hf_cache_root is None:
            raise RemovalError("Hugging Face hub cache root is not configured.")
        raw_path = model.get("local_path") or model.get("model_id")
        target_path, root = _hf_snapshot_target(raw_path, hf_cache_root)
        return RemovalTarget(
            runtime=runtime,
            model_id=model_id,
            path=target_path,
            root=root,
            action="Move HF cache snapshot to macOS Trash",
            size_bytes=_directory_size(target_path),
        )
    raise RemovalError(f"Unsupported model runtime for removal: {runtime}")


def _trash_model_folder(target: RemovalTarget, timeout: int) -> RemovalResult:
    if platform.system() != "Darwin":
        raise RemovalError(f"{target.runtime} Trash removal is available only on macOS.")
    path_literal = json.dumps(str(target.path))
    script = (
        'ObjC.import("Foundation");'
        f"const url = $.NSURL.fileURLWithPath({path_literal});"
        "const fileManager = $.NSFileManager.defaultManager;"
        "const ok = fileManager.trashItemAtURLResultingItemURLError(url, null, null);"
        'if (!ok) { throw new Error("trashItemAtURL failed"); }'
    )
    command = ("osascript", "-l", "JavaScript", "-e", script)
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
    if target.runtime in ("LM Studio", "MLX-LM"):
        return _trash_model_folder(target, timeout)
    if target.runtime == "Ollama":
        return _remove_ollama_model(target, timeout)
    raise RemovalError(f"Unsupported model runtime for removal: {target.runtime}")
