from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from local_ai_lab.skills_lab import skillopt


def evidence_payload(trials: list[dict]) -> dict:
    return {
        "schema_version": skillopt.EVIDENCE_SCHEMA,
        "tool": {
            "name": "SkillOpt",
            "repository": "https://github.com/microsoft/SkillOpt",
            "pinned_commit": skillopt.PINNED_SKILLOPT_COMMIT,
        },
        "policy": {
            "gate_mode": "hard",
            "task_source": "synthetic_reviewed",
            "untouched_test": True,
            "auto_adopt": False,
            "transcript_harvest": False,
        },
        "trials": trials,
    }


def trial(index: int, *, accepted: bool = True, hard: float = 1.0) -> dict:
    return {
        "trial_id": f"repeat-{index}",
        "accepted": accepted,
        "validation_before": 0.0,
        "validation_after": 0.5 if accepted else 0.0,
        "test_hard": hard if accepted else 0.0,
        "test_soft": 1.0 if accepted else 0.1,
        "edit_count": 1 if accepted else 0,
        "backend_error": False,
    }


def write_evidence(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_current_repeatability_shape_is_blocked(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    write_evidence(
        path,
        evidence_payload(
            [trial(1, accepted=False), trial(2, accepted=False), trial(3, hard=0.75)]
        ),
    )

    result = skillopt.evaluate_qualification(skillopt.load_evidence(path))

    assert result.status == "blocked"
    assert result.trial_count == 3
    assert result.successful_count == 0
    assert any("five" in reason or "5" in reason for reason in result.reasons)
    assert any("100%" in reason for reason in result.reasons)


def test_five_repeatable_perfect_trials_qualify(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    write_evidence(path, evidence_payload([trial(index) for index in range(5)]))

    result = skillopt.evaluate_qualification(skillopt.load_evidence(path))

    assert result.qualified is True
    assert result.success_rate == 1.0
    assert result.reasons == ()


@pytest.mark.parametrize("key", ["prompt", "raw_response", "transcript", "api_key", "path"])
def test_evidence_rejects_sensitive_fields(tmp_path: Path, key: str) -> None:
    path = tmp_path / "evidence.json"
    payload = evidence_payload([trial(1)])
    payload[key] = "must-not-be-stored"
    write_evidence(path, payload)

    with pytest.raises(skillopt.SkillOptEvidenceError, match="sensitive"):
        skillopt.load_evidence(path)


def test_checkout_inspection_uses_fixed_read_only_git_argv(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, skillopt.PINNED_SKILLOPT_COMMIT + "\n", "")

    result = skillopt.inspect_checkout(tmp_path, run_command=fake_run)

    assert result == {
        "status": "ready",
        "pinned": True,
        "head": skillopt.PINNED_SKILLOPT_COMMIT,
    }
    assert calls[0][0] == ["git", "-C", str(tmp_path), "rev-parse", "HEAD"]
    assert calls[0][1] == {
        "check": False,
        "capture_output": True,
        "text": True,
        "timeout": 5.0,
    }


def test_handoff_never_permits_activation(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    write_evidence(path, evidence_payload([trial(index) for index in range(5)]))
    result = skillopt.evaluate_qualification(skillopt.load_evidence(path))

    for host in ("local", "codex", "claude"):
        handoff = skillopt.host_handoff(host, result)
        assert handoff["state"] == "growth_review_required"
        assert handoff["activation_permitted"] is False
