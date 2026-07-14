from __future__ import annotations

import sqlite3

from local_ai_lab.cli import bench_diff, lab


def _write_diff_fixture(path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE models (
                id INTEGER PRIMARY KEY,
                model_name TEXT NOT NULL
            );
            CREATE TABLE model_runs (
                id INTEGER PRIMARY KEY,
                model_id INTEGER NOT NULL REFERENCES models(id),
                tokens_per_sec REAL,
                total_latency_seconds REAL,
                ram_usage_gb REAL,
                run_notes TEXT
            );
            CREATE TABLE eval_scores (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES model_runs(id),
                total_score REAL NOT NULL,
                score_status TEXT NOT NULL
            );
            INSERT INTO models (id, model_name) VALUES (1, 'Model A');
            INSERT INTO models (id, model_name) VALUES (2, 'Model B');
            INSERT INTO model_runs (
                id, model_id, tokens_per_sec, total_latency_seconds, ram_usage_gb, run_notes
            ) VALUES (
                10, 1, 20, 120, 40, 'benchmark_run_id=run-a | fixture=yes'
            );
            INSERT INTO model_runs (
                id, model_id, tokens_per_sec, total_latency_seconds, ram_usage_gb, run_notes
            ) VALUES (
                20, 2, 25, 90, NULL, 'benchmark_run_id=run-b | fixture=yes'
            );
            INSERT INTO eval_scores (id, run_id, total_score, score_status)
            VALUES (100, 10, 80, 'confirmed');
            INSERT INTO eval_scores (id, run_id, total_score, score_status)
            VALUES (200, 20, 95, 'draft');
            """
        )


def test_delta_math_handles_changes_missing_values_and_zero_baseline() -> None:
    increase = bench_diff.calculate_delta(20, 25)
    decrease = bench_diff.calculate_delta(120, 90)
    missing = bench_diff.calculate_delta(None, 10)
    zero_baseline = bench_diff.calculate_delta(0, 5)

    assert increase.absolute == 5
    assert increase.percent == 25
    assert decrease.absolute == -30
    assert decrease.percent == -25
    assert missing.absolute is None
    assert missing.percent is None
    assert zero_baseline.absolute == 5
    assert zero_baseline.percent is None


def test_bench_diff_is_read_only_warns_for_different_models_and_uses_em_dash(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    db_path = tmp_path / "dashboard.sqlite"
    _write_diff_fixture(db_path)
    before = db_path.read_bytes()

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench diff must not call a model runner or subprocess")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)

    exit_code = lab.main(
        [
            "bench",
            "diff",
            "--run",
            "run-a",
            "--run",
            "run-b",
            "--db",
            str(db_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "warning: runs use different models: Model A vs Model B" in captured.err
    assert "metric\trun-a\trun-b\tabsolute_delta\tpercent_change" in captured.out
    assert "tokens_per_sec\t20.00\t25.00\t+5.00\t+25.00%" in captured.out
    assert "total_latency_seconds\t120.00\t90.00\t-30.00\t-25.00%" in captured.out
    assert "ram_usage_gb\t40.00\t—\t—\t—" in captured.out
    assert "confirmed total_score\t80.00\t—\t—\t—" in captured.out
    assert db_path.read_bytes() == before

