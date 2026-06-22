"""Unified AI Lab OS command surface.

This CLI intentionally orchestrates existing local entry points instead of
cross-importing dashboard or benchmark internals. Commands that can execute
workflow actions shell out to the existing scripts; read-only status commands use
stdlib CSV/SQLite reads.
"""

from __future__ import annotations

import argparse
import csv
import re
import shlex
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

from local_ai_lab.cli.bench_matrix import (
    build_matrix,
    format_json,
    format_markdown,
    load_candidates,
)
from local_ai_lab.cli.hardware import collect_hardware_snapshot, format_snapshot, write_snapshot

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = REPO_ROOT / "data" / "model_registry" / "candidates.csv"
DEFAULT_EVAL_RESULTS = REPO_ROOT / "data" / "eval_results"
DEFAULT_DASHBOARD_DB = REPO_ROOT / "data" / "dashboard" / "model_dashboard.sqlite"
DEFAULT_REPORT = REPO_ROOT / "data" / "dashboard" / "reports" / "fixture-model-report.md"
HARNESS_PATH = REPO_ROOT / "evals" / "local-llm-benchmark" / "harness.py"
DASHBOARD_ENTRYPOINT = REPO_ROOT / "apps" / "model-dashboard" / "run_dashboard.py"
PROMPT_SET_ID = "ai-lab-local-llm-core-v0.1"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _read_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _candidate_by_id(path: Path, candidate_id: str) -> dict[str, str]:
    for row in _read_candidates(path):
        if row.get("candidate_id") == candidate_id:
            return row
    raise SystemExit(f"Unknown candidate: {candidate_id}")


def _safe_id(value: str, *, label: str) -> str:
    if not SAFE_ID_RE.fullmatch(value or ""):
        raise SystemExit(f"Invalid {label}: {value}")
    return value


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def _display_path(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _command_lines(command: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in command)


def _redact_endpoint(endpoint: str) -> str:
    return str(endpoint).split("?", 1)[0].split("#", 1)[0]


def _table_count(conn: sqlite3.Connection, table_name: str) -> int:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    if not exists:
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def _dashboard_counts(db_path: Path) -> dict[str, int]:
    if not db_path.exists():
        return {}
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        return {
            "models": _table_count(conn, "models"),
            "model_runs": _table_count(conn, "model_runs"),
            "eval_scores": _table_count(conn, "eval_scores"),
            "decisions": _table_count(conn, "decisions"),
        }


def _artifact_count(eval_results_dir: Path) -> int:
    if not eval_results_dir.exists():
        return 0
    return sum(1 for path in eval_results_dir.iterdir() if path.is_dir())


def command_status(args: argparse.Namespace) -> int:
    candidates = _read_candidates(args.registry)
    statuses: dict[str, int] = {}
    for row in candidates:
        status = row.get("status") or "unknown"
        statuses[status] = statuses.get(status, 0) + 1

    print("AI Lab OS status")
    print(f"Candidates: {len(candidates)}")
    for status in sorted(statuses):
        print(f"  {status}: {statuses[status]}")
    print(f"Benchmark artifacts: {_artifact_count(args.eval_results)}")

    counts = _dashboard_counts(args.db)
    if counts:
        print(f"Dashboard DB: {args.db}")
        row_summary = (
            "models={models}, runs={model_runs}, scores={eval_scores}, decisions={decisions}"
        ).format(**counts)
        print(f"Dashboard rows: {row_summary}")
    else:
        print(f"Dashboard DB: missing ({args.db})")
    return 0


def command_radar_list(args: argparse.Namespace) -> int:
    rows = _read_candidates(args.registry)
    if args.status:
        rows = [row for row in rows if row.get("status") == args.status]
    if args.limit:
        rows = rows[: args.limit]
    print("candidate_id\tstatus\tmodel_name\tlocal_runner")
    for row in rows:
        print(
            "{candidate_id}\t{status}\t{model_name}\t{local_runner}".format(
                candidate_id=row.get("candidate_id", ""),
                status=row.get("status", ""),
                model_name=row.get("model_name", ""),
                local_runner=row.get("local_runner", ""),
            )
        )
    return 0


def _default_run_id(candidate_id: str) -> str:
    safe_candidate = re.sub(r"[^A-Za-z0-9_.-]+", "-", candidate_id).strip(".-")
    return f"{date.today().isoformat().replace('-', '')}-{safe_candidate}-local"


def command_bench_run(args: argparse.Namespace) -> int:
    candidate = _candidate_by_id(args.registry, args.candidate)
    run_id = _safe_id(args.run_id or _default_run_id(args.candidate), label="benchmark run id")
    backend = (
        candidate.get("local_runner")
        or candidate.get("format_or_runtime")
        or candidate.get("runtime_availability")
        or "Local"
    )
    command = [
        sys.executable,
        str(HARNESS_PATH),
        "init-run",
        "--benchmark-run-id",
        run_id,
        "--model-name",
        candidate.get("model_name") or args.candidate,
        "--backend",
        backend,
        "--output-root",
        str(args.output_root),
    ]
    optional_fields = (
        ("model_family", "--model-family"),
        ("provider_or_org", "--provider"),
        ("model_page_url", "--source-url"),
        ("format_or_runtime", "--format"),
        ("why_interesting", "--model-notes"),
        ("proposed_eval", "--run-notes"),
    )
    for field_name, flag in optional_fields:
        value = candidate.get(field_name)
        if value:
            command.extend([flag, value])
    if args.force:
        command.append("--force")
    return _run(command)


def command_bench_matrix(args: argparse.Namespace) -> int:
    rows = load_candidates(args.registry)
    matrix = build_matrix(rows, statuses=args.status, runner=args.runner, limit=args.limit)
    if args.json:
        print(format_json(matrix))
    else:
        print(format_markdown(matrix))
    return 0


def _bench_execute_capture_shape(args: argparse.Namespace) -> str:
    if args.runner == "lmstudio-cli":
        return (
            f"lms chat <model-id> -p <prompt> --stats --ttl {args.ttl} "
            "--yes --dont-fetch-catalog"
        )
    endpoint = _redact_endpoint(args.endpoint) if args.endpoint else "<required-local-endpoint>"
    return f"POST {endpoint.rstrip('/')}/chat/completions model={args.model_id}"


def _bench_execute_preflight(
    args: argparse.Namespace,
    candidate: dict[str, str],
    run_dir: Path,
) -> str:
    import_dir = run_dir / "dashboard-import"
    lines = [
        "Benchmark execution preflight",
        f"candidate_id: {args.candidate}",
        f"candidate_model: {candidate.get('model_name') or args.candidate}",
        f"runner: {args.runner}",
        f"model_id: {args.model_id}",
        f"run_id: {args.run_id}",
        f"prompt_set_id: {PROMPT_SET_ID}",
        f"artifact_dir: {_display_path(run_dir)}",
        f"capture_shape: {_bench_execute_capture_shape(args)}",
        "dashboard_import_target: {}".format(
            _display_path(args.db) if args.import_dashboard else "not requested"
        ),
        f"dashboard_import_csvs: {_display_path(import_dir)}",
    ]
    return "\n".join(lines)


def _confirm_bench_execution(args: argparse.Namespace, preflight: str) -> bool:
    print(preflight)
    if args.i_approve_local_run:
        print("approval: explicit --i-approve-local-run")
        return True
    if sys.stdin.isatty():
        answer = input("Type yes to approve this local benchmark run: ")
        if answer.strip() == "yes":
            print("approval: interactive yes")
            return True
    print(
        "approval: missing; refusing before any harness, subprocess, endpoint, "
        "import, or score export.",
        file=sys.stderr,
    )
    return False


def _bench_execute_init_command(
    args: argparse.Namespace,
    candidate: dict[str, str],
) -> list[str]:
    command = [
        sys.executable,
        str(HARNESS_PATH),
        "init-run",
        "--benchmark-run-id",
        args.run_id,
        "--model-name",
        candidate.get("model_name") or args.model_id,
        "--backend",
        args.runner,
        "--output-root",
        str(args.output_root),
        "--run-notes",
        f"benchmark_run_id={args.run_id} | candidate_id={args.candidate} | ai_lab_execute=yes",
    ]
    optional_fields = (
        ("model_family", "--model-family"),
        ("provider_or_org", "--provider"),
        ("model_page_url", "--source-url"),
        ("format_or_runtime", "--format"),
        ("why_interesting", "--model-notes"),
    )
    for field_name, flag in optional_fields:
        value = candidate.get(field_name)
        if value:
            command.extend([flag, value])
    if args.force:
        command.append("--force")
    return command


def _bench_execute_capture_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
    if args.runner == "lmstudio-cli":
        command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-lmstudio-cli",
            "--run-dir",
            str(run_dir),
            "--model-id",
            args.model_id,
            "--timeout",
            str(args.timeout),
            "--ttl",
            str(args.ttl),
        ]
        if args.lms_path:
            command.extend(["--lms-path", args.lms_path])
    elif args.runner == "openai-compatible":
        if not args.endpoint:
            raise SystemExit("--endpoint is required for --runner openai-compatible")
        command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-local",
            "--run-dir",
            str(run_dir),
            "--endpoint",
            args.endpoint,
            "--model",
            args.model_id,
            "--timeout",
            str(args.timeout),
        ]
        if args.max_tokens is not None:
            command.extend(["--max-tokens", str(args.max_tokens)])
    else:
        raise SystemExit(f"Unsupported runner: {args.runner}")
    if args.force:
        command.append("--force")
    return command


def _bench_execute_export_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(HARNESS_PATH),
        "export-dashboard",
        "--run-dir",
        str(run_dir),
    ]
    if args.scores_json:
        command.extend(["--scores-json", str(args.scores_json)])
    if args.decision_json:
        command.extend(["--decision-json", str(args.decision_json)])
    return command


def _bench_execute_import_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
    import_dir = run_dir / "dashboard-import"
    return [
        sys.executable,
        str(DASHBOARD_ENTRYPOINT),
        "import-csv",
        "--db",
        str(args.db),
        "--models",
        str(import_dir / "models.csv"),
        "--runs",
        str(import_dir / "model_runs.csv"),
        "--scores",
        str(import_dir / "eval_scores.csv"),
        "--decisions",
        str(import_dir / "decisions.csv"),
    ]


def command_bench_execute(args: argparse.Namespace) -> int:
    candidate = _candidate_by_id(args.registry, args.candidate)
    args.run_id = _safe_id(args.run_id, label="benchmark run id")
    run_dir = args.output_root / args.run_id
    preflight = _bench_execute_preflight(args, candidate, run_dir)
    if not _confirm_bench_execution(args, preflight):
        return 2

    commands = [
        _bench_execute_init_command(args, candidate),
        _bench_execute_capture_command(args, run_dir),
        _bench_execute_export_command(args, run_dir),
    ]
    if args.import_dashboard:
        commands.append(_bench_execute_import_command(args, run_dir))

    for command in commands:
        print(f"$ {_command_lines(command)}")
        exit_code = _run(command)
        if exit_code != 0:
            return exit_code
    return 0


def command_import(args: argparse.Namespace) -> int:
    run_id = _safe_id(args.run, label="benchmark run id")
    import_dir = args.eval_results / run_id / "dashboard-import"
    command = [
        sys.executable,
        str(DASHBOARD_ENTRYPOINT),
        "import-csv",
        "--db",
        str(args.db),
        "--models",
        str(import_dir / "models.csv"),
        "--runs",
        str(import_dir / "model_runs.csv"),
        "--scores",
        str(import_dir / "eval_scores.csv"),
        "--decisions",
        str(import_dir / "decisions.csv"),
    ]
    return _run(command)


def command_report(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        str(DASHBOARD_ENTRYPOINT),
        "report",
        "--db",
        str(args.db),
        "--out",
        str(args.out),
    ]
    if args.include_demo:
        command.append("--include-demo")
    return _run(command)


def command_dashboard(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        str(DASHBOARD_ENTRYPOINT),
        "serve",
        "--db",
        str(args.db),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.demo:
        command.append("--demo")
    if args.enable_import_actions:
        command.append("--enable-import-actions")
    if args.enable_run_tests:
        command.append("--enable-run-tests")
    if args.enable_delete_actions:
        command.append("--enable-delete-actions")
    return _run(command)


def command_hardware_snapshot(args: argparse.Namespace) -> int:
    snapshot = collect_hardware_snapshot()
    output = format_snapshot(snapshot)
    print(output, end="")
    if args.out:
        try:
            path = write_snapshot(args.out, snapshot, repo_root=REPO_ROOT)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"Wrote hardware snapshot: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the local-first AI Lab OS loop.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show local lab loop status.")
    status_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    status_parser.add_argument("--eval-results", type=Path, default=DEFAULT_EVAL_RESULTS)
    status_parser.add_argument("--db", type=Path, default=DEFAULT_DASHBOARD_DB)
    status_parser.set_defaults(func=command_status)

    radar_parser = subparsers.add_parser("radar", help="Inspect radar candidate records.")
    radar_subparsers = radar_parser.add_subparsers(dest="radar_command", required=True)
    radar_list = radar_subparsers.add_parser("list", help="List model candidates.")
    radar_list.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    radar_list.add_argument("--status")
    radar_list.add_argument("--limit", type=int, default=0)
    radar_list.set_defaults(func=command_radar_list)

    hardware_parser = subparsers.add_parser("hardware", help="Inspect local hardware context.")
    hardware_subparsers = hardware_parser.add_subparsers(
        dest="hardware_command",
        required=True,
    )
    hardware_snapshot = hardware_subparsers.add_parser(
        "snapshot",
        help="Print a sanitized local hardware/runtime snapshot as JSON.",
    )
    hardware_snapshot.add_argument(
        "--out",
        type=Path,
        help="Write the same JSON to a repo-local path.",
    )
    hardware_snapshot.set_defaults(func=command_hardware_snapshot)

    bench_parser = subparsers.add_parser("bench", help="Prepare local benchmark artifacts.")
    bench_subparsers = bench_parser.add_subparsers(dest="bench_command", required=True)
    bench_run = bench_subparsers.add_parser(
        "run",
        help="Initialize a benchmark run artifact for a candidate; does not call a model.",
    )
    bench_run.add_argument("--candidate", required=True)
    bench_run.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    bench_run.add_argument("--run-id")
    bench_run.add_argument("--output-root", type=Path, default=DEFAULT_EVAL_RESULTS)
    bench_run.add_argument("--force", action="store_true")
    bench_run.set_defaults(func=command_bench_run)
    bench_matrix = bench_subparsers.add_parser(
        "matrix",
        help="Show a read-only benchmark planning matrix; does not call models.",
    )
    bench_matrix.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    bench_matrix.add_argument(
        "--status",
        action="append",
        help="Candidate status to include. Defaults to ready_for_eval; use all for every status.",
    )
    bench_matrix.add_argument("--runner", help="Only include candidates with this local_runner.")
    bench_matrix.add_argument("--limit", type=int, default=0)
    bench_matrix.add_argument("--json", action="store_true")
    bench_matrix.set_defaults(func=command_bench_matrix)
    bench_execute = bench_subparsers.add_parser(
        "execute",
        help="Run an explicitly approved local benchmark capture flow.",
    )
    bench_execute.add_argument("--candidate", required=True)
    bench_execute.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    bench_execute.add_argument("--model-id", required=True)
    bench_execute.add_argument(
        "--runner",
        required=True,
        choices=("lmstudio-cli", "openai-compatible"),
    )
    bench_execute.add_argument("--run-id", required=True)
    bench_execute.add_argument("--output-root", type=Path, default=DEFAULT_EVAL_RESULTS)
    bench_execute.add_argument("--db", type=Path, default=DEFAULT_DASHBOARD_DB)
    bench_execute.add_argument("--endpoint")
    bench_execute.add_argument("--lms-path")
    bench_execute.add_argument("--timeout", type=float, default=180.0)
    bench_execute.add_argument("--ttl", type=int, default=3600)
    bench_execute.add_argument("--max-tokens", type=int)
    bench_execute.add_argument("--scores-json", type=Path)
    bench_execute.add_argument("--decision-json", type=Path)
    bench_execute.add_argument("--import-dashboard", action="store_true")
    bench_execute.add_argument("--force", action="store_true")
    bench_execute.add_argument("--i-approve-local-run", action="store_true")
    bench_execute.set_defaults(func=command_bench_execute)

    import_parser = subparsers.add_parser("import", help="Import benchmark CSVs.")
    import_parser.add_argument("--run", required=True)
    import_parser.add_argument("--eval-results", type=Path, default=DEFAULT_EVAL_RESULTS)
    import_parser.add_argument("--db", type=Path, default=DEFAULT_DASHBOARD_DB)
    import_parser.set_defaults(func=command_import)

    report_parser = subparsers.add_parser("report", help="Generate a dashboard report.")
    report_parser.add_argument("--db", type=Path, default=DEFAULT_DASHBOARD_DB)
    report_parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    report_parser.add_argument("--include-demo", action="store_true")
    report_parser.set_defaults(func=command_report)

    dashboard_parser = subparsers.add_parser("dashboard", help="Launch the local dashboard.")
    dashboard_parser.add_argument("--db", type=Path, default=DEFAULT_DASHBOARD_DB)
    dashboard_parser.add_argument("--host", default="127.0.0.1")
    dashboard_parser.add_argument("--port", type=int, default=8765)
    dashboard_parser.add_argument("--demo", action="store_true")
    dashboard_parser.add_argument("--enable-import-actions", action="store_true")
    dashboard_parser.add_argument("--enable-run-tests", action="store_true")
    dashboard_parser.add_argument("--enable-delete-actions", action="store_true")
    dashboard_parser.set_defaults(func=command_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
