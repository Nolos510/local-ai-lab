from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_ai_lab.cli import lab
from local_ai_lab.growth import inventory
from local_ai_lab.growth.state import load_state

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "data" / "growth_registry"


def common_args(tmp_path: Path, repo_root: Path | None = None) -> list[str]:
    return [
        "--catalog-dir",
        str(CATALOG_DIR),
        "--state",
        str(tmp_path / ".local-ai-lab" / "growth-state-v1.json"),
        "--repo-root",
        str(repo_root or REPO_ROOT),
    ]


def test_growth_list_filters_and_json_shape(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    exit_code = lab.main(
        [
            "growth",
            "list",
            *common_args(tmp_path),
            "--kind",
            "skill",
            "--role",
            "AIA",
            "--effort",
            "1-3",
            "--json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "growth-list-v1"
    assert [item["id"] for item in payload["items"]] == ["skill-code-review"]
    assert payload["items"][0]["evidenced"] is True


def test_repo_scan_dry_run_is_read_only_and_sanitized(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    repo_root = tmp_path / "repo"
    skill = repo_root / "skills" / "code-review"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("fixture\n", encoding="utf-8")
    state_path = tmp_path / ".local-ai-lab" / "growth-state-v1.json"
    exit_code = lab.main(
        [
            "growth",
            "scan",
            *common_args(tmp_path, repo_root),
            "--ecosystem",
            "repo",
            "--dry-run",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "code-review\trepo\trepo_skills\tskill" in captured.out
    assert "dry-run: private growth state was not changed" in captured.out
    assert str(tmp_path) not in captured.out + captured.err
    assert not state_path.exists()


def test_scan_writes_only_normalized_private_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    secret = "sk-raw-private-value"
    home = tmp_path / "Users" / "alice"
    monkeypatch.setattr(inventory.Path, "home", classmethod(lambda _cls: home))
    monkeypatch.setattr(inventory.shutil, "which", lambda _name: "/safe/codex")

    def fake_run(argv, **_kwargs):
        if argv[1] == "plugin":
            stdout = json.dumps(
                {
                    "plugins": [
                        {"id": "safe-plugin", "enabled": True, "secret": secret},
                        {"id": "alice-private", "path": str(home)},
                    ]
                }
            )
        else:
            stdout = json.dumps({"servers": {"safe-mcp": {"enabled": False}}})
        return SimpleNamespace(returncode=0, stdout=stdout, stderr=f"ignored {secret}")

    monkeypatch.setattr(inventory.subprocess, "run", fake_run)
    state_path = tmp_path / ".local-ai-lab" / "growth-state-v1.json"
    exit_code = lab.main(
        [
            "growth",
            "scan",
            *common_args(tmp_path),
            "--ecosystem",
            "codex",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    stored = state_path.read_text(encoding="utf-8")
    combined = captured.out + captured.err + stored
    assert "safe-plugin" in combined
    assert "safe-mcp" in combined
    assert secret not in combined
    assert "alice" not in combined
    assert str(home) not in combined
    state = load_state(state_path)
    assert {entry["id"] for entry in state["inventory"]} == {"safe-mcp", "safe-plugin"}


def test_scan_exit_codes_for_missing_cli_and_malformed_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(inventory.shutil, "which", lambda _name: None)
    assert (
        lab.main(
            [
                "growth",
                "scan",
                *common_args(tmp_path),
                "--ecosystem",
                "codex",
            ]
        )
        == 2
    )
    assert "CLI is not available" in capsys.readouterr().err

    monkeypatch.setattr(inventory.shutil, "which", lambda _name: "/safe/codex")
    monkeypatch.setattr(
        inventory.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="raw /Users/alice sk-secret",
            stderr="token=sk-secret",
        ),
    )
    assert (
        lab.main(
            [
                "growth",
                "scan",
                *common_args(tmp_path),
                "--ecosystem",
                "codex",
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "inventory response was invalid" in captured.err
    assert "alice" not in captured.err
    assert "sk-secret" not in captured.err


def test_growth_progress_is_atomic_catalog_gated_and_evidence_narrow(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    repo_root = tmp_path / "repo"
    evidence = repo_root / "reports" / "proof.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("proof\n", encoding="utf-8")
    args = common_args(tmp_path, repo_root)
    assert (
        lab.main(
            [
                "growth",
                "progress",
                *args,
                "skill-code-review",
                "--status",
                "completed",
                "--evidence",
                str(evidence),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "skill-code-review -> completed" in captured.out
    assert str(tmp_path) not in captured.out + captured.err
    state = load_state(tmp_path / ".local-ai-lab" / "growth-state-v1.json")
    assert state["progress"] == [
        {
            "item_id": "skill-code-review",
            "status": "completed",
            "evidence": "reports/proof.md",
        }
    ]

    assert (
        lab.main(
            [
                "growth",
                "progress",
                *args,
                "unknown-private-item",
                "--status",
                "queued",
            ]
        )
        == 2
    )
    assert "not in the reviewed Growth catalog" in capsys.readouterr().err


def test_progress_rejects_outside_home_evidence_without_leak(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "Users" / "alice" / "private.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("private\n", encoding="utf-8")
    exit_code = lab.main(
        [
            "growth",
            "progress",
            *common_args(tmp_path, repo_root),
            "skill-code-review",
            "--status",
            "completed",
            "--evidence",
            str(outside),
        ]
    )
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "existing repo-relative artifact" in captured.err
    assert "alice" not in captured.err
    assert str(tmp_path) not in captured.err


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["list", "--role", "/Users/alice/sk-secret"], "unsupported career role"),
        (["list", "--effort", "sk-secret"], "unsupported effort tier"),
        (["scan", "--ecosystem", "/Users/alice"], "unsupported inventory ecosystem"),
        (
            ["progress", "skill-code-review", "--status", "sk-secret"],
            "unsupported progress status",
        ),
    ],
)
def test_invalid_growth_values_return_two_without_echoing_them(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    argv: list[str],
    expected: str,
) -> None:
    command = ["growth", argv[0], *common_args(tmp_path), *argv[1:]]
    assert lab.main(command) == 2
    captured = capsys.readouterr()
    assert expected in captured.err
    assert "alice" not in captured.err
    assert "sk-secret" not in captured.err
    assert "/Users" not in captured.err


def test_growth_argparse_errors_are_privacy_narrow(
    capsys: pytest.CaptureFixture,
) -> None:
    with pytest.raises(SystemExit) as exc:
        lab.main(["growth", "list", "--credential-sk-secret", "/Users/alice"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "ai-lab growth error: invalid arguments" in captured.err
    assert "alice" not in captured.err
    assert "sk-secret" not in captured.err
    assert "/Users" not in captured.err
