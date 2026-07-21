from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_ai_lab.growth import state as growth_state
from local_ai_lab.growth.state import StateError, load_state, update_progress, validate_state


def test_progress_write_uses_atomic_replace_and_repo_relative_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    evidence = repo_root / "reports" / "proof.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("proof\n", encoding="utf-8")
    state_path = repo_root / ".local-ai-lab" / "growth-state-v1.json"
    real_replace = growth_state.os.replace
    replacements = []

    def spy_replace(source, target):
        replacements.append((Path(source), Path(target)))
        real_replace(source, target)

    monkeypatch.setattr(growth_state.os, "replace", spy_replace)
    payload = update_progress(
        state_path,
        item_id="skill-example",
        status="completed",
        evidence_path=evidence,
        repo_root=repo_root,
    )
    assert replacements and replacements[0][1] == state_path
    assert replacements[0][0].parent == state_path.parent
    assert payload["progress"] == [
        {
            "item_id": "skill-example",
            "status": "completed",
            "evidence": "reports/proof.md",
        }
    ]
    assert load_state(state_path) == payload
    assert not list(state_path.parent.glob("*.tmp"))
    assert state_path.parent.stat().st_mode & 0o777 == 0o700
    assert state_path.stat().st_mode & 0o777 == 0o600


def test_progress_without_new_evidence_preserves_existing_proof(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    evidence = repo_root / "proof.md"
    repo_root.mkdir()
    evidence.write_text("proof\n", encoding="utf-8")
    state_path = repo_root / ".local-ai-lab" / "growth-state-v1.json"
    update_progress(
        state_path,
        item_id="skill-example",
        status="in_progress",
        evidence_path=evidence,
        repo_root=repo_root,
    )
    payload = update_progress(
        state_path,
        item_id="skill-example",
        status="completed",
        evidence_path=None,
        repo_root=repo_root,
    )
    assert payload["progress"][0]["evidence"] == "proof.md"


def test_outside_or_missing_evidence_is_rejected_without_path_leak(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "Users" / "alice" / "secret-proof.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("secret\n", encoding="utf-8")
    with pytest.raises(StateError) as exc:
        update_progress(
            repo_root / ".local-ai-lab" / "growth-state-v1.json",
            item_id="skill-example",
            status="completed",
            evidence_path=outside,
            repo_root=repo_root,
        )
    message = str(exc.value)
    assert "alice" not in message
    assert str(tmp_path) not in message
    assert not (repo_root / ".local-ai-lab" / "growth-state-v1.json").exists()


def test_malformed_state_is_not_overwritten_or_echoed(tmp_path: Path) -> None:
    path = tmp_path / "growth-state-v1.json"
    raw = '{"secret": "sk-do-not-echo", "home": "/Users/alice"}'
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(StateError) as exc:
        load_state(path)
    assert "sk-do-not-echo" not in str(exc.value)
    assert "alice" not in str(exc.value)
    assert path.read_text(encoding="utf-8") == raw


def test_state_validation_rejects_absolute_paths_and_extra_private_fields() -> None:
    payload = growth_state.empty_state()
    payload["progress"] = [
        {
            "item_id": "skill-example",
            "status": "completed",
            "evidence": "/Users/alice/private.md",
        }
    ]
    with pytest.raises(StateError):
        validate_state(payload)

    payload = json.loads(json.dumps(growth_state.empty_state()))
    payload["username"] = "alice"
    with pytest.raises(StateError):
        validate_state(payload)
