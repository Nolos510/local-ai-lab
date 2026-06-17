from __future__ import annotations

import csv
import json
from pathlib import Path

from local_ai_lab.cli import lab
from local_ai_lab.cli.bench_matrix import (
    build_matrix,
    format_json,
    format_markdown,
    load_candidates,
)

FIELDNAMES = [
    "candidate_id",
    "model_name",
    "status",
    "local_runner",
    "local_model_id",
    "benchmark_run_id",
    "security_review_status",
    "download_approval",
    "proposed_eval",
]


def write_matrix_registry(path: Path) -> None:
    rows = [
        {
            "candidate_id": "ready-local",
            "model_name": "Ready Local",
            "status": "ready_for_eval",
            "local_runner": "lmstudio-cli",
            "local_model_id": "ready-local-id",
            "benchmark_run_id": "20260617-ready-local-r1",
            "security_review_status": "local_inventory_reviewed",
            "download_approval": "not_needed_local",
            "proposed_eval": "Run the local benchmark harness.",
        },
        {
            "candidate_id": "missing-id",
            "model_name": "Missing Runtime ID",
            "status": "ready_for_eval",
            "local_runner": "ollama",
            "security_review_status": "approved",
            "download_approval": "approved",
        },
        {
            "candidate_id": "blocked-security",
            "model_name": "Blocked Security",
            "status": "ready_for_eval",
            "local_runner": "llama.cpp",
            "local_model_id": "blocked-security-id",
            "security_review_status": "needs_review",
            "download_approval": "not_approved",
        },
        {
            "candidate_id": "watchlist",
            "model_name": "Watchlist Model",
            "status": "watchlist",
            "local_runner": "lmstudio-cli",
            "local_model_id": "watchlist-id",
            "security_review_status": "approved",
            "download_approval": "approved",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def test_matrix_defaults_to_ready_candidates_and_marks_blocked(tmp_path) -> None:
    registry = tmp_path / "candidates.csv"
    write_matrix_registry(registry)

    matrix = build_matrix(load_candidates(registry))

    assert [row["candidate_id"] for row in matrix] == [
        "ready-local",
        "missing-id",
        "blocked-security",
    ]
    assert matrix[0]["readiness"] == "ready"
    assert matrix[1]["readiness"] == "blocked"
    assert matrix[1]["blocked_reasons"] == ["missing local_model_id"]
    assert matrix[2]["blocked_reasons"] == [
        "security_review_status=needs_review",
        "download_approval=not_approved",
    ]


def test_markdown_matrix_is_deterministic(tmp_path) -> None:
    registry = tmp_path / "candidates.csv"
    write_matrix_registry(registry)

    markdown = format_markdown(build_matrix(load_candidates(registry), limit=2))

    assert markdown.startswith("# Benchmark Matrix")
    assert "| Candidate | Model | Runner | Local model id |" in markdown
    assert "| ready-local | Ready Local | lmstudio-cli | ready-local-id |" in markdown
    assert "| missing-id | Missing Runtime ID | ollama | - |" in markdown
    assert "missing local_model_id" in markdown
    assert "blocked-security" not in markdown


def test_json_matrix_is_deterministic_and_filterable(tmp_path) -> None:
    registry = tmp_path / "candidates.csv"
    write_matrix_registry(registry)

    matrix = build_matrix(load_candidates(registry), statuses=["all"], runner="lmstudio-cli")
    decoded = json.loads(format_json(matrix))

    assert [row["candidate_id"] for row in decoded] == ["ready-local", "watchlist"]
    assert list(decoded[0].keys()) == sorted(decoded[0].keys())
    assert decoded[0]["benchmark_run_id"] == "20260617-ready-local-r1"


def test_cli_bench_matrix_does_not_call_subprocess(tmp_path, monkeypatch, capsys) -> None:
    registry = tmp_path / "candidates.csv"
    write_matrix_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench matrix must not call subprocess")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)

    exit_code = lab.main(["bench", "matrix", "--registry", str(registry), "--json"])

    assert exit_code == 0
    decoded = json.loads(capsys.readouterr().out)
    assert [row["candidate_id"] for row in decoded] == [
        "ready-local",
        "missing-id",
        "blocked-security",
    ]
