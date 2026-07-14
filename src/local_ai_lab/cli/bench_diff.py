"""Read-only benchmark regression comparisons for the AI Lab OS CLI."""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

EM_DASH = "—"
METRICS = (
    ("tokens_per_sec", "tokens_per_sec"),
    ("total_latency_seconds", "total_latency_seconds"),
    ("ram_usage_gb", "ram_usage_gb"),
    ("confirmed total_score", "total_score"),
)


class BenchDiffError(RuntimeError):
    """Raised when a requested read-only benchmark comparison is unavailable."""


@dataclass(frozen=True)
class Delta:
    absolute: float | None
    percent: float | None


@dataclass(frozen=True)
class BenchmarkRun:
    benchmark_run_id: str
    dashboard_run_id: int
    model_id: int
    model_name: str
    tokens_per_sec: float | None
    total_latency_seconds: float | None
    ram_usage_gb: float | None
    total_score: float | None


def _finite_number(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def calculate_delta(before: object, after: object) -> Delta:
    """Return absolute and percent change from before to after without inventing values."""

    before_number = _finite_number(before)
    after_number = _finite_number(after)
    if before_number is None or after_number is None:
        return Delta(None, None)
    absolute = after_number - before_number
    percent = None if before_number == 0 else absolute / abs(before_number) * 100
    return Delta(absolute, percent)


def _benchmark_run_id_from_notes(notes: object) -> str:
    for part in str(notes or "").split("|"):
        key, separator, value = part.strip().partition("=")
        if separator and key == "benchmark_run_id":
            return value.strip()
    return ""


def load_run(db_path: Path, benchmark_run_id: str) -> BenchmarkRun:
    """Load one imported benchmark run through a SQLite read-only connection."""

    path = Path(db_path)
    if not path.is_file():
        raise BenchDiffError(f"Dashboard database does not exist: {path}")
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    r.id AS dashboard_run_id,
                    r.model_id,
                    r.run_notes,
                    r.tokens_per_sec,
                    r.total_latency_seconds,
                    r.ram_usage_gb,
                    m.model_name,
                    (
                        SELECT s.total_score
                        FROM eval_scores s
                        WHERE s.run_id = r.id AND s.score_status = 'confirmed'
                        ORDER BY s.id DESC
                        LIMIT 1
                    ) AS total_score
                FROM model_runs r
                JOIN models m ON m.id = r.model_id
                ORDER BY r.id
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise BenchDiffError(f"Could not inspect dashboard database: {path}") from exc

    matches = [
        row
        for row in rows
        if _benchmark_run_id_from_notes(row["run_notes"]) == benchmark_run_id
    ]
    if not matches:
        raise BenchDiffError(f"Run {benchmark_run_id} is not imported in {path}.")
    if len(matches) != 1:
        raise BenchDiffError(f"Run {benchmark_run_id} maps to multiple dashboard run rows.")
    row = matches[0]
    return BenchmarkRun(
        benchmark_run_id=benchmark_run_id,
        dashboard_run_id=int(row["dashboard_run_id"]),
        model_id=int(row["model_id"]),
        model_name=str(row["model_name"]),
        tokens_per_sec=_finite_number(row["tokens_per_sec"]),
        total_latency_seconds=_finite_number(row["total_latency_seconds"]),
        ram_usage_gb=_finite_number(row["ram_usage_gb"]),
        total_score=_finite_number(row["total_score"]),
    )


def _format_value(value: object) -> str:
    number = _finite_number(value)
    return EM_DASH if number is None else f"{number:.2f}"


def _format_change(value: float | None, *, percent: bool = False) -> str:
    if value is None:
        return EM_DASH
    suffix = "%" if percent else ""
    return f"{value:+.2f}{suffix}"


def format_diff(run_a: BenchmarkRun, run_b: BenchmarkRun) -> str:
    """Format a stable tab-separated comparison table."""

    lines = [
        "Benchmark diff",
        f"run_A: {run_a.benchmark_run_id} ({run_a.model_name})",
        f"run_B: {run_b.benchmark_run_id} ({run_b.model_name})",
        (
            f"metric\t{run_a.benchmark_run_id}\t{run_b.benchmark_run_id}"
            "\tabsolute_delta\tpercent_change"
        ),
    ]
    for label, field in METRICS:
        value_a = getattr(run_a, field)
        value_b = getattr(run_b, field)
        delta = calculate_delta(value_a, value_b)
        lines.append(
            "\t".join(
                (
                    label,
                    _format_value(value_a),
                    _format_value(value_b),
                    _format_change(delta.absolute),
                    _format_change(delta.percent, percent=True),
                )
            )
        )
    return "\n".join(lines) + "\n"

