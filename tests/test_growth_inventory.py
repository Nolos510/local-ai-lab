from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_ai_lab.growth.inventory import InventoryError, scan_inventory


def catalog_item(
    item_id: str,
    alias: str,
    proof: str,
) -> dict[str, object]:
    return {
        "id": item_id,
        "inventory_aliases": [alias],
        "proof_artifact": proof,
    }


def make_skill(root: Path, relative: str) -> None:
    path = root / relative
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text("# fixture\n", encoding="utf-8")


def result(payload: object, *, returncode: int = 0, stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=json.dumps(payload), stderr=stderr)


def test_repo_skills_are_installed_but_only_existing_proof_is_evidenced(tmp_path: Path) -> None:
    make_skill(tmp_path, "skills/code-review")
    make_skill(tmp_path, "skills/planned-skill")
    catalog = [
        catalog_item("skill-code-review", "code-review", "skills/code-review/SKILL.md"),
        catalog_item("skill-planned", "planned-skill", "reports/growth/planned.md"),
    ]
    records = scan_inventory(
        repo_root=tmp_path,
        catalog_items=catalog,
        ecosystem="repo",
        home_dir=tmp_path / "home",
        environ={"PATH": "/bin"},
        which=lambda _name: pytest.fail("repo scan must not inspect host CLIs"),
        runner=lambda *_args, **_kwargs: pytest.fail("repo scan must not run subprocesses"),
    )
    by_id = {entry["id"]: entry for entry in records}
    assert by_id["code-review"] == {
        "id": "code-review",
        "kind": "skill",
        "ecosystem": "repo",
        "source": "repo_skills",
        "available": True,
        "configured": False,
        "installed": True,
        "enabled": False,
        "referenced": True,
        "evidenced": True,
    }
    assert by_id["planned-skill"]["installed"] is True
    assert by_id["planned-skill"]["evidenced"] is False


def test_codex_cli_inventory_normalizes_status_and_strips_private_fields(tmp_path: Path) -> None:
    home = tmp_path / "alice"
    make_skill(home, ".codex/skills/home-skill")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        if argv[1:3] == ["plugin", "list"]:
            return result(
                {
                    "plugins": [
                        {
                            "id": "safe-plugin",
                            "enabled": True,
                            "token": "sk-never-store",
                            "path": "/Users/alice/private",
                        },
                        {"id": "alice-private"},
                    ]
                }
            )
        return result({"servers": {"local-docs": {"enabled": False}}})

    records = scan_inventory(
        repo_root=tmp_path,
        catalog_items=[],
        ecosystem="codex",
        home_dir=home,
        environ={
            "PATH": "/safe/bin",
            "USER": "alice",
            "API_TOKEN": "sk-never-pass",
        },
        which=lambda name: "/safe/bin/codex" if name == "codex" else None,
        runner=fake_run,
    )
    assert {entry["id"] for entry in records} == {"home-skill", "local-docs", "safe-plugin"}
    plugin = next(entry for entry in records if entry["id"] == "safe-plugin")
    assert plugin["installed"] is True
    assert plugin["configured"] is False
    assert plugin["enabled"] is True
    mcp = next(entry for entry in records if entry["id"] == "local-docs")
    assert mcp["configured"] is True
    assert mcp["installed"] is False
    for argv, kwargs in calls:
        assert isinstance(argv, list)
        assert kwargs["check"] is False
        assert kwargs["capture_output"] is True
        assert kwargs["env"] == {
            "HOME": str(home),
            "PATH": "/safe/bin",
            "NO_COLOR": "1",
        }
    serialized = json.dumps(records)
    assert "alice" not in serialized
    assert "sk-never" not in serialized
    assert str(home) not in serialized


def test_same_id_in_codex_and_claude_ecosystems_is_not_collapsed(tmp_path: Path) -> None:
    def fake_run(argv, **_kwargs):
        if argv[1] == "plugin":
            return result([{"id": "shared-id", "installed": True}])
        return result([])

    records = scan_inventory(
        repo_root=tmp_path,
        catalog_items=[],
        ecosystem="all",
        home_dir=tmp_path / "home",
        environ={"PATH": "/safe/bin"},
        which=lambda name: f"/safe/bin/{name}",
        runner=fake_run,
    )
    shared = [entry for entry in records if entry["id"] == "shared-id"]
    assert [(entry["ecosystem"], entry["source"]) for entry in shared] == [
        ("claude", "claude_plugin_cli"),
        ("codex", "codex_plugin_cli"),
    ]


def test_duplicate_records_within_one_source_are_merged_deterministically(tmp_path: Path) -> None:
    def fake_run(argv, **_kwargs):
        if argv[1] == "plugin":
            return result(
                [
                    {"id": "duplicate", "enabled": False},
                    {"id": "duplicate", "enabled": True},
                ]
            )
        return result([])

    records = scan_inventory(
        repo_root=tmp_path,
        catalog_items=[],
        ecosystem="codex",
        home_dir=tmp_path / "home",
        environ={"PATH": "/safe/bin"},
        which=lambda _name: "/safe/bin/codex",
        runner=fake_run,
    )
    assert len(records) == 1
    assert records[0]["enabled"] is True


def test_plugin_available_and_installed_collections_remain_distinct(tmp_path: Path) -> None:
    def fake_run(argv, **_kwargs):
        if argv[1] == "plugin":
            return result(
                {
                    "installed": [{"id": "installed-one", "enabled": True}],
                    "available": [{"id": "available-one"}],
                }
            )
        return result([])

    records = scan_inventory(
        repo_root=tmp_path,
        catalog_items=[],
        ecosystem="codex",
        home_dir=tmp_path / "home",
        environ={"PATH": "/safe/bin"},
        which=lambda _name: "/safe/bin/codex",
        runner=fake_run,
    )
    by_id = {entry["id"]: entry for entry in records}
    assert by_id["installed-one"]["installed"] is True
    assert by_id["available-one"]["available"] is True
    assert by_id["available-one"]["installed"] is False


def test_missing_cli_is_exit_two_and_claude_is_optional_for_all(tmp_path: Path) -> None:
    with pytest.raises(InventoryError) as exc:
        scan_inventory(
            repo_root=tmp_path,
            catalog_items=[],
            ecosystem="codex",
            home_dir=tmp_path / "private-user",
            environ={"PATH": "/bin"},
            which=lambda _name: None,
        )
    assert exc.value.exit_code == 2
    assert "private-user" not in str(exc.value)

    records = scan_inventory(
        repo_root=tmp_path,
        catalog_items=[],
        ecosystem="repo",
        home_dir=tmp_path / "private-user",
        environ={"PATH": "/bin"},
        which=lambda _name: None,
    )
    assert records == []


def test_malformed_or_failed_cli_never_echoes_raw_output(tmp_path: Path) -> None:
    raw_secret = "sk-private-raw-output"

    def malformed(_argv, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=f"not json {raw_secret}", stderr="")

    with pytest.raises(InventoryError) as exc:
        scan_inventory(
            repo_root=tmp_path,
            catalog_items=[],
            ecosystem="codex",
            home_dir=tmp_path / "home",
            environ={"PATH": "/bin"},
            which=lambda _name: "/bin/codex",
            runner=malformed,
        )
    assert exc.value.exit_code == 1
    assert raw_secret not in str(exc.value)
    assert str(tmp_path) not in str(exc.value)
