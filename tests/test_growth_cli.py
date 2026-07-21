from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_ai_lab.cli import lab
from local_ai_lab.growth import commands as growth_commands
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


def test_discovery_and_update_commands_never_network_without_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(
        growth_commands,
        "discover",
        lambda **_kwargs: pytest.fail("discovery adapter must not run without --lookup"),
    )
    monkeypatch.setattr(
        growth_commands,
        "check_updates",
        lambda **_kwargs: pytest.fail("update adapter must not run without --lookup"),
    )
    args = common_args(tmp_path)
    assert lab.main(["growth", "discover", *args, "--source", "github"]) == 2
    assert lab.main(["growth", "check-updates", *args]) == 2
    captured = capsys.readouterr()
    assert captured.err.count("requires explicit --lookup") == 2
    assert not (tmp_path / ".local-ai-lab" / "growth-inbox-v1.json").exists()


def test_discovery_lookup_and_review_cli_use_ignored_inbox_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    inbox = repo_root / ".local-ai-lab" / "growth-inbox-v1.json"
    calls = []

    def fake_discover(**kwargs):
        calls.append(kwargs)
        return {"stored": 2, "skipped": 1, "failures": 0}

    monkeypatch.setattr(growth_commands, "discover", fake_discover)
    assert (
        lab.main(
            [
                "growth",
                "discover",
                "--catalog-dir",
                str(CATALOG_DIR),
                "--repo-root",
                str(repo_root),
                "--inbox",
                str(inbox),
                "--source",
                "mcp",
                "--lookup",
                "--query",
                "local tools",
            ]
        )
        == 0
    )
    assert calls[0]["source"] == "mcp"
    assert calls[0]["query"] == "local tools"
    assert calls[0]["inbox_path"] == inbox
    output = capsys.readouterr().out
    assert "popularity is context, never approval" in output

    def fake_review(**kwargs):
        calls.append(kwargs)
        return {"id": "review-" + "a" * 20}

    monkeypatch.setattr(growth_commands, "create_review_draft", fake_review)
    inbox_id = "inbox-" + "b" * 20
    assert (
        lab.main(
            [
                "growth",
                "review",
                "--repo-root",
                str(repo_root),
                "--inbox",
                str(inbox),
                inbox_id,
            ]
        )
        == 0
    )
    assert calls[-1]["inbox_id"] == inbox_id
    assert calls[-1]["inbox_path"] == inbox
    assert "reviewed repo patch" in capsys.readouterr().out


def test_install_cli_requires_operation_consent_and_two_step_nonce(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    calls = []

    class FakeService:
        def preflight(self, **kwargs):
            calls.append(("preflight", kwargs))
            return {
                "plan": {
                    "target": "ext-safe",
                    "source": "https://example.invalid/official",
                    "reviewed_version": "1.2.3",
                    "argv": ["codex", "plugin", "add", "safe@official"],
                },
                "nonce": "N" * 32,
                "expires_at": 1234.0,
                "dry_run": kwargs["dry_run"],
            }

        def execute(self, **kwargs):
            calls.append(("execute", kwargs))
            return {"outcome": "success"}

    monkeypatch.setattr(growth_commands, "_install_service", lambda _args: FakeService())
    base = ["growth", "install", "--target", "ext-safe", "--scope", "user"]
    assert lab.main(base) == 2
    assert calls == []
    assert "--allow-install" in capsys.readouterr().err

    remove_base = ["growth", "remove", "--target", "ext-safe", "--scope", "user"]
    assert lab.main(remove_base) == 2
    assert calls == []
    assert "--allow-remove" in capsys.readouterr().err

    assert lab.main([*base, "--allow-install", "--dry-run"]) == 0
    assert calls[-1] == (
        "preflight",
        {
            "target": "ext-safe",
            "scope": "user",
            "operation": "install",
            "dry_run": True,
        },
    )
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload["plan"]["argv"], list)

    assert lab.main([*base, "--allow-install", "--yes"]) == 2
    assert "live preflight nonce" in capsys.readouterr().err
    assert (
        lab.main(
            [
                *base,
                "--allow-install",
                "--yes",
                "--nonce",
                "N" * 32,
                "--confirm-target",
                "safe",
                "--ack-data-scope",
            ]
        )
        == 0
    )
    assert calls[-1][0] == "execute"
    assert calls[-1][1]["typed_plugin_id"] == "safe"
    assert calls[-1][1]["data_scope_ack"] is True


def test_install_cli_rejects_private_catalog_or_policy_overrides_before_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    called = False

    def forbidden_service(_args):
        nonlocal called
        called = True
        raise AssertionError("noncanonical mutation state must not reach the service")

    monkeypatch.setattr(growth_commands, "_install_service", forbidden_service)
    result = lab.main(
        [
            "growth",
            "install",
            "--target",
            "ext-semgrep-mcp",
            "--scope",
            "user",
            "--allow-install",
            "--dry-run",
            "--repo-root",
            str(tmp_path),
            "--catalog-dir",
            str(tmp_path / "data" / "growth_registry"),
            "--policy",
            str(tmp_path / "data" / "growth_registry" / "install-policies.json"),
        ]
    )
    assert result == 2
    assert called is False
    assert "canonical reviewed repository state" in capsys.readouterr().err
