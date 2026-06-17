from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_ai_lab.cli import lab


def write_registry(path: Path) -> None:
    fieldnames = [
        "candidate_id",
        "model_name",
        "model_family",
        "provider_or_org",
        "status",
        "format_or_runtime",
        "source_packet_path",
        "report_path",
        "benchmark_run_id",
        "model_page_url",
        "github_url",
        "lm_studio_url",
        "ollama_url",
        "runtime_availability",
        "local_runner",
        "local_model_id",
        "default_endpoint",
        "why_interesting",
        "risk_notes",
        "proposed_eval",
        "security_review_status",
        "download_approval",
        "license_review_status",
        "provenance_status",
        "security_notes",
        "isolation_notes",
        "security_review_path",
    ]
    rows = [
        {
            "candidate_id": "candidate-ready",
            "model_name": "Ready Model",
            "model_family": "Ready",
            "provider_or_org": "Local Org",
            "status": "ready_for_eval",
            "format_or_runtime": "GGUF",
            "model_page_url": "https://example.test/model",
            "local_runner": "llama.cpp",
            "why_interesting": "Small local candidate.",
            "proposed_eval": "Run local benchmark spec.",
        },
        {
            "candidate_id": "candidate-watch",
            "model_name": "Watch Model",
            "status": "watchlist",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_dashboard_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE models (id integer primary key)")
        conn.execute("CREATE TABLE model_runs (id integer primary key)")
        conn.execute("CREATE TABLE eval_scores (id integer primary key)")
        conn.execute("CREATE TABLE decisions (id integer primary key)")
        conn.execute("INSERT INTO models (id) VALUES (1)")
        conn.execute("INSERT INTO model_runs (id) VALUES (1)")
        conn.execute("INSERT INTO eval_scores (id) VALUES (1)")
        conn.execute("INSERT INTO decisions (id) VALUES (1)")


def capture_commands(monkeypatch):
    commands = []

    def fake_run(command, check=False):
        commands.append(command)
        assert check is False
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(lab.subprocess, "run", fake_run)
    return commands


def test_status_reads_registry_artifacts_and_dashboard_db(tmp_path, capsys) -> None:
    registry = tmp_path / "candidates.csv"
    eval_results = tmp_path / "eval_results"
    db_path = tmp_path / "dashboard.sqlite"
    write_registry(registry)
    write_dashboard_db(db_path)
    (eval_results / "run-one").mkdir(parents=True)

    exit_code = lab.main(
        [
            "status",
            "--registry",
            str(registry),
            "--eval-results",
            str(eval_results),
            "--db",
            str(db_path),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Candidates: 2" in output
    assert "ready_for_eval: 1" in output
    assert "watchlist: 1" in output
    assert "Benchmark artifacts: 1" in output
    assert "models=1, runs=1, scores=1, decisions=1" in output


def test_radar_list_filters_candidates(tmp_path, capsys) -> None:
    registry = tmp_path / "candidates.csv"
    write_registry(registry)

    exit_code = lab.main(["radar", "list", "--registry", str(registry), "--status", "watchlist"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "candidate_id\tstatus\tmodel_name\tlocal_runner" in output
    assert "candidate-watch\twatchlist\tWatch Model\t" in output
    assert "candidate-ready" not in output


def test_bench_run_builds_harness_init_command(tmp_path, monkeypatch) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)
    commands = capture_commands(monkeypatch)

    exit_code = lab.main(
        [
            "bench",
            "run",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--run-id",
            "20260616-candidate-ready-r1",
            "--output-root",
            str(output_root),
        ]
    )

    assert exit_code == 0
    command = commands[0]
    assert command[:3] == [lab.sys.executable, str(lab.HARNESS_PATH), "init-run"]
    assert "--benchmark-run-id" in command
    assert "20260616-candidate-ready-r1" in command
    assert "--model-name" in command
    assert "Ready Model" in command
    assert "--backend" in command
    assert "llama.cpp" in command


def test_import_report_and_dashboard_shell_out(tmp_path, monkeypatch) -> None:
    commands = capture_commands(monkeypatch)
    db_path = tmp_path / "dashboard.sqlite"
    out_path = tmp_path / "report.md"

    assert (
        lab.main(
            ["import", "--run", "run-1", "--eval-results", str(tmp_path), "--db", str(db_path)]
        )
        == 0
    )
    assert lab.main(["report", "--db", str(db_path), "--out", str(out_path)]) == 0
    assert lab.main(["dashboard", "--db", str(db_path), "--port", "9999", "--demo"]) == 0

    import_command, report_command, dashboard_command = commands
    assert import_command[:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "import-csv"]
    assert str(tmp_path / "run-1" / "dashboard-import" / "models.csv") in import_command
    assert report_command[:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "report"]
    assert str(out_path) in report_command
    assert dashboard_command[:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "serve"]
    assert "--port" in dashboard_command
    assert "9999" in dashboard_command
    assert "--demo" in dashboard_command


def test_unknown_subcommand_exits_nonzero(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        lab.main(["unknown"])

    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
