"""Fail-closed official-host plugin install and removal execution."""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import stat
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from local_ai_lab.growth.catalog import load_catalogs
from local_ai_lab.growth.install_policy import (
    COMPONENTS,
    EXEC_ID_RE,
    EXEC_TARGET_RE,
    IMMUTABLE_REVISION_RE,
    SCOPES,
    VERSION_RE,
    InstallPolicy,
    InstallPolicyError,
    build_host_argv,
    load_install_policies,
    policy_for_execution,
)
from local_ai_lab.growth.privacy import contains_sensitive_literal, safe_public_url
from local_ai_lab.growth.private_state import (
    PrivateStateError,
    load_private_json,
    write_private_json_atomic,
)

LIST_TIMEOUT_SECONDS = 15.0
MUTATION_TIMEOUT_SECONDS = 120.0
MAX_OUTPUT_BYTES = 1_000_000
PREFLIGHT_TTL_SECONDS = 300.0
MAX_PREFLIGHTS = 40
NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")
JOB_ID_RE = re.compile(r"^job-[a-f0-9]{20}$")
AUDIT_ID_RE = re.compile(r"^audit-[a-f0-9]{20}$")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
AUDIT_OUTCOMES = frozenset(
    {
        "started",
        "success",
        "command_failed",
        "command_failed_rolled_back",
        "verify_failed",
        "verify_failed_rolled_back",
        "rollback_started",
        "rollback_success",
        "rollback_failed",
        "remove_verify_failed",
        "blocked_version_drift",
        "blocked_policy_drift",
    }
)
PLAN_FIELDS = {
    "operation",
    "target",
    "host",
    "plugin_id",
    "marketplace",
    "marketplace_source",
    "marketplace_revision",
    "reviewed_version",
    "live_version",
    "scope",
    "components",
    "auth_policy",
    "data_scope",
    "high_risk",
    "data_scope_ack_required",
    "threat_review_artifact",
    "risk_facts",
    "argv",
    "rollback_argv",
    "pin_enforcement",
    "fingerprint",
}


class InstallError(RuntimeError):
    """A Growth mutation was blocked or failed without retaining raw host output."""

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True, slots=True)
class PluginRecord:
    plugin_id: str
    marketplace: str
    marketplace_source: str
    marketplace_revision: str
    version: str
    scope: str
    installed: bool
    enabled: bool


@dataclass(frozen=True, slots=True)
class InstallPlan:
    operation: str
    target: str
    host: str
    plugin_id: str
    marketplace: str
    marketplace_source: str
    marketplace_revision: str
    reviewed_version: str
    live_version: str | None
    scope: str
    components: tuple[str, ...]
    auth_policy: str
    data_scope: str
    high_risk: bool
    data_scope_ack_required: bool
    threat_review_artifact: str | None
    risk_facts: dict[str, str]
    argv: tuple[str, ...]
    rollback_argv: tuple[str, ...]
    pin_enforcement: str
    fingerprint: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["components"] = list(self.components)
        payload["argv"] = list(self.argv)
        payload["rollback_argv"] = list(self.rollback_argv)
        return payload


def _timestamp(now: Callable[[], datetime] | None = None) -> str:
    value = datetime.now(UTC) if now is None else now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _minimal_env(home: Path, environ: Mapping[str, str]) -> dict[str, str]:
    result = {"HOME": str(home), "PATH": environ.get("PATH", os.defpath), "NO_COLOR": "1"}
    if environ.get("CODEX_HOME"):
        result["CODEX_HOME"] = environ["CODEX_HOME"]
    return result


def _run_json(
    argv: list[str],
    *,
    runner: Callable[..., Any],
    env: Mapping[str, str],
    cwd: Path,
    timeout: float,
) -> object:
    result = None
    command_failed = False
    try:
        result = runner(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(env),
            cwd=str(cwd),
            shell=False,
            stdin=subprocess.DEVNULL,
        )
    except Exception:
        command_failed = True
    if command_failed or result is None:
        raise InstallError("official host inventory command failed", exit_code=1)
    if getattr(result, "returncode", None) != 0:
        raise InstallError("official host inventory command failed", exit_code=1)
    stdout = getattr(result, "stdout", None)
    if (
        not isinstance(stdout, str)
        or len(stdout.encode("utf-8", errors="ignore")) > MAX_OUTPUT_BYTES
    ):
        raise InstallError("official host inventory response was invalid", exit_code=1)
    parsed: object | None = None
    response_invalid = False
    try:
        parsed = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        response_invalid = True
    if response_invalid:
        raise InstallError("official host inventory response was invalid", exit_code=1)
    return parsed


def _plugin_entries(payload: object) -> list[tuple[Mapping[str, object], str]]:
    if isinstance(payload, list):
        if not all(isinstance(entry, dict) for entry in payload):
            raise InstallError("official host inventory response was invalid", exit_code=1)
        return [(entry, "listed") for entry in payload]
    if not isinstance(payload, dict):
        raise InstallError("official host inventory response was invalid", exit_code=1)
    entries: list[tuple[Mapping[str, object], str]] = []
    used_group = False
    for group in ("installed", "available"):
        if group in payload:
            used_group = True
            values = payload[group]
            if not isinstance(values, list) or not all(
                isinstance(entry, dict) for entry in values
            ):
                raise InstallError("official host inventory response was invalid", exit_code=1)
            entries.extend((entry, group) for entry in values)
    if used_group:
        return entries
    selected: object | None = None
    for key in ("plugins", "installed_plugins", "items", "data"):
        if key in payload:
            selected = payload[key]
            break
    if selected is None:
        return [] if not payload else _mapping_plugin_entries(payload)
    if isinstance(selected, list):
        if not all(isinstance(entry, dict) for entry in selected):
            raise InstallError("official host inventory response was invalid", exit_code=1)
        return [(entry, "listed") for entry in selected]
    if isinstance(selected, dict):
        return _mapping_plugin_entries(selected)
    raise InstallError("official host inventory response was invalid", exit_code=1)


def _mapping_plugin_entries(
    payload: Mapping[str, object],
) -> list[tuple[Mapping[str, object], str]]:
    entries: list[tuple[Mapping[str, object], str]] = []
    for fallback, raw in payload.items():
        if not isinstance(raw, dict):
            raise InstallError("official host inventory response was invalid", exit_code=1)
        entry = dict(raw)
        entry.setdefault("id", fallback)
        entries.append((entry, "listed"))
    return entries


def _first_string(entry: Mapping[str, object], names: Sequence[str]) -> str | None:
    return next(
        (value for name in names if isinstance((value := entry.get(name)), str)),
        None,
    )


def parse_plugin_records(payload: object, *, host: str) -> list[PluginRecord]:
    """Parse a version-aware sanitized plugin listing without retaining extra fields."""
    if host not in {"codex", "claude"}:
        raise InstallError("official plugin host is unsupported", exit_code=2)
    records: list[PluginRecord] = []
    for entry, collection in _plugin_entries(payload):
        plugin_id = _first_string(entry, ("plugin_id", "id", "name", "slug"))
        marketplace = _first_string(
            entry,
            ("marketplace", "marketplace_name", "source_marketplace"),
        )
        if isinstance(plugin_id, str) and "@" in plugin_id and marketplace is None:
            plugin_id, marketplace = plugin_id.rsplit("@", 1)
        raw_source = _first_string(
            entry,
            ("marketplace_source", "source_url", "marketplace_url"),
        )
        source = safe_public_url(raw_source)
        revision = _first_string(
            entry,
            ("marketplace_revision", "revision", "source_revision", "sha"),
        )
        version = _first_string(entry, ("version", "plugin_version"))
        scope = _first_string(entry, ("scope", "install_scope"))
        if scope is None and host == "codex":
            scope = "user"
        if (
            not isinstance(plugin_id, str)
            or not EXEC_ID_RE.fullmatch(plugin_id)
            or not isinstance(marketplace, str)
            or not EXEC_ID_RE.fullmatch(marketplace)
            or source is None
            or source != raw_source
            or not isinstance(revision, str)
            or not IMMUTABLE_REVISION_RE.fullmatch(revision)
            or not isinstance(version, str)
            or not VERSION_RE.fullmatch(version)
            or scope not in SCOPES
            or (host == "codex" and scope != "user")
        ):
            raise InstallError("official host inventory response was invalid", exit_code=1)
        installed_value = entry.get("installed")
        if "installed" in entry and not isinstance(installed_value, bool):
            raise InstallError("official host inventory response was invalid", exit_code=1)
        installed = (
            installed_value if isinstance(installed_value, bool) else collection != "available"
        )
        enabled_value = entry.get("enabled")
        if "enabled" in entry and not isinstance(enabled_value, bool):
            raise InstallError("official host inventory response was invalid", exit_code=1)
        records.append(
            PluginRecord(
                plugin_id=plugin_id,
                marketplace=marketplace,
                marketplace_source=source,
                marketplace_revision=revision,
                version=version,
                scope=scope,
                installed=installed,
                enabled=enabled_value if isinstance(enabled_value, bool) else False,
            )
        )
    return records


def scan_plugin_versions(
    host: str,
    *,
    runner: Callable[..., Any] = subprocess.run,
    which: Callable[[str], str | None] = shutil.which,
    environ: Mapping[str, str] | None = None,
    home_dir: Path | None = None,
    repo_root: Path | None = None,
    timeout: float = LIST_TIMEOUT_SECONDS,
) -> list[PluginRecord]:
    """Run only the existing read-only official plugin inventory command."""
    if host not in {"codex", "claude"}:
        raise InstallError("official plugin host is unsupported", exit_code=2)
    if which(host) is None:
        raise InstallError(f"{host} CLI is not available for Growth", exit_code=2)
    env_source = dict(os.environ if environ is None else environ)
    home = Path.home() if home_dir is None else home_dir
    cwd = Path.cwd() if repo_root is None else repo_root
    argv = [host, "plugin", "list"]
    if host == "claude":
        argv.append("--available")
    argv.append("--json")
    payload = _run_json(
        argv,
        runner=runner,
        env=_minimal_env(home, env_source),
        cwd=cwd,
        timeout=timeout,
    )
    return parse_plugin_records(payload, host=host)


def _record_for_policy(
    records: Sequence[PluginRecord],
    policy: InstallPolicy,
) -> PluginRecord | None:
    matches = [
        record
        for record in records
        if record.plugin_id == policy.plugin_id
        and record.marketplace == policy.marketplace
        and record.scope == policy.scope
    ]
    unique = {
        (
            record.marketplace_source,
            record.marketplace_revision,
            record.version,
            record.scope,
            record.installed,
        )
        for record in matches
    }
    if len(unique) > 1:
        raise InstallError("official host inventory was ambiguous", exit_code=1)
    return matches[0] if matches else None


def _policy_fingerprint(
    policy: InstallPolicy,
    item: dict[str, Any],
    *,
    operation: str,
    argv: Sequence[str],
    rollback_argv: Sequence[str],
    live_version: str | None,
) -> str:
    payload = {
        "policy": policy.fingerprint_payload(),
        "catalog": {
            "id": item.get("id"),
            "official": item.get("official"),
            "review_state": item.get("review_state"),
            "status": item.get("status"),
            "risk_facts": item.get("risk_facts"),
        },
        "operation": operation,
        "argv": list(argv),
        "rollback_argv": list(rollback_argv),
        "live_version": live_version,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _build_plan(
    policy: InstallPolicy,
    item: dict[str, Any],
    *,
    operation: str,
    live_record: PluginRecord | None,
) -> InstallPlan:
    argv = tuple(build_host_argv(policy, operation))
    rollback_operation = "remove" if operation == "install" else "install"
    rollback_argv = tuple(build_host_argv(policy, rollback_operation))
    live_version = live_record.version if live_record is not None else None
    fingerprint = _policy_fingerprint(
        policy,
        item,
        operation=operation,
        argv=argv,
        rollback_argv=rollback_argv,
        live_version=live_version,
    )
    risk_facts = item.get("risk_facts")
    if (
        not isinstance(risk_facts, dict)
        or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in risk_facts.items()
        )
        or contains_sensitive_literal(json.dumps(risk_facts, sort_keys=True))
    ):
        raise InstallError("tracked Growth risk facts are unsafe for preflight", exit_code=2)
    return InstallPlan(
        operation=operation,
        target=policy.target_id,
        host=policy.host,
        plugin_id=policy.plugin_id,
        marketplace=policy.marketplace,
        marketplace_source=policy.marketplace_source,
        marketplace_revision=policy.marketplace_revision,
        reviewed_version=policy.reviewed_version,
        live_version=live_version,
        scope=policy.scope,
        components=policy.components,
        auth_policy=policy.auth_policy,
        data_scope=policy.data_scope,
        high_risk=policy.high_risk,
        data_scope_ack_required=policy.data_scope_ack_required,
        threat_review_artifact=policy.threat_review_artifact,
        risk_facts=dict(risk_facts),
        argv=argv,
        rollback_argv=rollback_argv,
        pin_enforcement=(
            "reviewed marketplace snapshot rechecked at confirm + "
            "exact post-install version verification/rollback"
        ),
        fingerprint=fingerprint,
    )


def _validate_plan(payload: object) -> InstallPlan:
    if not isinstance(payload, dict) or set(payload) != PLAN_FIELDS:
        raise InstallError("Growth preflight record is invalid", exit_code=2)
    plan: InstallPlan | None = None
    invalid_plan = False
    try:
        plan = InstallPlan(
            operation=payload["operation"],
            target=payload["target"],
            host=payload["host"],
            plugin_id=payload["plugin_id"],
            marketplace=payload["marketplace"],
            marketplace_source=payload["marketplace_source"],
            marketplace_revision=payload["marketplace_revision"],
            reviewed_version=payload["reviewed_version"],
            live_version=payload["live_version"],
            scope=payload["scope"],
            components=tuple(payload["components"]),
            auth_policy=payload["auth_policy"],
            data_scope=payload["data_scope"],
            high_risk=payload["high_risk"],
            data_scope_ack_required=payload["data_scope_ack_required"],
            threat_review_artifact=payload["threat_review_artifact"],
            risk_facts=dict(payload["risk_facts"]),
            argv=tuple(payload["argv"]),
            rollback_argv=tuple(payload["rollback_argv"]),
            pin_enforcement=payload["pin_enforcement"],
            fingerprint=payload["fingerprint"],
        )
    except (KeyError, TypeError, ValueError):
        invalid_plan = True
    if invalid_plan or plan is None:
        raise InstallError("Growth preflight record is invalid", exit_code=2)
    if (
        plan.operation not in {"install", "remove"}
        or not EXEC_TARGET_RE.fullmatch(plan.target)
        or plan.host not in {"codex", "claude"}
        or not EXEC_ID_RE.fullmatch(plan.plugin_id)
        or not EXEC_ID_RE.fullmatch(plan.marketplace)
        or safe_public_url(plan.marketplace_source) != plan.marketplace_source
        or not IMMUTABLE_REVISION_RE.fullmatch(plan.marketplace_revision)
        or not VERSION_RE.fullmatch(plan.reviewed_version)
        or (plan.live_version is not None and not VERSION_RE.fullmatch(plan.live_version))
        or plan.scope not in SCOPES
        or (plan.host == "codex" and plan.scope != "user")
        or not plan.components
        or len(plan.components) != len(set(plan.components))
        or not set(plan.components) <= COMPONENTS
        or not isinstance(plan.auth_policy, str)
        or not isinstance(plan.data_scope, str)
        or not isinstance(plan.high_risk, bool)
        or not isinstance(plan.data_scope_ack_required, bool)
        or (plan.high_risk and plan.data_scope_ack_required is not True)
        or not isinstance(plan.risk_facts, dict)
        or not plan.risk_facts
        or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in plan.risk_facts.items()
        )
        or not re.fullmatch(r"^[a-f0-9]{64}$", plan.fingerprint)
        or plan.pin_enforcement
        != (
            "reviewed marketplace snapshot rechecked at confirm + "
            "exact post-install version verification/rollback"
        )
        or contains_sensitive_literal(json.dumps(payload, sort_keys=True))
    ):
        raise InstallError("Growth preflight record is invalid", exit_code=2)
    invalid_argv = False
    try:
        policy = _policy_from_plan(plan)
        expected_argv = tuple(build_host_argv(policy, plan.operation))
        rollback_operation = "remove" if plan.operation == "install" else "install"
        expected_rollback = tuple(build_host_argv(policy, rollback_operation))
    except InstallPolicyError:
        invalid_argv = True
    if invalid_argv:
        raise InstallError("Growth preflight record is invalid", exit_code=2)
    if plan.argv != expected_argv or plan.rollback_argv != expected_rollback:
        raise InstallError("Growth preflight record is invalid", exit_code=2)
    return plan


def _validate_preflight_state(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "entries"}:
        raise InstallError("Growth preflight state is invalid", exit_code=2)
    if payload.get("schema_version") != "growth-preflights-v1" or not isinstance(
        payload.get("entries"), list
    ):
        raise InstallError("Growth preflight state is invalid", exit_code=2)
    nonces: set[str] = set()
    for entry in payload["entries"]:
        if not isinstance(entry, dict) or set(entry) != {"nonce", "expires_at", "plan"}:
            raise InstallError("Growth preflight state is invalid", exit_code=2)
        nonce = entry.get("nonce")
        expires_at = entry.get("expires_at")
        if (
            not isinstance(nonce, str)
            or not NONCE_RE.fullmatch(nonce)
            or nonce in nonces
            or not isinstance(expires_at, (int, float))
            or isinstance(expires_at, bool)
            or not math.isfinite(expires_at)
            or expires_at <= 0
        ):
            raise InstallError("Growth preflight state is invalid", exit_code=2)
        _validate_plan(entry.get("plan"))
        nonces.add(nonce)
    return payload


_FILE_LOCKS_GUARD = threading.Lock()
_FILE_LOCKS: dict[str, threading.Lock] = {}
_LOCK_NAMES = frozenset(
    {
        "growth-audit-v1.lock",
        "growth-operation-v1.lock",
        "growth-preflights-v1.lock",
    }
)


class _FileLease:
    """Hold a fixed-target thread and advisory process lock without path expansion."""

    def __init__(
        self,
        path: Path,
        *,
        repo_root: Path,
        expected_name: str,
        blocking: bool,
        busy_message: str,
        failure_message: str,
    ) -> None:
        self.path = path
        self.repo_root = repo_root
        self.expected_name = expected_name
        self.blocking = blocking
        self.busy_message = busy_message
        self.failure_message = failure_message
        self._fd: int | None = None
        self._root_fd: int | None = None
        self._state_dir_fd: int | None = None
        self._thread_lock: threading.Lock | None = None

    def __enter__(self):
        failure: InstallError | None = None
        try:
            root = self.repo_root.resolve(strict=True)
            expected = root / ".local-ai-lab" / self.expected_name
            if (
                self.expected_name not in _LOCK_NAMES
                or self.path != expected
            ):
                raise InstallError(self.failure_message, exit_code=1)
            key = str(expected)
            with _FILE_LOCKS_GUARD:
                self._thread_lock = _FILE_LOCKS.setdefault(key, threading.Lock())
            if not self._thread_lock.acquire(blocking=self.blocking):
                raise InstallError(self.busy_message, exit_code=2)
            nofollow = getattr(os, "O_NOFOLLOW", 0)
            directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | nofollow
            self._root_fd = os.open(root, directory_flags)
            with suppress(FileExistsError):
                os.mkdir(".local-ai-lab", 0o700, dir_fd=self._root_fd)
            self._state_dir_fd = os.open(
                ".local-ai-lab",
                directory_flags,
                dir_fd=self._root_fd,
            )
            state_stat = os.fstat(self._state_dir_fd)
            path_stat = os.stat(self.path.parent, follow_symlinks=False)
            if not stat.S_ISDIR(state_stat.st_mode) or (
                state_stat.st_dev,
                state_stat.st_ino,
            ) != (path_stat.st_dev, path_stat.st_ino):
                raise InstallError(self.failure_message, exit_code=1)
            os.fchmod(self._state_dir_fd, 0o700)
            self._fd = os.open(
                self.expected_name,
                os.O_RDWR | os.O_CREAT | nofollow,
                0o600,
                dir_fd=self._state_dir_fd,
            )
            if not stat.S_ISREG(os.fstat(self._fd).st_mode):
                raise InstallError(self.failure_message, exit_code=1)
            os.fchmod(self._fd, 0o600)
            lock_flags = fcntl.LOCK_EX | (0 if self.blocking else fcntl.LOCK_NB)
            fcntl.flock(self._fd, lock_flags)
        except BlockingIOError:
            failure = InstallError(self.busy_message, exit_code=2)
        except InstallError as error:
            failure = error
        except OSError:
            failure = InstallError(self.failure_message, exit_code=1)
        if failure is not None:
            self.__exit__(None, None, None)
            raise failure
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        if self._fd is not None:
            with suppress(OSError):
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            with suppress(OSError):
                os.close(self._fd)
            self._fd = None
        if self._state_dir_fd is not None:
            with suppress(OSError):
                os.close(self._state_dir_fd)
            self._state_dir_fd = None
        if self._root_fd is not None:
            with suppress(OSError):
                os.close(self._root_fd)
            self._root_fd = None
        if self._thread_lock is not None:
            with suppress(RuntimeError):
                self._thread_lock.release()
            self._thread_lock = None


class PreflightStore:
    def __init__(
        self,
        path: Path,
        *,
        repo_root: Path,
        clock: Callable[[], float] = time.time,
        nonce_factory: Callable[[], str] | None = None,
    ) -> None:
        self.path = path
        self.repo_root = repo_root
        self.clock = clock
        self.nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(24))
        self._lock = threading.Lock()
        self._lease_path = path.with_name("growth-preflights-v1.lock")

    def _load(self) -> dict[str, Any]:
        try:
            payload = load_private_json(
                self.path,
                repo_root=self.repo_root,
                filename="growth-preflights-v1.json",
                default={"schema_version": "growth-preflights-v1", "entries": []},
            )
        except PrivateStateError as error:
            message = str(error)
        else:
            return _validate_preflight_state(payload)
        raise InstallError(message, exit_code=1)

    def _write(self, payload: dict[str, Any]) -> None:
        _validate_preflight_state(payload)
        try:
            write_private_json_atomic(
                self.path,
                payload,
                repo_root=self.repo_root,
                filename="growth-preflights-v1.json",
            )
        except PrivateStateError as error:
            message = str(error)
        else:
            return
        raise InstallError(message, exit_code=1)

    def issue(self, plan: InstallPlan, *, ttl: float = PREFLIGHT_TTL_SECONDS) -> tuple[str, float]:
        nonce = self.nonce_factory()
        if not isinstance(nonce, str) or not NONCE_RE.fullmatch(nonce):
            raise InstallError("Growth preflight nonce generation failed", exit_code=1)
        if (
            not isinstance(ttl, (int, float))
            or isinstance(ttl, bool)
            or not math.isfinite(ttl)
            or ttl <= 0
            or ttl > PREFLIGHT_TTL_SECONDS
        ):
            raise InstallError("Growth preflight expiry is invalid", exit_code=1)
        with self._lock, _FileLease(
            self._lease_path,
            repo_root=self.repo_root,
            expected_name="growth-preflights-v1.lock",
            blocking=True,
            busy_message="Growth preflight state is busy",
            failure_message="Growth preflight lock could not be acquired",
        ):
            now = self.clock()
            if (
                not isinstance(now, (int, float))
                or isinstance(now, bool)
                or not math.isfinite(now)
            ):
                raise InstallError("Growth preflight expiry is invalid", exit_code=1)
            expires_at = now + ttl
            if not math.isfinite(expires_at) or expires_at <= now:
                raise InstallError("Growth preflight expiry is invalid", exit_code=1)
            state = self._load()
            entries = [entry for entry in state["entries"] if entry["expires_at"] > now]
            entries.append({"nonce": nonce, "expires_at": expires_at, "plan": plan.as_dict()})
            state["entries"] = entries[-MAX_PREFLIGHTS:]
            self._write(state)
        return nonce, expires_at

    def consume(self, nonce: str) -> InstallPlan:
        if not isinstance(nonce, str) or not NONCE_RE.fullmatch(nonce):
            raise InstallError("Growth preflight nonce is invalid or expired", exit_code=2)
        with self._lock, _FileLease(
            self._lease_path,
            repo_root=self.repo_root,
            expected_name="growth-preflights-v1.lock",
            blocking=True,
            busy_message="Growth preflight state is busy",
            failure_message="Growth preflight lock could not be acquired",
        ):
            now = self.clock()
            if (
                not isinstance(now, (int, float))
                or isinstance(now, bool)
                or not math.isfinite(now)
            ):
                raise InstallError("Growth preflight expiry is invalid", exit_code=1)
            state = self._load()
            matched = next((entry for entry in state["entries"] if entry["nonce"] == nonce), None)
            state["entries"] = [
                entry
                for entry in state["entries"]
                if entry["nonce"] != nonce and entry["expires_at"] > now
            ]
            self._write(state)
        if matched is None or matched["expires_at"] <= now:
            raise InstallError("Growth preflight nonce is invalid or expired", exit_code=2)
        return _validate_plan(matched["plan"])


def _audit_argv_is_exact(event: Mapping[str, object]) -> bool:
    argv = event.get("argv")
    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        return False
    host = event.get("host")
    operation = event.get("operation")
    marketplace = event.get("marketplace")
    if host == "codex":
        verb = "add" if operation == "install" else "remove"
        if len(argv) != 4 or argv[:3] != ["codex", "plugin", verb]:
            return False
        plugin_ref = argv[3]
    elif host == "claude":
        verb = "install" if operation == "install" else "uninstall"
        if (
            len(argv) != 6
            or argv[:3] != ["claude", "plugin", verb]
            or argv[4] != "--scope"
            or argv[5] not in SCOPES
        ):
            return False
        plugin_ref = argv[3]
    else:
        return False
    if plugin_ref.count("@") != 1:
        return False
    plugin_id, argv_marketplace = plugin_ref.split("@", 1)
    return bool(
        EXEC_ID_RE.fullmatch(plugin_id)
        and EXEC_ID_RE.fullmatch(argv_marketplace)
        and argv_marketplace == marketplace
    )


def _validate_audit(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "events"}:
        raise InstallError("Growth audit journal is invalid", exit_code=1)
    if payload.get("schema_version") != "growth-audit-v1" or not isinstance(
        payload.get("events"), list
    ):
        raise InstallError("Growth audit journal is invalid", exit_code=1)
    required = {
        "id",
        "correlation_id",
        "operation",
        "target",
        "host",
        "source",
        "marketplace",
        "reviewed_version",
        "argv",
        "timestamp",
        "outcome",
    }
    ids: set[str] = set()
    for event in payload["events"]:
        if not isinstance(event, dict) or set(event) != required:
            raise InstallError("Growth audit journal is invalid", exit_code=1)
        if (
            not isinstance(event.get("id"), str)
            or not AUDIT_ID_RE.fullmatch(event["id"])
            or event["id"] in ids
            or not isinstance(event.get("correlation_id"), str)
            or not JOB_ID_RE.fullmatch(event["correlation_id"])
            or event.get("operation") not in {"install", "remove"}
            or not isinstance(event.get("target"), str)
            or not EXEC_TARGET_RE.fullmatch(event["target"])
            or event.get("host") not in {"codex", "claude"}
            or safe_public_url(event.get("source")) != event.get("source")
            or not isinstance(event.get("marketplace"), str)
            or not EXEC_ID_RE.fullmatch(event["marketplace"])
            or not isinstance(event.get("reviewed_version"), str)
            or not VERSION_RE.fullmatch(event["reviewed_version"])
            or not isinstance(event.get("timestamp"), str)
            or not UTC_TIMESTAMP_RE.fullmatch(event["timestamp"])
            or event.get("outcome") not in AUDIT_OUTCOMES
            or not _audit_argv_is_exact(event)
            or contains_sensitive_literal(json.dumps(event, sort_keys=True))
        ):
            raise InstallError("Growth audit journal is invalid", exit_code=1)
        ids.add(event["id"])
    return payload


class AuditJournal:
    def __init__(
        self,
        path: Path,
        *,
        repo_root: Path,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = path
        self.repo_root = repo_root
        self.now = now
        self._lock = threading.Lock()
        self._lease_path = path.with_name("growth-audit-v1.lock")

    def append(
        self,
        plan: InstallPlan,
        *,
        correlation_id: str,
        operation: str,
        argv: Sequence[str],
        outcome: str,
    ) -> dict[str, Any]:
        if outcome not in AUDIT_OUTCOMES or not JOB_ID_RE.fullmatch(correlation_id):
            raise InstallError("Growth audit event is invalid", exit_code=1)
        timestamp = _timestamp(self.now)
        digest = hashlib.sha256(
            f"{correlation_id}\0{operation}\0{outcome}\0{timestamp}\0{secrets.token_hex(8)}".encode()
        ).hexdigest()
        event = {
            "id": f"audit-{digest[:20]}",
            "correlation_id": correlation_id,
            "operation": operation,
            "target": plan.target,
            "host": plan.host,
            "source": plan.marketplace_source,
            "marketplace": plan.marketplace,
            "reviewed_version": plan.reviewed_version,
            "argv": list(argv),
            "timestamp": timestamp,
            "outcome": outcome,
        }
        with self._lock, _FileLease(
            self._lease_path,
            repo_root=self.repo_root,
            expected_name="growth-audit-v1.lock",
            blocking=True,
            busy_message="Growth audit journal is busy",
            failure_message="Growth audit lock could not be acquired",
        ):
            try:
                payload = load_private_json(
                    self.path,
                    repo_root=self.repo_root,
                    filename="growth-audit-v1.json",
                    default={"schema_version": "growth-audit-v1", "events": []},
                )
            except PrivateStateError as error:
                message = str(error)
            else:
                message = None
            if message is not None:
                raise InstallError(message, exit_code=1)
            _validate_audit(payload)
            payload["events"].append(event)
            _validate_audit(payload)
            try:
                write_private_json_atomic(
                    self.path,
                    payload,
                    repo_root=self.repo_root,
                    filename="growth-audit-v1.json",
                )
            except PrivateStateError as error:
                message = str(error)
            else:
                message = None
            if message is not None:
                raise InstallError(message, exit_code=1)
        return event


class OperationLease(_FileLease):
    """Serialize Growth mutations across dashboard threads and local CLI processes."""

    def __init__(self, path: Path, *, repo_root: Path) -> None:
        super().__init__(
            path,
            repo_root=repo_root,
            expected_name="growth-operation-v1.lock",
            blocking=False,
            busy_message="another Growth install or removal is already running",
            failure_message="Growth operation lock could not be acquired",
        )


class GrowthInstallService:
    def __init__(
        self,
        *,
        repo_root: Path,
        catalog_dir: Path,
        policy_path: Path,
        preflight_path: Path,
        audit_path: Path,
        operation_lock_path: Path,
        runner: Callable[..., Any] = subprocess.run,
        which: Callable[[str], str | None] = shutil.which,
        environ: Mapping[str, str] | None = None,
        home_dir: Path | None = None,
        clock: Callable[[], float] = time.time,
        now: Callable[[], datetime] | None = None,
        nonce_factory: Callable[[], str] | None = None,
        list_timeout: float = LIST_TIMEOUT_SECONDS,
        mutation_timeout: float = MUTATION_TIMEOUT_SECONDS,
    ) -> None:
        self.repo_root = repo_root
        self.catalog_dir = catalog_dir
        self.policy_path = policy_path
        self.runner = runner
        self.which = which
        self.environ = dict(os.environ if environ is None else environ)
        self.home_dir = Path.home() if home_dir is None else home_dir
        self.list_timeout = list_timeout
        self.mutation_timeout = mutation_timeout
        self.preflights = PreflightStore(
            preflight_path,
            repo_root=repo_root,
            clock=clock,
            nonce_factory=nonce_factory,
        )
        self.audit = AuditJournal(audit_path, repo_root=repo_root, now=now)
        self.operation_lock_path = operation_lock_path

    def _policy_and_item(
        self,
        *,
        target: str,
        scope: str,
        operation: str,
    ) -> tuple[InstallPolicy, dict[str, Any]]:
        result: tuple[InstallPolicy, dict[str, Any]] | None = None
        failure: InstallError | None = None
        try:
            catalogs = load_catalogs(self.catalog_dir)
            policies = load_install_policies(self.policy_path, repo_root=self.repo_root)
            result = policy_for_execution(
                policies=policies,
                catalog_items=catalogs,
                target_id=target,
                scope=scope,
                operation=operation,
            )
        except InstallPolicyError as error:
            failure = InstallError(str(error), exit_code=error.exit_code)
        except Exception:
            failure = InstallError(
                "tracked Growth execution data could not be read safely", exit_code=1
            )
        if failure is not None:
            raise failure
        if result is None:
            raise InstallError(
                "tracked Growth execution data could not be read safely", exit_code=1
            )
        return result

    def _records(self, host: str) -> list[PluginRecord]:
        return scan_plugin_versions(
            host,
            runner=self.runner,
            which=self.which,
            environ=self.environ,
            home_dir=self.home_dir,
            repo_root=self.repo_root,
            timeout=self.list_timeout,
        )

    def plan(
        self,
        *,
        target: str,
        scope: str,
        operation: str,
        live_lookup: bool,
    ) -> InstallPlan:
        if not isinstance(target, str) or not EXEC_TARGET_RE.fullmatch(target):
            raise InstallError("Growth install target id is invalid", exit_code=2)
        policy, item = self._policy_and_item(target=target, scope=scope, operation=operation)
        live_record = None
        if live_lookup:
            live_record = _record_for_policy(self._records(policy.host), policy)
            if live_record is None:
                raise InstallError(
                    "reviewed plugin was not found in the exact marketplace", exit_code=2
                )
            if (
                live_record.marketplace_source != policy.marketplace_source
                or live_record.marketplace_revision != policy.marketplace_revision
            ):
                raise InstallError("reviewed marketplace source changed; review again", exit_code=2)
            if operation == "install" and live_record.version != policy.reviewed_version:
                raise InstallError(
                    "reviewed marketplace version changed; review again", exit_code=2
                )
            if operation == "install" and live_record.installed:
                raise InstallError(
                    "reviewed plugin is already installed; use inventory or remove first",
                    exit_code=2,
                )
            if operation == "remove" and not live_record.installed:
                raise InstallError(
                    "reviewed plugin is not installed at the requested scope", exit_code=2
                )
        return _build_plan(policy, item, operation=operation, live_record=live_record)

    def preflight(
        self,
        *,
        target: str,
        scope: str,
        operation: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan(
            target=target,
            scope=scope,
            operation=operation,
            live_lookup=not dry_run,
        )
        result = {"plan": plan.as_dict(), "nonce": None, "expires_at": None, "dry_run": dry_run}
        if not dry_run:
            nonce, expires_at = self.preflights.issue(plan)
            result.update({"nonce": nonce, "expires_at": expires_at})
        return result

    def _run_mutation(self, argv: Sequence[str]) -> bool:
        try:
            result = self.runner(
                list(argv),
                check=False,
                capture_output=True,
                text=True,
                timeout=self.mutation_timeout,
                env=_minimal_env(self.home_dir, self.environ),
                cwd=str(self.repo_root),
                shell=False,
                stdin=subprocess.DEVNULL,
            )
        except Exception:
            return False
        return getattr(result, "returncode", None) == 0

    def _record_audit_safely(
        self,
        plan: InstallPlan,
        *,
        correlation_id: str,
        operation: str,
        argv: Sequence[str],
        outcome: str,
    ) -> bool:
        try:
            self.audit.append(
                plan,
                correlation_id=correlation_id,
                operation=operation,
                argv=argv,
                outcome=outcome,
            )
        except InstallError:
            return False
        return True

    def _verify_absent(self, plan: InstallPlan) -> bool:
        try:
            record = _record_for_policy(
                self._records(plan.host),
                policy=_policy_from_plan(plan),
            )
        except InstallError:
            return False
        return record is None or not record.installed

    def _rollback_failed_install(
        self,
        plan: InstallPlan,
        *,
        correlation_id: str,
        initial_outcome: str,
    ) -> tuple[bool, bool]:
        """Always attempt and verify the allowlisted uninstall after install uncertainty."""
        audit_ok = self._record_audit_safely(
            plan,
            correlation_id=correlation_id,
            operation="install",
            argv=plan.argv,
            outcome=initial_outcome,
        )
        audit_ok = (
            self._record_audit_safely(
                plan,
                correlation_id=correlation_id,
                operation="remove",
                argv=plan.rollback_argv,
                outcome="rollback_started",
            )
            and audit_ok
        )
        rollback_command_ok = self._run_mutation(plan.rollback_argv)
        rollback_ok = rollback_command_ok and self._verify_absent(plan)
        audit_ok = (
            self._record_audit_safely(
                plan,
                correlation_id=correlation_id,
                operation="remove",
                argv=plan.rollback_argv,
                outcome="rollback_success" if rollback_ok else "rollback_failed",
            )
            and audit_ok
        )
        terminal_outcome = (
            "verify_failed_rolled_back"
            if rollback_ok and initial_outcome == "verify_failed"
            else "command_failed_rolled_back"
            if rollback_ok
            else "rollback_failed"
        )
        audit_ok = (
            self._record_audit_safely(
                plan,
                correlation_id=correlation_id,
                operation="install",
                argv=plan.argv,
                outcome=terminal_outcome,
            )
            and audit_ok
        )
        return rollback_ok, audit_ok

    def execute(
        self,
        *,
        nonce: str,
        target: str,
        scope: str,
        operation: str,
        yes: bool,
        allowed: bool,
        typed_plugin_id: str | None = None,
        data_scope_ack: bool = False,
        stage: Callable[[str, int, int], None] | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        if not yes or not allowed:
            raise InstallError("explicit Growth mutation consent is required", exit_code=2)
        if not isinstance(target, str) or not EXEC_TARGET_RE.fullmatch(target):
            raise InstallError("Growth install target id is invalid", exit_code=2)
        if operation not in {"install", "remove"}:
            raise InstallError("Growth plugin operation is invalid", exit_code=2)
        correlation_id = correlation_id or f"job-{secrets.token_hex(10)}"
        if not JOB_ID_RE.fullmatch(correlation_id):
            raise InstallError("Growth operation id is invalid", exit_code=1)
        update_stage = stage or (lambda _name, _step, _total: None)
        with OperationLease(self.operation_lock_path, repo_root=self.repo_root):
            update_stage("preflight", 0, 3)
            stored = self.preflights.consume(nonce)
            if stored.target != target or stored.scope != scope or stored.operation != operation:
                raise InstallError("Growth preflight confirmation did not match", exit_code=2)
            if stored.high_risk and (
                typed_plugin_id != stored.plugin_id or data_scope_ack is not True
            ):
                raise InstallError("high-risk Growth confirmation is incomplete", exit_code=2)
            try:
                current = self.plan(
                    target=target,
                    scope=scope,
                    operation=operation,
                    live_lookup=True,
                )
            except InstallError as exc:
                outcome = (
                    "blocked_version_drift"
                    if "version" in str(exc) or "source" in str(exc)
                    else "blocked_policy_drift"
                )
                self.audit.append(
                    stored,
                    correlation_id=correlation_id,
                    operation=operation,
                    argv=stored.argv,
                    outcome=outcome,
                )
                raise
            if current.as_dict() != stored.as_dict():
                self.audit.append(
                    stored,
                    correlation_id=correlation_id,
                    operation=operation,
                    argv=stored.argv,
                    outcome="blocked_policy_drift",
                )
                raise InstallError("Growth preflight changed; review again", exit_code=2)

            update_stage("installing", 1, 3)
            self.audit.append(
                current,
                correlation_id=correlation_id,
                operation=operation,
                argv=current.argv,
                outcome="started",
            )
            if not self._run_mutation(current.argv):
                if operation == "install":
                    _rollback_ok, audit_ok = self._rollback_failed_install(
                        current,
                        correlation_id=correlation_id,
                        initial_outcome="command_failed",
                    )
                    update_stage("failed", 3, 3)
                    message = (
                        "official host plugin command failed; automatic rollback was attempted"
                    )
                    if not audit_ok:
                        message += "; audit recording also failed"
                    raise InstallError(message, exit_code=1)
                self.audit.append(
                    current,
                    correlation_id=correlation_id,
                    operation=operation,
                    argv=current.argv,
                    outcome="command_failed",
                )
                update_stage("failed", 1, 3)
                raise InstallError("official host plugin command failed", exit_code=1)

            update_stage("verifying", 2, 3)
            if operation == "install":
                verification_failed = False
                try:
                    record = _record_for_policy(
                        self._records(current.host), policy=_policy_from_plan(current)
                    )
                    verification_failed = not (
                        record is not None
                        and record.installed
                        and record.version == current.reviewed_version
                        and record.marketplace_source == current.marketplace_source
                        and record.marketplace_revision == current.marketplace_revision
                    )
                except InstallError:
                    verification_failed = True
                if verification_failed:
                    _rollback_ok, audit_ok = self._rollback_failed_install(
                        current,
                        correlation_id=correlation_id,
                        initial_outcome="verify_failed",
                    )
                    update_stage("failed", 3, 3)
                    if not audit_ok:
                        raise InstallError(
                            "plugin verification failed; automatic rollback was attempted; "
                            "audit recording also failed",
                            exit_code=1,
                        )
                    raise InstallError(
                        "plugin verification failed; automatic rollback was attempted",
                        exit_code=1,
                    )
            else:
                try:
                    record = _record_for_policy(
                        self._records(current.host), policy=_policy_from_plan(current)
                    )
                    removed = record is None or not record.installed
                except InstallError:
                    removed = False
                if not removed:
                    self.audit.append(
                        current,
                        correlation_id=correlation_id,
                        operation="remove",
                        argv=current.argv,
                        outcome="remove_verify_failed",
                    )
                    update_stage("failed", 2, 3)
                    raise InstallError("plugin removal could not be verified", exit_code=1)

            self.audit.append(
                current,
                correlation_id=correlation_id,
                operation=operation,
                argv=current.argv,
                outcome="success",
            )
            update_stage("complete", 3, 3)
            return {
                "operation": operation,
                "target": target,
                "outcome": "success",
                "correlation_id": correlation_id,
            }


def _policy_from_plan(plan: InstallPlan) -> InstallPolicy:
    """Reconstruct only the identity fields needed to match a sanitized inventory record."""
    return InstallPolicy(
        target_id=plan.target,
        host=plan.host,
        plugin_id=plan.plugin_id,
        marketplace=plan.marketplace,
        marketplace_source=plan.marketplace_source,
        marketplace_revision=plan.marketplace_revision,
        reviewed_version=plan.reviewed_version,
        scope=plan.scope,
        components=plan.components,
        auth_policy=plan.auth_policy,
        data_scope=plan.data_scope,
        high_risk=plan.high_risk,
        data_scope_ack_required=plan.data_scope_ack_required,
        threat_review_artifact=plan.threat_review_artifact,
        threat_review_sha256=None,
        threat_review_version=None,
        threat_review_scope=None,
        reviewed_at="1970-01-01",
        pin_mode="immutable_marketplace_revision",
    )


__all__ = (
    "AUDIT_OUTCOMES",
    "AuditJournal",
    "GrowthInstallService",
    "InstallError",
    "InstallPlan",
    "OperationLease",
    "PluginRecord",
    "PreflightStore",
    "parse_plugin_records",
    "scan_plugin_versions",
)
