"""Dashboard POST action helpers for local benchmark and artifact workflows."""

# ruff: noqa: E501,F403,F405,I001
from __future__ import annotations

import http.client
import json
import os
import secrets
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse

from .. import csv_io, db, model_roles, score_review
from ..components import *
from ..layout import _layout
from ..run_config import (
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    infer_quantization,
)

def _build_candidate_commands(row, run_id, eval_results_dir):
    run_dir = Path(eval_results_dir) / run_id
    quantization, quantization_source = infer_quantization(
        row.get("model_name"),
        row.get("format_or_runtime"),
        row.get("runtime_availability"),
        row.get("local_model_id"),
        row.get("model_page_url"),
        row.get("lm_studio_url"),
        row.get("ollama_url"),
    )
    run_notes = (
        "benchmark_run_id={} | candidate_id={} | dashboard_run_button=yes | "
        "context_window_source=inferred:benchmark_default | "
        "temperature_source=inferred:benchmark_default | "
        "top_p_source=inferred:benchmark_default"
    ).format(run_id, row.get("candidate_id", ""))
    if quantization_source:
        run_notes = f"{run_notes} | quantization_source={quantization_source}"
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
        "--context-window",
        str(DEFAULT_CONTEXT_WINDOW),
        "--temperature",
        str(DEFAULT_TEMPERATURE),
        "--top-p",
        str(DEFAULT_TOP_P),
        "--run-notes",
        run_notes,
    ]
    _append_arg(init_command, "--model-family", row.get("model_family"))
    _append_arg(init_command, "--provider", row.get("provider_or_org"))
    _append_arg(init_command, "--source-url", row.get("model_page_url"))
    _append_arg(init_command, "--format", row.get("format_or_runtime"))
    _append_arg(init_command, "--quantization", quantization)

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
            "--manage-model-lifecycle",
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


def _candidate_test_plan(
    candidate_id,
    registry_path,
    eval_results_dir,
    database_path=None,
    *,
    clock=None,
):
    candidates = _load_radar_candidates(registry_path)
    row = next((item for item in candidates if item.get("candidate_id") == candidate_id), None)
    if row is None:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if not _candidate_run_ready(row):
        raise ValueError("Candidate is missing exact local runner metadata.")
    existing_ids = _existing_benchmark_run_ids(database_path, eval_results_dir)
    run_id = _next_dashboard_run_id(
        row,
        eval_results_dir,
        existing_ids=existing_ids,
        clock=clock,
    )
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


def _run_candidate_test(
    candidate_id,
    registry_path,
    eval_results_dir,
    timeout,
    database_path=None,
    *,
    clock=None,
):
    row, run_id = _candidate_test_plan(
        candidate_id,
        registry_path,
        eval_results_dir,
        database_path,
        clock=clock,
    )
    return _run_candidate_test_for_row(row, run_id, eval_results_dir, timeout)


def _write_background_error(run_dir, exc):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    error_path = run_dir / "dashboard-run-error.txt"
    error_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")


def _export_dashboard_import(run_id, eval_results_dir, timeout, scores_path=None):
    run_dir = Path(eval_results_dir) / run_id
    export_command = [
        sys.executable,
        str(HARNESS_PATH),
        "export-dashboard",
        "--run-dir",
        str(run_dir),
    ]
    _append_arg(export_command, "--scores-json", scores_path)
    return _run_subprocess(export_command, timeout)


def _suggest_draft_scores(
    run_id,
    eval_results_dir,
    timeout,
    judge_endpoint,
    judge_model=None,
    output_path=None,
):
    run_dir = Path(eval_results_dir) / run_id
    draft_path = Path(output_path) if output_path is not None else run_dir / "draft-scores.json"
    score_command = [
        sys.executable,
        str(HARNESS_PATH),
        "suggest-scores",
        "--run-dir",
        str(run_dir),
        "--endpoint",
        judge_endpoint,
        "--out",
        str(draft_path),
        "--reasoning-effort",
        "none",
        "--max-tokens",
        "4096",
        "--force",
    ]
    _append_arg(score_command, "--judge-model", judge_model)
    result = _run_subprocess(score_command, timeout)
    return result, draft_path


def _judge_model_ids(judge_endpoint, timeout):
    parsed = urlparse(str(judge_endpoint or ""))
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Local judge endpoint must be an HTTP(S) URL with a host.")
    if not _is_loopback_host(parsed.hostname):
        raise ValueError("Local judge endpoint must use localhost or a loopback IP.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Local judge endpoint must not include credentials, query, or fragment.")
    connection_class = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = f"{parsed.path.rstrip('/')}/models" or "/models"
    connection = connection_class(parsed.hostname, port=port, timeout=timeout)
    try:
        headers = {}
        api_token = os.environ.get("LM_API_TOKEN", "").strip()
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(
            "Local judge endpoint is not reachable; start the local model server before scoring."
        ) from exc
    finally:
        connection.close()
    if response.status == 401:
        raise ValueError(
            "Local judge model inventory requires authentication; export LM_API_TOKEN "
            "before starting the dashboard or disable LM Studio API authentication for "
            "this loopback-only server."
        )
    if response.status != 200:
        raise ValueError(f"Local judge model inventory returned HTTP {response.status}.")
    try:
        payload = json.loads(response_body)
    except ValueError as exc:
        raise ValueError("Local judge model inventory returned invalid JSON.") from exc
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Local judge model inventory returned an unexpected payload.")
    return {
        str(row.get("id") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def _judge_preflight(judge_endpoint, judge_model, timeout):
    model = str(judge_model or "").strip()
    if not model:
        raise ValueError(
            "A judge model is required when score actions are enabled; restart with "
            "`--judge-model <exact-local-model-id>`."
        )
    model_ids = _judge_model_ids(judge_endpoint, timeout)
    if model not in model_ids:
        raise ValueError(
            f"Configured judge model '{model}' is not available from the local judge endpoint."
        )
    return {"model": model, "available_models": len(model_ids)}


def _reviewer_preflight(
    reviewer_endpoint,
    reviewer_model,
    primary_endpoint,
    primary_model,
    timeout,
):
    model = str(reviewer_model or "").strip()
    if not model:
        raise ValueError(
            "A reviewer model is required; restart with "
            "`--reviewer-model <different-local-model-id>`."
        )
    if model == str(primary_model or "").strip():
        raise ValueError("Independent review requires a different model from the primary judge.")
    result = _judge_preflight(reviewer_endpoint, model, timeout)
    result["independent_from"] = str(primary_model or "")
    result["same_endpoint"] = str(reviewer_endpoint).rstrip("/") == str(primary_endpoint).rstrip(
        "/"
    )
    return result


def _unscored_artifact_ids(eval_results_dir, database_path=None):
    imported_score_status = {}
    if database_path is not None:
        db.init_db(database_path, reset=False)
        with db.connect(database_path) as conn:
            imported_score_status = {
                run_id: row["score_status"]
                for run_id, row in _dashboard_runs_by_benchmark_id(conn).items()
            }
    run_ids = []
    for artifact in _artifact_summaries(eval_results_dir):
        run_id = artifact["benchmark_run_id"]
        if artifact["raw_responses"] <= 0:
            continue
        if not model_roles.model_supports_generation(artifact.get("model_role")):
            continue
        if artifact["scores"] == "yes":
            continue
        if database_path is None and artifact["draft_scores"] == "yes":
            continue
        if imported_score_status.get(run_id) in ("draft", "confirmed"):
            continue
        review = score_review.review_state(Path(eval_results_dir) / run_id)
        if review.get("status") == "rejected" and not (
            review.get("human_action") == "automatic_invalid_evidence"
            and review.get("recommended_action") in ("rescore", "rerun_review")
        ):
            continue
        run_ids.append(run_id)
    return sorted(run_ids)


def _import_dashboard_artifact(run_id, database_path, eval_results_dir):
    paths = _artifact_csv_paths(run_id, eval_results_dir)
    return csv_io.import_all(database_path, paths)


def _sync_pending_artifacts(database_path, eval_results_dir, source="automatic"):
    db.init_db(database_path, reset=False)
    with db.connect(database_path) as conn:
        pending_run_ids = _pending_artifact_run_ids(conn, eval_results_dir)
    result = {"source": source, "imported": [], "skipped": []}
    for run_id in pending_run_ids:
        if score_review.review_state(Path(eval_results_dir) / run_id).get(
            "status"
        ) == "rejected":
            result["skipped"].append(
                {
                    "benchmark_run_id": run_id,
                    "reason": "rejected evidence preserved outside active rankings",
                }
            )
            continue
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


def _archive_score_attempt(artifact_dir, names):
    artifact_dir = Path(artifact_dir)
    existing = [artifact_dir / name for name in names if (artifact_dir / name).is_file()]
    if not existing:
        return ""
    archive_root = artifact_dir / "score-attempts"
    archive_root.mkdir(parents=True, exist_ok=True)
    index = 1
    while (archive_root / f"attempt-{index:02d}").exists():
        index += 1
    attempt_dir = archive_root / f"attempt-{index:02d}"
    attempt_dir.mkdir()
    for path in existing:
        path.replace(attempt_dir / path.name)
    return f"score-attempts/{attempt_dir.name}"


def _remove_imported_draft_score(benchmark_run_id, database_path):
    if database_path is None:
        return False
    db.init_db(database_path, reset=False)
    with db.connect(database_path) as conn:
        run = _dashboard_runs_by_benchmark_id(conn).get(benchmark_run_id)
        if not run or run["score_status"] != "draft" or run["score_id"] is None:
            return False
        conn.execute(
            "DELETE FROM eval_scores WHERE id = ? AND score_status = 'draft'",
            (run["score_id"],),
        )
        conn.commit()
    return True


def _auto_reject_invalid_artifact(
    benchmark_run_id,
    database_path,
    eval_results_dir,
    disposition=None,
):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    disposition = disposition or score_review.automatic_disposition(artifact_dir)
    if not disposition:
        return None
    prior = score_review.load_json_object(artifact_dir / "score-review.json")
    already_current = (
        prior.get("status") == "rejected"
        and prior.get("human_action") == "automatic_invalid_evidence"
        and prior.get("recommended_action") == disposition["recommended_action"]
        and prior.get("reason") == disposition["reason"]
    )
    if not already_current and not (
        prior.get("status") == "rejected"
        and prior.get("human_action") == "rejected"
    ):
        record = dict(prior)
        record.update(
            {
                "status": "rejected",
                "human_action": "automatic_invalid_evidence",
                "recommended_action": disposition["recommended_action"],
                "reason": disposition["reason"],
                "flags": sorted(
                    set(prior.get("flags") or ())
                    | set(disposition.get("flags") or ())
                    | {"automatic_invalid_evidence"}
                ),
            }
        )
        if disposition.get("capture_evidence"):
            record["capture_evidence"] = disposition["capture_evidence"]
        score_review.write_review_record(artifact_dir, record)
    removed = _remove_imported_draft_score(benchmark_run_id, database_path)
    return {
        "benchmark_run_id": benchmark_run_id,
        "status": "rejected",
        "reason": disposition["reason"],
        "recommended_action": disposition["recommended_action"],
        "removed_imported_draft": removed,
    }


def _auto_reject_invalid_artifacts(database_path, eval_results_dir, *, enabled=True):
    result = {"rejected": [], "skipped": []}
    if not enabled:
        return result
    root = Path(eval_results_dir)
    if not root.is_dir():
        return result
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if (path / "scores.json").is_file():
            continue
        prior = score_review.load_json_object(path / "score-review.json")
        if prior.get("status") == "rejected" and prior.get("human_action") == "rejected":
            continue
        disposition = score_review.automatic_disposition(path)
        if not disposition:
            continue
        try:
            rejected = _auto_reject_invalid_artifact(
                path.name,
                database_path,
                root,
                disposition,
            )
        except Exception:
            result["skipped"].append(
                {
                    "benchmark_run_id": path.name,
                    "reason": "automatic evidence triage did not complete",
                }
            )
            continue
        result["rejected"].append(rejected)
    return result


def _lifecycle_summary(run_dir):
    path = Path(run_dir) / "lms-lifecycle.log"
    try:
        values = {
            key.strip(): value.strip()
            for key, value in (
                line.split("=", 1)
                for line in path.read_text(encoding="utf-8").splitlines()
                if "=" in line
            )
        }
    except (OSError, UnicodeError, ValueError):
        return "not managed"
    if values.get("loaded_by_harness") == "yes" and values.get("unloaded_after_run") == "yes":
        return "loaded · captured · unloaded"
    if values.get("already_loaded") == "yes":
        return "already loaded · preserved"
    if values.get("cleanup_error") == "yes":
        return "cleanup failed"
    return "managed" if values.get("managed") == "yes" else "not managed"


def _background_candidate_test(
    row,
    run_id,
    eval_results_dir,
    timeout,
    database_path,
    score_config=None,
):
    if run_id in _existing_benchmark_run_ids(database_path, eval_results_dir):
        return {
            "candidate_id": row.get("candidate_id", ""),
            "model_name": row.get("model_name", ""),
            "model_id": row.get("local_model_id", ""),
            "runner": row.get("local_runner", ""),
            "run_id": run_id,
            "status": "failed",
            "reason": "benchmark run id or artifact directory already exists; run was not started",
        }
    try:
        run_result = _run_candidate_test_for_row(row, run_id, eval_results_dir, timeout)
        score_result = None
        scores_path = None
        scoring_status = "disabled"
        scoring_reason = ""
        if (
            score_config
            and score_config.get("enabled")
            and run_result["init"].returncode == 0
            and run_result["capture"] is not None
            and run_result["capture"].returncode == 0
        ):
            scoring_status = "pending"
            try:
                score_result, draft_path = _suggest_draft_scores(
                    run_id,
                    eval_results_dir,
                    timeout,
                    score_config["endpoint"],
                    score_config.get("judge_model"),
                )
                if score_result.returncode == 0:
                    scores_path = draft_path
                    scoring_status = "draft"
                else:
                    scoring_reason = (
                        f"draft scoring exited {score_result.returncode}; "
                        "raw benchmark evidence preserved"
                    )
            except Exception:
                scoring_reason = (
                    "draft scoring did not complete; raw benchmark evidence preserved"
                )
        elif score_config and score_config.get("enabled"):
            scoring_status = "not_run"
        export_result = _export_dashboard_import(
            run_id,
            eval_results_dir,
            timeout,
            scores_path=scores_path,
        )
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
        capture_passed = (
            run_result["init"].returncode == 0
            and run_result["capture"] is not None
            and run_result["capture"].returncode == 0
        )
        return {
            "candidate_id": row.get("candidate_id", ""),
            "model_name": row.get("model_name", ""),
            "model_id": row.get("local_model_id", ""),
            "runner": row.get("local_runner", ""),
            "run_id": run_id,
            "status": "failed" if failures else "passed",
            "capture_status": "passed" if capture_passed else "failed",
            "scoring_status": scoring_status,
            "review_status": "awaiting review" if scoring_status == "draft" else "not ready",
            "lifecycle_status": _lifecycle_summary(Path(eval_results_dir) / run_id),
            "reason": "; ".join(failures or ([scoring_reason] if scoring_reason else [])),
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
            "capture_status": "failed",
            "scoring_status": "not run",
            "review_status": "not ready",
            "lifecycle_status": _lifecycle_summary(Path(eval_results_dir) / run_id),
            "reason": f"{type(exc).__name__}: {exc}",
        }


def _start_candidate_test(
    candidate_id,
    registry_path,
    eval_results_dir,
    timeout,
    database_path,
    score_config=None,
    *,
    clock=None,
):
    row, run_id = _candidate_test_plan(
        candidate_id,
        registry_path,
        eval_results_dir,
        database_path,
        clock=clock,
    )
    run_dir = Path(eval_results_dir) / run_id
    thread = threading.Thread(
        target=_background_candidate_test,
        args=(row, run_id, eval_results_dir, timeout, database_path, score_config),
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


def _background_candidate_batch(
    plan,
    eval_results_dir,
    timeout,
    database_path,
    status,
    score_config=None,
):
    status["state"] = "running"
    try:
        for item in plan:
            try:
                args = [
                    item["candidate"],
                    item["run_id"],
                    eval_results_dir,
                    timeout,
                    database_path,
                ]
                if score_config:
                    args.append(score_config)
                result = _background_candidate_test(*args)
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


def _start_candidate_batch(plan, eval_results_dir, timeout, database_path, score_config=None):
    if not plan:
        raise ValueError("No runnable models were confirmed.")
    run_ids = [item.get("run_id", "") for item in plan]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("Run-all preflight contains duplicate run ids.")
    existing_ids = _existing_benchmark_run_ids(database_path, eval_results_dir)
    collisions = sorted(set(run_ids) & existing_ids)
    if collisions:
        raise ValueError(
            "Run-all artifact target now exists; refresh preflight before execution: "
            + ", ".join(collisions)
        )
    batch_id = f"dashboard-batch-{secrets.token_urlsafe(9)}"
    status = _new_run_all_status(batch_id, plan)
    thread = threading.Thread(
        target=_background_candidate_batch,
        args=(plan, eval_results_dir, timeout, database_path, status, score_config),
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
        if state == "passed" and result.get("scoring_status") == "pending":
            state = "Capture passed · Scoring pending"
        elif state == "passed" and result.get("scoring_status") == "draft":
            state = "Capture passed · Draft scored"
        rows.append(
            [
                _text(item.get("model_name") or "—"),
                f'<code>{_text(item.get("model_id") or "—")}</code>',
                f'<code>{_text(item.get("runner") or "—")}</code>',
                f'<code>{_text(item.get("run_id") or "—")}</code>',
                _pill(state),
                _pill(result.get("capture_status") or "queued"),
                _pill(result.get("scoring_status") or "queued"),
                _pill(result.get("review_status") or "queued"),
                _text(result.get("lifecycle_status") or "—"),
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
            [
                "Model",
                "Exact model id",
                "Runner",
                "Run id",
                "Overall",
                "Capture",
                "Scoring",
                "Review",
                "Lifecycle",
                "Reason",
            ],
            rows,
            empty_message="No run-all batch entries were recorded.",
        ),
    )
    return _layout("Run All Summary", "/inventory", body)


def _import_artifact(benchmark_run_id, database_path, eval_results_dir=None):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise ValueError(f"Artifact not found: {benchmark_run_id}")
    if score_review.review_state(artifact_dir).get("status") == "rejected":
        raise ValueError(
            "Rejected evidence is preserved outside active rankings; create a fresh "
            "capture or rescore attempt instead of re-importing the rejected draft."
        )
    role = model_roles.artifact_model_role(artifact_dir)
    if not model_roles.model_supports_generation(role):
        raise ValueError(
            f"{role.title()} artifacts require their matching evaluation lane and cannot be "
            "imported into generative-model rankings."
        )
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


def _score_artifact(
    benchmark_run_id,
    database_path,
    eval_results_dir,
    timeout,
    judge_endpoint,
    judge_model=None,
):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise ValueError(f"Artifact not found: {benchmark_run_id}")
    role = model_roles.artifact_model_role(artifact_dir)
    if not model_roles.model_supports_generation(role):
        return _auto_reject_invalid_artifact(
            benchmark_run_id,
            database_path,
            eval_results_dir,
        )
    draft_path = artifact_dir / "draft-scores.json"
    review = score_review.review_state(artifact_dir)
    disposition = score_review.automatic_disposition(artifact_dir)
    if review.get("status") == "rejected" and review.get("human_action") == "rejected":
        raise ValueError(
            "This artifact was rejected by the owner; create a fresh benchmark run "
            "instead of reusing it."
        )
    if disposition and disposition["recommended_action"] == "rescore":
        _archive_score_attempt(
            artifact_dir,
            ("draft-scores.json", "review-scores.json", "score-review.json"),
        )
    elif disposition and disposition["recommended_action"] == "rerun_review":
        _archive_score_attempt(
            artifact_dir,
            ("review-scores.json", "score-review.json"),
        )
    elif disposition:
        return _auto_reject_invalid_artifact(
            benchmark_run_id,
            database_path,
            eval_results_dir,
            disposition,
        )
    for attempt in range(2):
        if draft_path.exists():
            break
        score_result, draft_path = _suggest_draft_scores(
            benchmark_run_id,
            eval_results_dir,
            timeout,
            judge_endpoint,
            judge_model,
        )
        if score_result.returncode != 0:
            raise ValueError("Draft scoring failed; inspect the artifact and local judge server.")
        disposition = score_review.automatic_disposition(artifact_dir)
        if not disposition:
            break
        if disposition["recommended_action"] == "rescore" and attempt == 0:
            _archive_score_attempt(
                artifact_dir,
                ("draft-scores.json", "review-scores.json", "score-review.json"),
            )
            continue
        return _auto_reject_invalid_artifact(
            benchmark_run_id,
            database_path,
            eval_results_dir,
            disposition,
        )
    export_result = _export_dashboard_import(
        benchmark_run_id,
        eval_results_dir,
        timeout,
        scores_path=draft_path,
    )
    if export_result.returncode != 0:
        raise ValueError("Dashboard export with draft scores failed.")
    imported = _import_artifact(benchmark_run_id, database_path, eval_results_dir)
    imported["draft_scores"] = str(draft_path)
    return imported


def _review_artifact(
    benchmark_run_id,
    eval_results_dir,
    timeout,
    reviewer_endpoint,
    reviewer_model,
    database_path=None,
):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    primary_path = artifact_dir / "draft-scores.json"
    if not primary_path.is_file():
        raise ValueError("Draft score artifact is missing.")
    if (artifact_dir / "scores.json").is_file():
        raise ValueError("This artifact already has a confirmed score.")
    current_review = score_review.review_state(artifact_dir)
    if (
        current_review.get("status") == "rejected"
        and current_review.get("human_action") == "rejected"
    ):
        raise ValueError("This artifact was rejected by the owner.")
    disposition = score_review.automatic_disposition(artifact_dir)
    if disposition and disposition["recommended_action"] != "rerun_review":
        return _auto_reject_invalid_artifact(
            benchmark_run_id,
            database_path,
            eval_results_dir,
            disposition,
        )
    if disposition:
        _archive_score_attempt(
            artifact_dir,
            ("review-scores.json", "score-review.json"),
        )
    reviewer_path = artifact_dir / "review-scores.json"
    for attempt in range(2):
        result, reviewer_path = _suggest_draft_scores(
            benchmark_run_id,
            eval_results_dir,
            timeout,
            reviewer_endpoint,
            reviewer_model,
            output_path=reviewer_path,
        )
        if result.returncode != 0:
            raise ValueError(
                "Reviewer output was invalid after a local retry; verify the reviewer model "
                "and retry this artifact."
            )
        disposition = score_review.automatic_disposition(artifact_dir)
        if not disposition:
            break
        if disposition["recommended_action"] == "rerun_review" and attempt == 0:
            _archive_score_attempt(
                artifact_dir,
                ("review-scores.json", "score-review.json"),
            )
            continue
        return _auto_reject_invalid_artifact(
            benchmark_run_id,
            database_path,
            eval_results_dir,
            disposition,
        )
    comparison = score_review.evaluate_artifact_review(artifact_dir)
    comparison["benchmark_run_id"] = benchmark_run_id
    score_review.write_review_record(artifact_dir, comparison)
    if database_path is not None:
        export_result = _export_dashboard_import(
            benchmark_run_id,
            eval_results_dir,
            timeout,
            scores_path=primary_path,
        )
        if export_result.returncode != 0:
            raise ValueError("Dashboard export after independent review failed.")
        _import_artifact(benchmark_run_id, database_path, eval_results_dir)
    return comparison


def _form_value(form, key):
    value = form.get(key, "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _confirm_artifact_score(
    benchmark_run_id,
    form,
    database_path,
    eval_results_dir,
    timeout,
):
    if _form_value(form, "human_reviewed") != "yes":
        raise ValueError("Human review acknowledgement is required before confirmation.")
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    primary_path = artifact_dir / "draft-scores.json"
    primary = score_review.load_json_object(primary_path)
    if not primary:
        raise ValueError("Draft score artifact is missing or invalid.")
    review_status = score_review.review_state(artifact_dir).get("status")
    if review_status not in ("machine_reviewed", "disagreement"):
        raise ValueError(
            "Independent review is required before a draft score can be confirmed."
        )
    mode = _form_value(form, "confirmation_mode") or "edited"
    if mode == "primary":
        score_edits = primary.get("scores") or {}
        final_label = primary.get("final_label")
    elif mode == "edited":
        score_edits = {
            field: _form_value(form, field) for field in score_review.METRIC_FIELDS
        }
        final_label = _form_value(form, "final_label")
    else:
        raise ValueError("Unknown confirmation mode.")
    confirmed = score_review.build_confirmed_score(
        primary,
        score_edits,
        final_label,
    )
    pending_path = artifact_dir / ".scores.pending.json"
    scores_path = artifact_dir / "scores.json"
    score_review.write_json_atomic(pending_path, confirmed)
    try:
        export_result = _export_dashboard_import(
            benchmark_run_id,
            eval_results_dir,
            timeout,
            scores_path=pending_path,
        )
        if export_result.returncode != 0:
            raise ValueError("Dashboard export with confirmed scores failed.")
        pending_path.replace(scores_path)
        imported = _import_artifact(benchmark_run_id, database_path, eval_results_dir)
    finally:
        pending_path.unlink(missing_ok=True)
    prior_review = score_review.load_json_object(artifact_dir / "score-review.json")
    machine_status = prior_review.get("status")
    review_record = dict(prior_review)
    review_record.update(
        {
            "status": "confirmed",
            "machine_status": machine_status
            if machine_status in ("machine_reviewed", "disagreement")
            else "not_reviewed",
            "human_action": "confirmed_primary" if mode == "primary" else "edited_and_confirmed",
        }
    )
    score_review.write_review_record(artifact_dir, review_record)
    return {
        "benchmark_run_id": benchmark_run_id,
        "status": "confirmed",
        "mode": mode,
        "counts": imported.get("counts", {}),
    }


def _confirm_reviewed_agreements(
    run_ids,
    form,
    database_path,
    eval_results_dir,
    timeout,
):
    if _form_value(form, "human_reviewed") != "yes":
        raise ValueError(
            "Human review acknowledgement is required before batch confirmation."
        )
    submitted_ids = list(dict.fromkeys(str(run_id) for run_id in run_ids if run_id))
    if not submitted_ids:
        raise ValueError("No reviewed agreements were submitted for confirmation.")
    available_ids = set(score_review.confirmable_agreement_ids(eval_results_dir))
    unavailable_ids = [run_id for run_id in submitted_ids if run_id not in available_ids]
    if unavailable_ids:
        raise ValueError(
            "The review queue changed or includes a disagreement; reload it before "
            "confirming agreements."
        )
    results = []
    confirmation_form = {
        "human_reviewed": ["yes"],
        "confirmation_mode": ["primary"],
    }
    for run_id in submitted_ids:
        try:
            result = _confirm_artifact_score(
                run_id,
                confirmation_form,
                database_path,
                eval_results_dir,
                timeout,
            )
            results.append(
                {
                    "benchmark_run_id": run_id,
                    "status": result.get("status") or "confirmed",
                    "reason": "",
                }
            )
        except Exception:
            results.append(
                {
                    "benchmark_run_id": run_id,
                    "status": "failed",
                    "reason": (
                        "Confirmation did not complete; inspect this artifact and retry."
                    ),
                }
            )
    return {
        "status": "complete",
        "results": results,
        "confirmed": sum(item["status"] == "confirmed" for item in results),
        "failed": sum(item["status"] == "failed" for item in results),
    }


def _reject_artifact_score(benchmark_run_id, form, database_path, eval_results_dir):
    if _form_value(form, "human_reviewed") != "yes":
        raise ValueError("Human review acknowledgement is required before rejection.")
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    if not (artifact_dir / "draft-scores.json").is_file():
        raise ValueError("Draft score artifact is missing.")
    if (artifact_dir / "scores.json").is_file():
        raise ValueError("A confirmed score cannot be rejected from the draft review queue.")
    prior_review = score_review.load_json_object(artifact_dir / "score-review.json")
    machine_status = prior_review.get("status")
    review_record = dict(prior_review)
    review_record.update(
        {
            "status": "rejected",
            "machine_status": machine_status
            if machine_status in ("machine_reviewed", "disagreement")
            else "not_reviewed",
            "human_action": "rejected",
            "flags": sorted(set(prior_review.get("flags") or ()) | {"human_rejected"}),
        }
    )
    score_review.write_review_record(artifact_dir, review_record)
    db.init_db(database_path, reset=False)
    with db.connect(database_path) as conn:
        run = _dashboard_runs_by_benchmark_id(conn).get(benchmark_run_id)
        if run and run["score_status"] == "draft" and run["score_id"] is not None:
            conn.execute(
                "DELETE FROM eval_scores WHERE id = ? AND score_status = 'draft'",
                (run["score_id"],),
            )
            conn.commit()
    return {"benchmark_run_id": benchmark_run_id, "status": "rejected"}


def _new_review_batch_status(batch_id, run_ids):
    return {
        "batch_id": batch_id,
        "state": "queued",
        "run_ids": list(run_ids),
        "results": [],
        "current_run_id": "",
    }


def _background_review_batch(
    run_ids,
    eval_results_dir,
    timeout,
    reviewer_endpoint,
    reviewer_model,
    status,
    database_path=None,
):
    status["state"] = "running"
    try:
        for run_id in run_ids:
            status["current_run_id"] = run_id
            try:
                review = _review_artifact(
                    run_id,
                    eval_results_dir,
                    timeout,
                    reviewer_endpoint,
                    reviewer_model,
                    database_path,
                )
                result = {
                    "run_id": run_id,
                    "status": (
                        "quarantined"
                        if review.get("status") == "rejected"
                        else "passed"
                    ),
                    "review_status": review["status"],
                    "reason": review.get("reason") or "",
                }
            except Exception as exc:
                if isinstance(exc, ValueError) and str(exc).startswith(
                    "Reviewer output was invalid after a local retry"
                ):
                    reason = str(exc)
                else:
                    reason = "Independent review did not complete; inspect the local reviewer and retry."
                result = {
                    "run_id": run_id,
                    "status": "failed",
                    "review_status": "",
                    "reason": reason,
                }
            status["results"].append(result)
    finally:
        status["current_run_id"] = ""
        status["state"] = "complete"
    return status


def _start_review_batch(
    run_ids,
    eval_results_dir,
    timeout,
    reviewer_endpoint,
    reviewer_model,
    primary_endpoint,
    primary_model,
    database_path=None,
):
    if not run_ids:
        raise ValueError("No draft artifacts are awaiting independent review.")
    _reviewer_preflight(
        reviewer_endpoint,
        reviewer_model,
        primary_endpoint,
        primary_model,
        min(timeout, 10),
    )
    batch_id = f"dashboard-review-{secrets.token_urlsafe(9)}"
    status = _new_review_batch_status(batch_id, run_ids)
    thread = threading.Thread(
        target=_background_review_batch,
        args=(
            run_ids,
            eval_results_dir,
            timeout,
            reviewer_endpoint,
            reviewer_model,
            status,
            database_path,
        ),
        daemon=True,
        name=f"dashboard-review-all-{batch_id[-24:]}",
    )
    thread.start()
    return {"batch_id": batch_id, "status": status, "thread_name": thread.name}


def _new_score_batch_status(batch_id, run_ids):
    return {
        "batch_id": batch_id,
        "state": "queued",
        "run_ids": list(run_ids),
        "current_run_id": "",
        "results": [],
    }


def _background_score_batch(
    run_ids,
    database_path,
    eval_results_dir,
    timeout,
    judge_endpoint,
    judge_model,
    status,
):
    status["state"] = "running"
    try:
        for run_id in run_ids:
            status["current_run_id"] = run_id
            try:
                scored = _score_artifact(
                    run_id,
                    database_path,
                    eval_results_dir,
                    timeout,
                    judge_endpoint,
                    judge_model,
                )
                result = {
                    "run_id": run_id,
                    "status": (
                        "quarantined"
                        if scored.get("status") == "rejected"
                        else "passed"
                    ),
                    "reason": scored.get("reason") or "",
                }
            except Exception as exc:
                result = {
                    "run_id": run_id,
                    "status": "failed",
                    "reason": f"{type(exc).__name__}: scoring did not complete",
                }
            status["results"].append(result)
    finally:
        status["current_run_id"] = ""
        status["state"] = "complete"
    return status


def _start_score_batch(
    run_ids,
    database_path,
    eval_results_dir,
    timeout,
    judge_endpoint,
    judge_model,
):
    if not run_ids:
        raise ValueError("No unscored raw artifacts are available.")
    _judge_preflight(judge_endpoint, judge_model, min(timeout, 10))
    batch_id = f"dashboard-score-{secrets.token_urlsafe(9)}"
    status = _new_score_batch_status(batch_id, run_ids)
    thread = threading.Thread(
        target=_background_score_batch,
        args=(
            run_ids,
            database_path,
            eval_results_dir,
            timeout,
            judge_endpoint,
            judge_model,
            status,
        ),
        daemon=True,
        name=f"dashboard-score-all-{batch_id[-24:]}",
    )
    thread.start()
    return {"batch_id": batch_id, "status": status, "thread_name": thread.name}


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


def _score_action_page(result):
    if result.get("status") == "rejected":
        body = """
        <section class="panel page-intro">
          <h2>Invalid Evidence Quarantined</h2>
          <p><strong>Benchmark run:</strong> {artifact}</p>
          <p><strong>Reason:</strong> {reason}</p>
          <p><strong>Automated next step:</strong> {next_action}</p>
          <p class="section-note">The raw artifact and prior score attempt are preserved, but this result is excluded from active rankings and human confirmation.</p>
          <p><a href="/runs">Back to Benchmark</a></p>
        </section>
        """.format(
            artifact=_artifact_link(result["benchmark_run_id"]),
            reason=_text(result.get("reason") or "Invalid evidence"),
            next_action=_text(
                str(result.get("recommended_action") or "rerun").replace("_", " ")
            ),
        )
        return _layout("Invalid Evidence Quarantined", "/runs", body)
    body = """
    <section class="panel">
      <h2>Draft Score Suggested</h2>
      <p><strong>Benchmark run:</strong> {artifact}</p>
      <p><strong>Draft scores:</strong> <code>{draft_scores}</code></p>
      <p><strong>Imported rows:</strong> <code>{counts}</code></p>
      <p><a href="/runs">Inspect imported draft score</a></p>
    </section>
    """.format(
        artifact=_artifact_link(result["benchmark_run_id"]),
        draft_scores=_text(result.get("draft_scores")),
        counts=_text(result["counts"]),
    )
    return _layout("Draft Score Suggested", "", body)


def _score_all_started_page(started):
    batch_id = started["batch_id"]
    count = len(started["status"].get("run_ids", []))
    body = f"""
    <section class="panel page-intro">
      <h2>Bulk Draft Scoring Started</h2>
      <p><strong>{count} artifacts</strong> will be scored sequentially by the configured local judge.</p>
      <p><a href="/runs/score-all/status?batch_id={_text(batch_id)}">View scoring progress</a></p>
    </section>
    """
    return _layout("Bulk Draft Scoring Started", "/runs", body)


def _score_all_status_page(status):
    results = {item.get("run_id"): item for item in status.get("results", [])}
    current_run_id = status.get("current_run_id") or ""
    rows = []
    for run_id in status.get("run_ids", []):
        result = results.get(run_id, {})
        state = result.get("status") or ("scoring" if run_id == current_run_id else "queued")
        rows.append(
            [
                _artifact_link(run_id),
                _pill(state),
                _text(result.get("reason") or "—"),
            ]
        )
    passed = sum(item.get("status") == "passed" for item in status.get("results", []))
    failed = sum(item.get("status") == "failed" for item in status.get("results", []))
    quarantined = sum(
        item.get("status") == "quarantined" for item in status.get("results", [])
    )
    remaining = max(
        len(status.get("run_ids", [])) - passed - failed - quarantined,
        0,
    )
    body = """
    <section class="panel page-intro">
      <h2>Bulk Draft Scoring</h2>
      <p><strong>State:</strong> {state}</p>
      <p><strong>{passed} scored</strong> &middot; <strong>{quarantined} quarantined</strong> &middot; <strong>{failed} failed</strong> &middot; <strong>{remaining} remaining</strong></p>
      <p><a href="/runs">Back to Benchmark</a></p>
    </section>
    <section class="runs-section">{table}</section>
    """.format(
        state=_text(status.get("state") or "unknown"),
        passed=passed,
        quarantined=quarantined,
        failed=failed,
        remaining=remaining,
        table=_table(
            ["Artifact", "Status", "Reason"],
            rows,
            empty_message="No artifacts were queued for scoring.",
        ),
    )
    return _layout("Bulk Draft Scoring", "/runs", body)


def _review_all_started_page(started):
    batch_id = started["batch_id"]
    count = len(started["status"].get("run_ids", []))
    body = f"""
    <section class="panel page-intro">
      <h2>Independent Review Started</h2>
      <p><strong>{count} draft artifacts</strong> will be reviewed sequentially by the configured independent local model.</p>
      <p class="empty">The reviewer sees the benchmark evidence and rubric, not the primary judge's draft score. Machine review never confirms a score.</p>
      <p><a href="/runs/review-all/status?batch_id={_text(batch_id)}">View review progress</a></p>
    </section>
    """
    return _layout("Independent Review Started", "/runs", body)


def _review_all_status_page(status):
    results = {item.get("run_id"): item for item in status.get("results", [])}
    current_run_id = status.get("current_run_id") or ""
    rows = []
    for run_id in status.get("run_ids", []):
        result = results.get(run_id, {})
        state = result.get("status") or (
            "reviewing" if run_id == current_run_id else "queued"
        )
        rows.append(
            [
                _artifact_link(run_id),
                _pill(state),
                _pill(result.get("review_status") or "pending"),
                _text(result.get("reason") or "—"),
            ]
        )
    reviewed = sum(item.get("status") == "passed" for item in status.get("results", []))
    failed = sum(item.get("status") == "failed" for item in status.get("results", []))
    quarantined = sum(
        item.get("status") == "quarantined" for item in status.get("results", [])
    )
    remaining = max(
        len(status.get("run_ids", [])) - reviewed - failed - quarantined,
        0,
    )
    body = """
    <section class="panel page-intro">
      <h2>Independent Draft Review</h2>
      <p><strong>State:</strong> {state}</p>
      <p><strong>{reviewed} reviewed</strong> &middot; <strong>{quarantined} quarantined</strong> &middot; <strong>{failed} failed</strong> &middot; <strong>{remaining} remaining</strong></p>
      <p class="empty">Only valid judge agreements or disagreements continue to human confirmation. Structurally invalid evidence is quarantined automatically.</p>
      <p><a href="/reviews">Open Draft Review Queue</a></p>
    </section>
    <section class="runs-section">{table}</section>
    """.format(
        state=_text(status.get("state") or "unknown"),
        reviewed=reviewed,
        quarantined=quarantined,
        failed=failed,
        remaining=remaining,
        table=_table(
            ["Artifact", "Worker status", "Review outcome", "Reason"],
            rows,
            empty_message="No artifacts were queued for independent review.",
        ),
    )
    return _layout("Independent Draft Review", "/runs", body)


def _human_score_action_page(result):
    action = result.get("status") or "updated"
    body = """
    <section class="panel page-intro">
      <h2>Draft Score {action}</h2>
      <p><strong>Artifact:</strong> {artifact}</p>
      <p><strong>Status:</strong> {status}</p>
      <p><a href="/reviews">Back to Draft Review Queue</a></p>
    </section>
    """.format(
        action=_text(action.title()),
        artifact=_artifact_link(result.get("benchmark_run_id")),
        status=_pill(action),
    )
    return _layout(f"Draft Score {action.title()}", "/runs", body)


def _human_confirmation_batch_page(result):
    rows = [
        [
            _artifact_link(item.get("benchmark_run_id")),
            _pill(item.get("status") or "unknown"),
            _text(item.get("reason") or "—"),
        ]
        for item in result.get("results", [])
    ]
    body = """
    <section class="panel page-intro">
      <h2>Reviewed Agreement Confirmation</h2>
      <p><strong>{confirmed} confirmed</strong> &middot; <strong>{failed} failed</strong></p>
      <p class="section-note">Only independently reviewed agreements were eligible. Disagreements remain in the review queue.</p>
      <p><a href="/reviews">Back to Draft Review Queue</a></p>
    </section>
    <section class="runs-section">{table}</section>
    """.format(
        confirmed=_text(result.get("confirmed", 0)),
        failed=_text(result.get("failed", 0)),
        table=_table(
            ["Artifact", "Status", "Reason"],
            rows,
            empty_message="No reviewed agreements were confirmed.",
        ),
    )
    return _layout("Reviewed Agreement Confirmation", "/reviews", body)


__all__ = ('_build_candidate_commands', '_candidate_test_plan', '_run_candidate_test_for_row', '_run_candidate_test', '_start_candidate_test', '_new_run_all_status', '_background_candidate_batch', '_start_candidate_batch', '_result_block', '_run_action_page', '_run_action_started_page', '_run_all_started_page', '_run_all_status_page', '_import_artifact', '_import_action_page', '_judge_model_ids', '_judge_preflight', '_reviewer_preflight', '_unscored_artifact_ids', '_score_artifact', '_score_action_page', '_review_artifact', '_confirm_artifact_score', '_confirm_reviewed_agreements', '_reject_artifact_score', '_new_review_batch_status', '_background_review_batch', '_start_review_batch', '_review_all_started_page', '_review_all_status_page', '_human_score_action_page', '_human_confirmation_batch_page', '_new_score_batch_status', '_background_score_batch', '_start_score_batch', '_score_all_started_page', '_score_all_status_page', '_sync_pending_artifacts', '_startup_import_sync', '_auto_reject_invalid_artifact', '_auto_reject_invalid_artifacts')
