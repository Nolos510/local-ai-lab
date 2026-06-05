#!/usr/bin/env python3
"""Command line entrypoint for the Local Model Performance Dashboard."""

import argparse
import sys
from pathlib import Path

from model_dashboard import csv_io, db, reports, server

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
DEFAULT_DB = REPO_ROOT / "data" / "dashboard" / "model_dashboard.sqlite"
FIXTURE_DIR = APP_DIR / "fixtures"


def _csv_paths_from_args(args):
    return {
        "models": args.models,
        "model_runs": args.runs,
        "eval_scores": args.scores,
        "decisions": args.decisions,
    }


def command_init_db(args):
    db.init_db(args.db, reset=args.reset)
    if args.with_fixtures:
        counts = csv_io.import_fixture_set(args.db, FIXTURE_DIR)
        print("Imported fixtures: {}".format(counts))
    print("Database ready: {}".format(args.db))
    return 0


def command_import_csv(args):
    counts = csv_io.import_all(args.db, _csv_paths_from_args(args))
    print("Imported rows: {}".format(counts))
    return 0


def command_export_csv(args):
    output_paths = csv_io.export_all(args.db, args.out)
    for table_name, path in output_paths.items():
        print("{}: {}".format(table_name, path))
    return 0


def command_report(args):
    path = reports.write_report(args.db, args.out, include_demo=args.include_demo)
    print("Report written: {}".format(path))
    return 0


def command_serve(args):
    if args.demo and not db.database_has_data(args.db):
        db.init_db(args.db, reset=False)
        csv_io.import_fixture_set(args.db, FIXTURE_DIR)
    server.serve(
        args.db,
        host=args.host,
        port=args.port,
        enable_run_tests=args.enable_run_tests,
        run_test_timeout=args.run_test_timeout,
        inventory_timeout=args.inventory_timeout,
    )
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Local-first model performance dashboard for AI Lab OS."
    )
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init-db", help="Create the SQLite database.")
    init_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    init_parser.add_argument("--reset", action="store_true")
    init_parser.add_argument("--with-fixtures", action="store_true")
    init_parser.set_defaults(func=command_init_db)

    serve_parser = subparsers.add_parser("serve", help="Run the local dashboard server.")
    serve_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    serve_parser.add_argument("--demo", action="store_true")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument(
        "--enable-run-tests",
        action="store_true",
        help="Enable local run-test buttons for candidates with exact runner metadata.",
    )
    serve_parser.add_argument(
        "--run-test-timeout",
        type=int,
        default=3600,
        help="Maximum seconds allowed for each dashboard-triggered harness command.",
    )
    serve_parser.add_argument(
        "--inventory-timeout",
        type=int,
        default=5,
        help="Maximum seconds allowed for each local inventory command.",
    )
    serve_parser.set_defaults(func=command_serve)

    import_parser = subparsers.add_parser("import-csv", help="Import table-shaped CSV files.")
    import_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    import_parser.add_argument("--models", type=Path)
    import_parser.add_argument("--runs", type=Path)
    import_parser.add_argument("--scores", type=Path)
    import_parser.add_argument("--decisions", type=Path)
    import_parser.set_defaults(func=command_import_csv)

    export_parser = subparsers.add_parser("export-csv", help="Export dashboard tables to CSV.")
    export_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    export_parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "dashboard" / "exports")
    export_parser.set_defaults(func=command_export_csv)

    report_parser = subparsers.add_parser("report", help="Generate a Markdown report.")
    report_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    report_parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "data" / "dashboard" / "reports" / "fixture-model-report.md",
    )
    report_parser.add_argument(
        "--include-demo",
        action="store_true",
        help="Include bundled fixture rows in the generated report.",
    )
    report_parser.set_defaults(func=command_report)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.func is None:
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
