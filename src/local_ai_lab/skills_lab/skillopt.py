"""Qualification boundary for the external SkillOpt pilot.

This module reads sanitized trial summaries and performs a read-only checkout
inspection. It deliberately has no optimizer execution or installation path.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PINNED_SKILLOPT_COMMIT = "61735e3922efc2b90c6d6cab561e62e98452ca90"
EVIDENCE_SCHEMA = "skillopt-pilot-evidence-v1"
MIN_TRIALS = 5
MIN_SUCCESS_RATE = 0.8
MAX_EVIDENCE_BYTES = 256 * 1024
SAFE_TRIAL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
PROHIBITED_EVIDENCE_KEYS = {
    "api_key",
    "document",
    "endpoint",
    "path",
    "prompt",
    "raw_response",
    "response",
    "secret",
    "transcript",
}


class SkillOptEvidenceError(ValueError):
    """Raised when pilot evidence is missing, unsafe, or malformed."""


@dataclass(frozen=True)
class TrialEvidence:
    trial_id: str
    accepted: bool
    validation_before: float
    validation_after: float
    test_hard: float
    test_soft: float
    edit_count: int
    backend_error: bool


@dataclass(frozen=True)
class QualificationResult:
    status: str
    trial_count: int
    accepted_count: int
    successful_count: int
    success_rate: float
    required_trials: int
    required_success_rate: float
    reasons: tuple[str, ...]

    @property
    def qualified(self) -> bool:
        return self.status == "qualified"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["qualified"] = self.qualified
        payload["reasons"] = list(self.reasons)
        return payload


def _contains_prohibited_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in PROHIBITED_EVIDENCE_KEYS:
                return True
            if _contains_prohibited_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_prohibited_key(item) for item in value)
    return False


def _score(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SkillOptEvidenceError(f"{field} must be a number between 0 and 1")
    score = float(value)
    if not 0.0 <= score <= 1.0:
        raise SkillOptEvidenceError(f"{field} must be a number between 0 and 1")
    return score


def _trial(payload: Any) -> TrialEvidence:
    if not isinstance(payload, dict):
        raise SkillOptEvidenceError("each trial must be an object")
    expected = {
        "trial_id",
        "accepted",
        "validation_before",
        "validation_after",
        "test_hard",
        "test_soft",
        "edit_count",
        "backend_error",
    }
    if set(payload) != expected:
        raise SkillOptEvidenceError("trial fields do not match the sanitized evidence schema")
    trial_id = payload["trial_id"]
    if not isinstance(trial_id, str) or not SAFE_TRIAL_ID.fullmatch(trial_id):
        raise SkillOptEvidenceError("trial_id is invalid")
    if not isinstance(payload["accepted"], bool) or not isinstance(
        payload["backend_error"], bool
    ):
        raise SkillOptEvidenceError("trial status fields must be boolean")
    edit_count = payload["edit_count"]
    if isinstance(edit_count, bool) or not isinstance(edit_count, int) or edit_count < 0:
        raise SkillOptEvidenceError("edit_count must be a non-negative integer")
    return TrialEvidence(
        trial_id=trial_id,
        accepted=payload["accepted"],
        validation_before=_score(payload["validation_before"], field="validation_before"),
        validation_after=_score(payload["validation_after"], field="validation_after"),
        test_hard=_score(payload["test_hard"], field="test_hard"),
        test_soft=_score(payload["test_soft"], field="test_soft"),
        edit_count=edit_count,
        backend_error=payload["backend_error"],
    )


def load_evidence(path: Path) -> dict[str, Any]:
    """Load a bounded, sanitized pilot evidence file."""

    try:
        if not path.is_file() or path.stat().st_size > MAX_EVIDENCE_BYTES:
            raise SkillOptEvidenceError("pilot evidence is missing or exceeds the size limit")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except SkillOptEvidenceError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SkillOptEvidenceError("pilot evidence could not be read") from exc
    if not isinstance(payload, dict) or _contains_prohibited_key(payload):
        raise SkillOptEvidenceError("pilot evidence contains unsupported or sensitive fields")
    expected = {"schema_version", "tool", "policy", "trials"}
    if set(payload) != expected or payload.get("schema_version") != EVIDENCE_SCHEMA:
        raise SkillOptEvidenceError("pilot evidence schema is unsupported")
    tool = payload.get("tool")
    if not isinstance(tool, dict) or tool.get("pinned_commit") != PINNED_SKILLOPT_COMMIT:
        raise SkillOptEvidenceError("pilot evidence does not match the reviewed SkillOpt revision")
    policy = payload.get("policy")
    required_policy = {
        "gate_mode": "hard",
        "task_source": "synthetic_reviewed",
        "untouched_test": True,
        "auto_adopt": False,
        "transcript_harvest": False,
    }
    if policy != required_policy:
        raise SkillOptEvidenceError("pilot evidence does not satisfy the review-only policy")
    trials = payload.get("trials")
    if not isinstance(trials, list):
        raise SkillOptEvidenceError("pilot trials must be a list")
    parsed_trials = [_trial(item) for item in trials]
    if len({trial.trial_id for trial in parsed_trials}) != len(parsed_trials):
        raise SkillOptEvidenceError("pilot trial ids must be unique")
    return {**payload, "trials": parsed_trials}


def evaluate_qualification(evidence: dict[str, Any]) -> QualificationResult:
    """Apply the conservative promotion gate to parsed evidence."""

    trials: list[TrialEvidence] = evidence["trials"]
    accepted = [trial for trial in trials if trial.accepted]
    successful = [
        trial
        for trial in accepted
        if not trial.backend_error
        and trial.validation_after > trial.validation_before
        and trial.test_hard == 1.0
    ]
    success_rate = len(successful) / len(trials) if trials else 0.0
    reasons: list[str] = []
    if len(trials) < MIN_TRIALS:
        reasons.append(f"needs at least {MIN_TRIALS} fresh independent trials")
    if success_rate < MIN_SUCCESS_RATE:
        reasons.append(f"successful improvement rate must be at least {MIN_SUCCESS_RATE:.0%}")
    if any(trial.backend_error for trial in trials):
        reasons.append("backend errors are not allowed")
    if any(trial.test_hard != 1.0 for trial in accepted):
        reasons.append("every accepted candidate must score 100% on the untouched hard test")
    if any(trial.validation_after <= trial.validation_before for trial in accepted):
        reasons.append("every accepted candidate must improve hard validation")
    status = "blocked" if reasons else "qualified"
    return QualificationResult(
        status=status,
        trial_count=len(trials),
        accepted_count=len(accepted),
        successful_count=len(successful),
        success_rate=success_rate,
        required_trials=MIN_TRIALS,
        required_success_rate=MIN_SUCCESS_RATE,
        reasons=tuple(reasons),
    )


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def inspect_checkout(
    checkout: Path,
    *,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Inspect an external checkout without executing SkillOpt code."""

    if not checkout.is_dir() or not (checkout / "pyproject.toml").is_file():
        return {"status": "missing", "pinned": False, "head": None}
    try:
        result = run_command(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
    except (OSError, subprocess.SubprocessError):
        return {"status": "unreadable", "pinned": False, "head": None}
    head = result.stdout.strip() if result.returncode == 0 else ""
    pinned = head == PINNED_SKILLOPT_COMMIT
    return {
        "status": "ready" if pinned else "revision_mismatch",
        "pinned": pinned,
        "head": head if re.fullmatch(r"[0-9a-f]{40}", head) else None,
    }


def host_handoff(host: str, qualification: QualificationResult) -> dict[str, Any]:
    """Describe, but never perform, the next integration state for one host."""

    if host not in {"local", "codex", "claude"}:
        raise ValueError("unsupported host")
    if not qualification.qualified:
        state = "evaluation_only" if host == "local" else "blocked_until_qualified"
        next_step = "run more isolated reviewed trials; do not install or adopt"
    else:
        state = "growth_review_required"
        next_step = "open a separate reviewed Growth policy and threat-model change"
    return {
        "host": host,
        "state": state,
        "activation_permitted": False,
        "next_step": next_step,
    }
