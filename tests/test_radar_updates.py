from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from local_ai_lab.cli import lab, radar_updates

FIELDS = (
    "candidate_id",
    "model_name",
    "benchmark_run_id",
    "model_page_url",
    "github_url",
)


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_evaluation_db(path: Path, benchmark_run_id: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE model_runs (
                id INTEGER PRIMARY KEY,
                model_id INTEGER NOT NULL,
                run_notes TEXT
            );
            CREATE TABLE eval_scores (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL,
                score_status TEXT NOT NULL
            );
            CREATE TABLE decisions (
                id INTEGER PRIMARY KEY,
                model_id INTEGER NOT NULL,
                created_at TEXT
            );
            """
        )
        conn.execute(
            "INSERT INTO model_runs (id, model_id, run_notes) VALUES (1, 10, ?)",
            (f"benchmark_run_id={benchmark_run_id} | fixture=yes",),
        )
        conn.execute(
            "INSERT INTO eval_scores (id, run_id, score_status) VALUES (1, 1, 'confirmed')"
        )


def test_check_updates_without_lookup_never_uses_network_or_writes_state(
    tmp_path, monkeypatch, capsys
) -> None:
    registry = tmp_path / "candidates.csv"
    state = tmp_path / "radar_upstream_state.json"
    write_registry(
        registry,
        [
            {
                "candidate_id": "hf-model",
                "model_name": "HF Model",
                "benchmark_run_id": "run-old",
                "model_page_url": "https://huggingface.co/example/hf-model",
                "github_url": "",
            }
        ],
    )

    def fail_fetch(*_args, **_kwargs):
        raise AssertionError("network must require the explicit --lookup flag")

    monkeypatch.setattr(radar_updates, "fetch_json", fail_fetch)
    exit_code = lab.main(
        [
            "radar",
            "check-updates",
            "--registry",
            str(registry),
            "--state",
            str(state),
        ]
    )

    assert exit_code == 0
    assert "Network lookup: disabled" in capsys.readouterr().out
    assert not state.exists()


def test_lookup_uses_fake_public_metadata_and_failures_are_nonfatal(
    tmp_path, monkeypatch, capsys
) -> None:
    registry = tmp_path / "candidates.csv"
    state = tmp_path / "radar_upstream_state.json"
    db_path = tmp_path / "dashboard.sqlite"
    write_registry(
        registry,
        [
            {
                "candidate_id": "hf-model",
                "model_name": "HF Model",
                "benchmark_run_id": "run-old",
                "model_page_url": "https://huggingface.co/example/hf-model",
                "github_url": "",
            },
            {
                "candidate_id": "github-model",
                "model_name": "GitHub Model",
                "benchmark_run_id": "run-old",
                "model_page_url": "",
                "github_url": "https://github.com/example/github-model",
            },
            {
                "candidate_id": "failed-model",
                "model_name": "Failed Model",
                "benchmark_run_id": "run-old",
                "model_page_url": "https://huggingface.co/example/failed-model",
                "github_url": "",
            },
        ],
    )
    write_evaluation_db(db_path, "run-old")
    revisions = {"hf": "hf-old", "github": "gh-old"}

    def fake_fetch(url: str, *, timeout: float = 10.0):
        assert timeout == 2.0
        if url.endswith("/example/hf-model"):
            return {"sha": revisions["hf"], "lastModified": "2026-07-01T00:00:00Z"}
        if url.endswith("/example/failed-model"):
            raise OSError("fixture metadata unavailable")
        if url.endswith("/repos/example/github-model"):
            return {"default_branch": "main", "pushed_at": "2026-07-01T00:00:00Z"}
        if url.endswith("/repos/example/github-model/commits/main"):
            return {"sha": revisions["github"]}
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(radar_updates, "fetch_json", fake_fetch)
    args = [
        "radar",
        "check-updates",
        "--lookup",
        "--registry",
        str(registry),
        "--state",
        str(state),
        "--db",
        str(db_path),
        "--timeout",
        "2",
    ]

    assert lab.main(args) == 0
    first_output = capsys.readouterr().out
    assert "Failures: 1" in first_output
    first = json.loads(state.read_text(encoding="utf-8"))
    assert first["candidates"]["hf-model"]["update_pending"] is False
    assert first["candidates"]["github-model"]["revision"] == "gh-old"
    assert "failed-model" not in first["candidates"]

    revisions.update(hf="hf-new", github="gh-new")
    assert lab.main(args) == 0
    second = json.loads(state.read_text(encoding="utf-8"))
    hf_state = second["candidates"]["hf-model"]
    github_state = second["candidates"]["github-model"]
    assert hf_state["update_pending"] is True
    assert hf_state["previous_revision"] == "hf-old"
    assert hf_state["revision"] == "hf-new"
    assert github_state["update_pending"] is True
    assert github_state["previous_revision"] == "gh-old"
    assert github_state["revision"] == "gh-new"


def test_check_after_new_evaluation_clears_pending_update(
    tmp_path, monkeypatch
) -> None:
    registry = tmp_path / "candidates.csv"
    state = tmp_path / "radar_upstream_state.json"
    db_path = tmp_path / "dashboard.sqlite"
    row = {
        "candidate_id": "hf-model",
        "model_name": "HF Model",
        "benchmark_run_id": "run-old",
        "model_page_url": "https://huggingface.co/example/hf-model",
        "github_url": "",
    }
    write_registry(registry, [row])
    write_evaluation_db(db_path, "run-old")
    revision = {"value": "old-sha"}

    def fake_fetch(_url: str, *, timeout: float = 10.0):
        return {"sha": revision["value"], "lastModified": "2026-07-01T00:00:00Z"}

    monkeypatch.setattr(radar_updates, "fetch_json", fake_fetch)
    args = [
        "radar",
        "check-updates",
        "--lookup",
        "--registry",
        str(registry),
        "--state",
        str(state),
        "--db",
        str(db_path),
    ]
    assert lab.main(args) == 0
    revision["value"] = "new-sha"
    assert lab.main(args) == 0
    assert json.loads(state.read_text(encoding="utf-8"))["candidates"]["hf-model"][
        "update_pending"
    ]

    row["benchmark_run_id"] = "run-new"
    write_registry(registry, [row])
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO model_runs (id, model_id, run_notes) VALUES (2, 10, ?)",
            ("benchmark_run_id=run-new | fixture=yes",),
        )
        conn.execute(
            "INSERT INTO eval_scores (id, run_id, score_status) VALUES (2, 2, 'confirmed')"
        )

    assert lab.main(args) == 0
    final = json.loads(state.read_text(encoding="utf-8"))["candidates"]["hf-model"]
    assert final["update_pending"] is False
    assert final["cleared_reason"] == "re_evaluated"
