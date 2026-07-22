from __future__ import annotations

import json

from local_ai_lab.cli import lab
from local_ai_lab.skills_lab import commands


def test_skills_status_reports_blocked_without_install_language(capsys) -> None:
    exit_code = lab.main(["skills", "status"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Status: blocked" in captured.out
    assert "review-only" in captured.out
    assert "activation_permitted" not in captured.out
    assert captured.err == ""


def test_skills_handoff_blocks_codex(capsys) -> None:
    exit_code = lab.main(["skills", "handoff", "--host", "codex"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == {
        "activation_permitted": False,
        "host": "codex",
        "next_step": "run more isolated reviewed trials; do not install or adopt",
        "state": "blocked_until_qualified",
    }


def test_skills_preflight_is_nonzero_while_qualification_is_blocked(capsys) -> None:
    exit_code = lab.main(
        [
            "skills",
            "preflight",
            "--checkout",
            "/Users/example/private-skillopt-checkout",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["execution_permitted"] is False
    assert payload["activation_permitted"] is False
    assert "private-skillopt-checkout" not in json.dumps(payload)


def test_default_evidence_is_the_reviewed_repo_file() -> None:
    assert commands.DEFAULT_EVIDENCE.name == "skillopt-pilot.json"
    assert commands.DEFAULT_EVIDENCE.parent.name == "skills_lab"
