from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from local_ai_lab.cli import lab
from local_ai_lab.cli.hardware import collect_hardware_snapshot, format_snapshot, write_snapshot


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["fake"], returncode, stdout=stdout, stderr="")


def test_hardware_snapshot_uses_fakes_and_excludes_private_paths(monkeypatch) -> None:
    private_path = "/Users/example/.local/bin/ollama"
    calls: list[list[str]] = []

    def fake_resolver(name: str) -> str | None:
        return private_path if name == "ollama" else None

    def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command == ["sysctl", "-n", "machdep.cpu.brand_string"]:
            return completed("Apple M3 Ultra\n")
        if command == ["sysctl", "-n", "hw.memsize"]:
            return completed("274877906944\n")
        if command == ["ollama", "--version"]:
            return completed("ollama version 0.9.0\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("local_ai_lab.cli.hardware.platform.system", lambda: "Darwin")

    snapshot = collect_hardware_snapshot(
        command_runner=fake_runner,
        command_resolver=fake_resolver,
        now=datetime(2026, 6, 17, 12, 0, 0, tzinfo=UTC),
    )
    payload = format_snapshot(snapshot)

    assert snapshot["schema_version"] == "hardware-snapshot-v0.1"
    assert snapshot["macos"]["chip_brand"] == "Apple M3 Ultra"
    assert snapshot["macos"]["memory_bytes"] == 274877906944
    assert snapshot["runtimes"]["ollama"]["present"] is True
    assert snapshot["runtimes"]["ollama"]["version"] == "ollama version 0.9.0"
    assert snapshot["runtimes"]["lms"]["present"] is False
    assert "/Users/example" not in payload
    assert private_path not in payload
    assert all("list" not in command for command in calls)


def test_hardware_snapshot_handles_missing_optional_commands(monkeypatch) -> None:
    def fake_resolver(name: str) -> str | None:
        del name
        return None

    def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("local_ai_lab.cli.hardware.platform.system", lambda: "Linux")

    snapshot = collect_hardware_snapshot(
        command_runner=fake_runner,
        command_resolver=fake_resolver,
        now=datetime(2026, 6, 17, 12, 0, 0, tzinfo=UTC),
    )

    assert snapshot["runtimes"]["ollama"] == {"present": False, "version": None}
    assert snapshot["runtimes"]["lms"] == {"present": False, "version": None}


def test_hardware_snapshot_out_writes_repo_local_json(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(lab, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        lab,
        "collect_hardware_snapshot",
        lambda: {
            "schema_version": "hardware-snapshot-v0.1",
            "captured_at": "2026-06-17T12:00:00Z",
            "runtimes": {},
        },
    )

    exit_code = lab.main(["hardware", "snapshot", "--out", "docs/lab-notes/hardware.json"])

    assert exit_code == 0
    output_path = tmp_path / "docs" / "lab-notes" / "hardware.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "hardware-snapshot-v0.1"
    stdout = capsys.readouterr().out
    assert json.loads(stdout)["schema_version"] == "hardware-snapshot-v0.1"


def test_hardware_snapshot_out_rejects_paths_outside_repo(tmp_path) -> None:
    with pytest.raises(ValueError, match="inside the repository"):
        write_snapshot(Path("/tmp/outside-ai-lab-hardware.json"), {}, repo_root=tmp_path)


def test_hardware_snapshot_command_rejects_outside_repo_path(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(lab, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        lab,
        "collect_hardware_snapshot",
        lambda: {
            "schema_version": "hardware-snapshot-v0.1",
            "captured_at": "2026-06-17T12:00:00Z",
            "runtimes": {},
        },
    )

    exit_code = lab.main(["hardware", "snapshot", "--out", "/tmp/outside-ai-lab.json"])

    assert exit_code == 2
    assert "inside the repository" in capsys.readouterr().err
