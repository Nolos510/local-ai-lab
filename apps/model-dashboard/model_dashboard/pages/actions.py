"""Dashboard POST action helpers for local benchmark and artifact workflows."""

# ruff: noqa: E501,F403,F405,I001
from __future__ import annotations

import secrets
import sys
import threading
from pathlib import Path

from .. import csv_io, db
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
    elif runner == "ollama":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-ollama",
            "--run-dir",
            str(run_dir),
            "--model-id",
            row.get("local_model_id", ""),
            "--force",
        ]
        _append_arg(capture_command, "--endpoint", row.get("default_endpoint"))
    elif runner == "mlx-lm":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-mlx-lm",
            "--run-dir",
            str(run_dir),
            "--model-id",
            row.get("local_model_id", ""),
            "--force",
        ]
    elif runner == "llama-cpp":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-llama-cpp",
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


def _sync_pending_artifacts(database_path, eval_results_dir, source="automatic"):
    db.init_db(database_path, reset=False)
    with db.connect(database_path) as conn:
        pending_run_ids = _pending_artifact_run_ids(conn, eval_results_dir)
    result = {"source": source, "imported": [], "skipped": []}
    for run_id in pending_run_ids:
        if not _artifact_import_ready(run_id, eval_results_dir):
            result["skipped"].append(
                {
                    "benchmark_run_id": run_id,
                    "reason": "incomplete dashboard CSV set",
                }
            )
            continue
        try:
            imported = _import_artifact(run_id, database_path, eval_results_dir)
        except Exception:
            result["skipped"].append(
                {
                    "benchmark_run_id": run_id,
                    "reason": "invalid dashboard CSV set",
                }
            )
            continue
        result["imported"].append(imported)
    return result


def _startup_import_sync(database_path, eval_results_dir, *, enabled):
    if not enabled:
        return {"source": "automatic", "imported": [], "skipped": []}
    return _sync_pending_artifacts(database_path, eval_results_dir, source="automatic")


def _background_candidate_test(row, run_id, eval_results_dir, timeout, database_path):
    try:
        run_result = _run_candidate_test_for_row(row, run_id, eval_results_dir, timeout)
        export_result = _export_dashboard_import(run_id, eval_results_dir, timeout)
        sync_result = _sync_pending_artifacts(
            database_path,
            eval_results_dir,
            source="automatic",
        )
        failures = []
        if run_result["init"].returncode != 0:
            failures.append(f'init exited {run_result["init"].returncode}')
        elif run_result["capture"] is None:
            failures.append("capture did not run")
        elif run_result["capture"].returncode != 0:
            failures.append(f'capture exited {run_result["capture"].returncode}')
        if export_result.returncode != 0:
            failures.append(f"dashboard export exited {export_result.returncode}")
        skipped_import = next(
            (
                item
                for item in sync_result.get("skipped", [])
                if item.get("benchmark_run_id") == run_id
            ),
            None,
        )
        if skipped_import:
            failures.append(f'auto-import skipped: {skipped_import.get("reason") or "unknown reason"}')
        return {
            "candidate_id": row.get("candidate_id", ""),
            "model_name": row.get("model_name", ""),
            "model_id": row.get("local_model_id", ""),
            "runner": row.get("local_runner", ""),
            "run_id": run_id,
            "status": "failed" if failures else "passed",
            "reason": "; ".join(failures),
        }
    except Exception as exc:  # pragma: no cover - defensive worker guard
        _write_background_error(Path(eval_results_dir) / run_id, exc)
        return {
            "candidate_id": row.get("candidate_id", ""),
            "model_name": row.get("model_name", ""),
            "model_id": row.get("local_model_id", ""),
            "runner": row.get("local_runner", ""),
            "run_id": run_id,
            "status": "failed",
            "reason": f"{type(exc).__name__}: {exc}",
        }


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


def _new_run_all_status(batch_id, plan):
    return {
        "batch_id": batch_id,
        "state": "queued",
        "plan": [
            {
                key: item.get(key, "")
                for key in (
                    "candidate_id",
                    "model_name",
                    "model_id",
                    "runner",
                    "run_id",
                )
            }
            for item in plan
        ],
        "results": [],
    }


def _background_candidate_batch(plan, eval_results_dir, timeout, database_path, status):
    status["state"] = "running"
    try:
        for item in plan:
            try:
                result = _background_candidate_test(
                    item["candidate"],
                    item["run_id"],
                    eval_results_dir,
                    timeout,
                    database_path,
                )
            except Exception as exc:  # pragma: no cover - defensive batch guard
                result = {
                    "candidate_id": item.get("candidate_id", ""),
                    "model_name": item.get("model_name", ""),
                    "model_id": item.get("model_id", ""),
                    "runner": item.get("runner", ""),
                    "run_id": item.get("run_id", ""),
                    "status": "failed",
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            status["results"].append(result)
    finally:
        status["state"] = "complete"
    return status


def _start_candidate_batch(plan, eval_results_dir, timeout, database_path):
    if not plan:
        raise ValueError("No runnable models were confirmed.")
    batch_id = f"dashboard-batch-{secrets.token_urlsafe(9)}"
    status = _new_run_all_status(batch_id, plan)
    thread = threading.Thread(
        target=_background_candidate_batch,
        args=(plan, eval_results_dir, timeout, database_path, status),
        daemon=True,
        name=f"dashboard-run-all-{batch_id[-24:]}",
    )
    thread.start()
    return {
        "batch_id": batch_id,
        "status": status,
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


def _run_all_started_page(started):
    status = started["status"]
    batch_id = started["batch_id"]
    count = len(status.get("plan", []))
    body = """
    <section class="panel page-intro">
      <h2>Run All Started</h2>
      <p><strong>Approved batch:</strong> {count} models</p>
      <p><strong>Batch id:</strong> <code>{batch_id}</code></p>
      <p class="empty">One background worker is running the approved models sequentially. Each completed run refreshes dashboard CSVs and U1 auto-imports them; a failure does not stop the remaining models.</p>
      <p><a href="/inventory/run-all/status?batch_id={batch_id}">View / refresh batch summary</a></p>
    </section>
    """.format(
        count=count,
        batch_id=_text(batch_id),
    )
    return _layout("Run All Started", "/inventory", body)


def _run_all_status_page(status):
    results = {item.get("run_id"): item for item in status.get("results", [])}
    rows = []
    for item in status.get("plan", []):
        result = results.get(item.get("run_id"), {})
        state = result.get("status") or "queued"
        rows.append(
            [
                _text(item.get("model_name") or "—"),
                f'<code>{_text(item.get("model_id") or "—")}</code>',
                f'<code>{_text(item.get("runner") or "—")}</code>',
                f'<code>{_text(item.get("run_id") or "—")}</code>',
                _pill(state),
                _text(result.get("reason") or "—"),
            ]
        )
    passed = sum(item.get("status") == "passed" for item in status.get("results", []))
    failed = sum(item.get("status") == "failed" for item in status.get("results", []))
    remaining = max(len(status.get("plan", [])) - passed - failed, 0)
    body = """
    <section class="panel page-intro">
      <h2>Run All Summary</h2>
      <p><strong>Batch state:</strong> {state}</p>
      <p><strong>{passed} succeeded</strong> &middot; <strong>{failed} failed</strong> &middot; <strong>{remaining} remaining</strong></p>
      <p class="empty">Refresh this page to see later sequential runs. Completed run artifacts are auto-imported into run history when their dashboard CSVs are valid.</p>
      <p><a href="/inventory">Back to My Models</a></p>
    </section>
    <section class="inventory-section">
      {table}
    </section>
    """.format(
        state=_text(status.get("state") or "unknown"),
        passed=passed,
        failed=failed,
        remaining=remaining,
        table=_table(
            ["Model", "Exact model id", "Runner", "Run id", "Status", "Reason"],
            rows,
            empty_message="No run-all batch entries were recorded.",
        ),
    )
    return _layout("Run All Summary", "/inventory", body)


def _import_artifact(benchmark_run_id, database_path, eval_results_dir=None):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise ValueError(f"Artifact not found: {benchmark_run_id}")
    paths = _artifact_csv_paths(benchmark_run_id, eval_results_dir)
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise ValueError("Artifact is missing dashboard CSVs: {}".format(", ".join(missing)))
    run_rows = csv_io._read_import_rows("model_runs", paths["model_runs"])
    if benchmark_run_id not in {
        _benchmark_run_id_from_notes(row.get("run_notes")) for row in run_rows
    }:
        raise ValueError("Artifact model_runs.csv does not contain its benchmark run id.")
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

__all__ = ('_build_candidate_commands', '_candidate_test_plan', '_run_candidate_test_for_row', '_run_candidate_test', '_start_candidate_test', '_new_run_all_status', '_background_candidate_batch', '_start_candidate_batch', '_result_block', '_run_action_page', '_run_action_started_page', '_run_all_started_page', '_run_all_status_page', '_import_artifact', '_import_action_page', '_sync_pending_artifacts', '_startup_import_sync')
