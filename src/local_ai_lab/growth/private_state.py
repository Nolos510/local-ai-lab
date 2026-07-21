"""Atomic fixed-target storage for ignored Growth state envelopes."""

from __future__ import annotations

import json
import os
import secrets
import stat
from contextlib import suppress
from pathlib import Path
from typing import Any

PRIVATE_DIR_NAME = ".local-ai-lab"
ALLOWED_STATE_FILES = frozenset(
    {
        "growth-inbox-v1.json",
        "growth-audit-v1.json",
        "growth-preflights-v1.json",
    }
)


def _reject_json_constant(_value: str) -> None:
    raise ValueError


class PrivateStateError(ValueError):
    """A fixed private-state target or envelope could not be handled safely."""


def validate_private_target(path: Path, *, repo_root: Path, filename: str) -> Path:
    if filename not in ALLOWED_STATE_FILES or Path(path).name != filename:
        raise PrivateStateError("private Growth state target is invalid")
    invalid = False
    try:
        root = Path(repo_root).resolve(strict=True)
        target = Path(path)
        expected_parent = root / PRIVATE_DIR_NAME
        if (
            target.parent != expected_parent
            or target.parent.name != PRIVATE_DIR_NAME
            or target.parent.is_symlink()
            or target.is_symlink()
        ):
            raise PrivateStateError("private Growth state target is invalid")
    except OSError:
        invalid = True
    if invalid:
        raise PrivateStateError("private Growth state target is invalid")
    return target


def load_private_json(
    path: Path,
    *,
    repo_root: Path,
    filename: str,
    default: dict[str, Any],
) -> dict[str, Any]:
    target = validate_private_target(path, repo_root=repo_root, filename=filename)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    root_fd: int | None = None
    state_dir_fd: int | None = None
    target_fd: int | None = None
    payload: object | None = None
    missing = False
    read_failed = False
    try:
        root = Path(repo_root).resolve(strict=True)
        root_fd = os.open(root, directory_flags | nofollow)
        try:
            state_dir_fd = os.open(
                PRIVATE_DIR_NAME,
                directory_flags | nofollow,
                dir_fd=root_fd,
            )
        except FileNotFoundError:
            missing = True
        if not missing and state_dir_fd is not None:
            directory_stat = os.fstat(state_dir_fd)
            path_stat = os.stat(target.parent, follow_symlinks=False)
            if not stat.S_ISDIR(directory_stat.st_mode) or (
                directory_stat.st_dev,
                directory_stat.st_ino,
            ) != (path_stat.st_dev, path_stat.st_ino):
                raise PrivateStateError("private Growth state target is invalid")
            try:
                target_fd = os.open(filename, os.O_RDONLY | nofollow, dir_fd=state_dir_fd)
            except FileNotFoundError:
                missing = True
        if not missing and target_fd is not None:
            if not stat.S_ISREG(os.fstat(target_fd).st_mode):
                raise PrivateStateError("private Growth state target is invalid")
            with os.fdopen(target_fd, mode="r", encoding="utf-8") as handle:
                target_fd = None
                payload = json.load(handle, parse_constant=_reject_json_constant)
    except PrivateStateError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        read_failed = True
    finally:
        if target_fd is not None:
            with suppress(OSError):
                os.close(target_fd)
        if state_dir_fd is not None:
            with suppress(OSError):
                os.close(state_dir_fd)
        if root_fd is not None:
            with suppress(OSError):
                os.close(root_fd)
    if missing and not read_failed:
        return json.loads(
            json.dumps(default, allow_nan=False),
            parse_constant=_reject_json_constant,
        )
    if read_failed:
        raise PrivateStateError("private Growth state could not be read safely")
    if not isinstance(payload, dict):
        raise PrivateStateError("private Growth state has an invalid envelope")
    return payload


def write_private_json_atomic(
    path: Path,
    payload: dict[str, Any],
    *,
    repo_root: Path,
    filename: str,
) -> None:
    """Replace one allowlisted ignored state file without following symlinks."""
    target = validate_private_target(path, repo_root=repo_root, filename=filename)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    root_fd: int | None = None
    state_dir_fd: int | None = None
    temporary_name: str | None = None
    write_failed = False
    try:
        root = Path(repo_root).resolve(strict=True)
        root_fd = os.open(root, directory_flags | nofollow)
        with suppress(FileExistsError):
            os.mkdir(PRIVATE_DIR_NAME, 0o700, dir_fd=root_fd)
        state_dir_fd = os.open(
            PRIVATE_DIR_NAME,
            directory_flags | nofollow,
            dir_fd=root_fd,
        )
        directory_stat = os.fstat(state_dir_fd)
        path_stat = os.stat(target.parent, follow_symlinks=False)
        if not stat.S_ISDIR(directory_stat.st_mode) or (
            directory_stat.st_dev,
            directory_stat.st_ino,
        ) != (path_stat.st_dev, path_stat.st_ino):
            raise PrivateStateError("private Growth state target is invalid")
        os.fchmod(state_dir_fd, 0o700)

        try:
            target_stat = os.stat(filename, dir_fd=state_dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            target_stat = None
        if target_stat is not None and not stat.S_ISREG(target_stat.st_mode):
            raise PrivateStateError("private Growth state target is invalid")

        prefix = f".{filename.removesuffix('.json')}-"
        temporary_name = f"{prefix}{secrets.token_hex(12)}.tmp"
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
            0o600,
            dir_fd=state_dir_fd,
        )
        with os.fdopen(temporary_fd, mode="w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(payload, handle, allow_nan=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            filename,
            src_dir_fd=state_dir_fd,
            dst_dir_fd=state_dir_fd,
        )
        temporary_name = None
        os.fsync(state_dir_fd)
    except PrivateStateError:
        raise
    except (OSError, TypeError, ValueError):
        write_failed = True
    finally:
        if temporary_name is not None and state_dir_fd is not None:
            with suppress(OSError):
                os.unlink(temporary_name, dir_fd=state_dir_fd)
        if state_dir_fd is not None:
            with suppress(OSError):
                os.close(state_dir_fd)
        if root_fd is not None:
            with suppress(OSError):
                os.close(root_fd)
    if write_failed:
        raise PrivateStateError("private Growth state could not be written safely")


__all__ = (
    "ALLOWED_STATE_FILES",
    "PRIVATE_DIR_NAME",
    "PrivateStateError",
    "load_private_json",
    "validate_private_target",
    "write_private_json_atomic",
)
