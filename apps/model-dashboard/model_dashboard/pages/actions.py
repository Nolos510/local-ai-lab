"""Dashboard POST action helpers for local benchmark and artifact workflows."""

# ruff: noqa: E501,F403,F405,I001
from __future__ import annotations

import sys
import threading
from pathlib import Path

from .. import csv_io
from ..components import *
from ..layout import _layout

def _build_candidate_commands(row, run_id, eval_results_dir):
    run_dir = Path(eval_results_dir) / run_id
    init_command = [
        sys.executable,
        str(HARNESS_PATH),
        "init-run",
        "--benchmark-run-id",
        run_id,
        "--model-name",
        row.get("model_name", ""),
        "--backend",
        _candidate_runner_label(row),
        "--output-root",
        str(eval_results_dir),
        "--run-notes",
        "benchmark_run_id={} | candidate_id={} | dashboard_run_button=yes".format(
            run_id,
            row.get("candidate_id", ""),
        ),
    ]
    _append_arg(init_command, "--model-family", row.get("model_family"))
    _append_arg(init_command, "--provider", row.get("provider_or_org"))
    _append_arg(init_command, "--source-url", row.get("model_page_url"))
    _append_arg(init_command, "--format", row.get("format_or_runtime"))

    runner = row.get("local_runner", "")
    if runner == "lmstudio-cli":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-lmstudio-cli",
            "--run-dir",
            str(run_dir),
            "--model-id",
            row.get("local_model_id", ""),
            "--force",
        ]
    elif runner == "openai-compatible":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-local",
            "--run-dir",
            str(run_dir),
            "--endpoint",
            row.get("default_endpoint", ""),
            "--model",
            row.get("local_model_id") or row.get("model_name", ""),
            "--force",
        ]
    else:
        raise ValueError(f"Unsupported local runner: {runner}")
    return init_command, capture_command


def _candidate_test_plan(candidate_id, registry_path, eval_results_dir):
    candidates = _load_radar_candidates(registry_path)
    row = next((item for item in candidates if item.get("candidate_id") == candidate_id), None)
    if row is None:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if not _candidate_run_ready(row):
        raise ValueError("Candidate is missing exact local runner metadata.")
    run_id = _next_dashboard_run_id(row, eval_results_dir)
    return row, run_id


def _run_candidate_test_for_row(row, run_id, eval_results_dir, timeout):
    init_command, capture_command = _build_candidate_commands(row, run_id, eval_results_dir)
    init_result = _run_subprocess(init_command, timeout)
    if init_result.returncode != 0:
        return {
            "candidate": row,
            "run_id": run_id,
            "run_dir": str(Path(eval_results_dir) / run_id),
            "init": init_result,
            "capture": None,
        }
    capture_result = _run_subprocess(capture_command, timeout)
    return {
        "candidate": row,
        "run_id": run_id,
        "run_dir": str(Path(eval_results_dir) / run_id),
        "init": init_result,
        "capture": capture_result,
    }


def _run_candidate_test(candidate_id, registry_path, eval_results_dir, timeout):
    row, run_id = _candidate_test_plan(candidate_id, registry_path, eval_results_dir)
    return _run_candidate_test_for_row(row, run_id, eval_results_dir, timeout)


def _write_background_error(run_dir, exc):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    error_path = run_dir / "dashboard-run-error.txt"
    error_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")


def _export_dashboard_import(run_id, eval_results_dir, timeout):
    run_dir = Path(eval_results_dir) / run_id
    export_command = [
        sys.executable,
        str(HARNESS_PATH),
        "export-dashboard",
        "--run-dir",
        str(run_dir),
    ]
    return _run_subprocess(export_command, timeout)


def _import_dashboard_artifact(run_id, database_path, eval_results_dir):
    paths = _artifact_csv_paths(run_id, eval_results_dir)
    return csv_io.import_all(database_path, paths)


def _background_candidate_test(row, run_id, eval_results_dir, timeout, database_path):
    try:
        _run_candidate_test_for_row(row, run_id, eval_results_dir, timeout)
        _export_dashboard_import(run_id, eval_results_dir, timeout)
        _import_dashboard_artifact(run_id, database_path, eval_results_dir)
    except Exception as exc:  # pragma: no cover - defensive worker guard
        _write_background_error(Path(eval_results_dir) / run_id, exc)


def _start_candidate_test(candidate_id, registry_path, eval_results_dir, timeout, database_path):
    row, run_id = _candidate_test_plan(candidate_id, registry_path, eval_results_dir)
    run_dir = Path(eval_results_dir) / run_id
    thread = threading.Thread(
        target=_background_candidate_test,
        args=(row, run_id, eval_results_dir, timeout, database_path),
        daemon=True,
        name=f"dashboard-run-{run_id[:48]}",
    )
    thread.start()
    return {
        "candidate": row,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "thread_name": thread.name,
    }


def _result_block(label, result):
    if result is None:
        return f'<p class="empty">{_text(label)} did not run.</p>'
    status = "passed" if result.returncode == 0 else "failed"
    return """
    <div class="panel">
      <h2>{label} {status}</h2>
      <p>Exit code: <code>{code}</code></p>
      <pre class="command">{stdout}{stderr}</pre>
    </div>
    """.format(
        label=_text(label),
        status=_text(status),
        code=_text(result.returncode),
        stdout=_text(result.stdout or ""),
        stderr=_text(result.stderr or ""),
    )


def _run_action_page(result):
    candidate = result["candidate"]
    body = """
    <section class="panel">
      <h2>Run Test Result</h2>
      <p><strong>Candidate:</strong> {candidate}</p>
      <p><strong>Runner:</strong> {runner}</p>
      <p><strong>Artifact:</strong> {artifact}</p>
      <p class="empty">Raw responses are local artifact evidence. Scores and decisions still require human review.</p>
    </section>
    <section style="margin-top:16px">{init}</section>
    <section style="margin-top:16px">{capture}</section>
    """.format(
        candidate=_text(candidate.get("model_name")),
        runner=_text(_candidate_runner_label(candidate)),
        artifact=_artifact_link(result["run_id"]),
        init=_result_block("Init run", result["init"]),
        capture=_result_block("Capture prompts", result["capture"]),
    )
    return _layout("Run Test Result", "", body)


def _run_action_started_page(result):
    candidate = result["candidate"]
    artifact_path = _relative_path(result["run_dir"])
    body = """
    <section class="panel">
      <h2>Run Test Started</h2>
      <p><strong>Candidate:</strong> {candidate}</p>
      <p><strong>Runner:</strong> {runner}</p>
      <p><strong>Artifact:</strong> {artifact}</p>
      <p><strong>Local path:</strong> <code>{artifact_path}</code></p>
      <p class="empty">The local benchmark is running in the background. When capture finishes, dashboard-import CSVs are refreshed and imported automatically. Raw responses remain local artifact evidence; scores still require human review or a scored artifact export.</p>
    </section>
    """.format(
        candidate=_text(candidate.get("model_name")),
        runner=_text(_candidate_runner_label(candidate)),
        artifact=_artifact_link(result["run_id"]),
        artifact_path=_text(artifact_path),
    )
    return _layout("Run Test Started", "", body)


def _import_artifact(benchmark_run_id, database_path, eval_results_dir=None):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise ValueError(f"Artifact not found: {benchmark_run_id}")
    paths = _artifact_csv_paths(benchmark_run_id, eval_results_dir)
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise ValueError("Artifact is missing dashboard CSVs: {}".format(", ".join(missing)))
    counts = csv_io.import_all(database_path, paths)
    return {"benchmark_run_id": benchmark_run_id, "counts": counts}


def _import_action_page(result):
    body = """
    <section class="panel">
      <h2>Artifact Imported</h2>
      <p><strong>Benchmark run:</strong> {artifact}</p>
      <p><strong>Imported rows:</strong> <code>{counts}</code></p>
      <p><a href="/runs">Inspect imported runs</a></p>
    </section>
    """.format(
        artifact=_artifact_link(result["benchmark_run_id"]),
        counts=_text(result["counts"]),
    )
    return _layout("Artifact Imported", "", body)

__all__ = ('_build_candidate_commands', '_candidate_test_plan', '_run_candidate_test_for_row', '_run_candidate_test', '_start_candidate_test', '_result_block', '_run_action_page', '_run_action_started_page', '_import_artifact', '_import_action_page')
