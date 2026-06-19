"""Dashboard artifact page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path

from .. import capability, charts, db
from ..components import *
from ..filters import *
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS

def _artifact_detail(
    conn,
    benchmark_run_id,
    registry_path=CANDIDATE_REGISTRY_PATH,
    database_path=DEFAULT_DASHBOARD_DB,
    enable_import_actions=False,
    action_token="",
    eval_results_dir=None,
):
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    candidates = _load_radar_candidates(registry_path)
    candidate = next(
        (row for row in candidates if row.get("benchmark_run_id") == benchmark_run_id),
        None,
    )
    try:
        artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    except ValueError:
        return _layout("Benchmark Artifact", "", "<h2>Artifact not found</h2>")
    if candidate is None and not artifact_dir.exists():
        return _layout("Benchmark Artifact", "", "<h2>Artifact not found</h2>")

    dashboard_run = _dashboard_runs_by_benchmark_id(conn).get(benchmark_run_id)
    decisions_by_model = _latest_decisions_by_model_id(conn)
    dashboard_state = _import_state_for_run(dashboard_run, decisions_by_model)
    candidate_state = (
        _pill(candidate.get("status")) if candidate else '<span class="empty">not registered</span>'
    )
    artifact_name = (
        candidate.get("model_name")
        if candidate
        else dashboard_run["model_name"]
        if dashboard_run
        else benchmark_run_id
    )
    file_rows = []
    if artifact_dir.exists():
        for path in sorted(artifact_dir.iterdir(), key=lambda item: item.name.lower()):
            kind = "directory" if path.is_dir() else "file"
            file_rows.append([_text(path.name), _text(kind), _path_cell(_relative_path(path))])

    body = """
    <div class="split">
      <section class="panel">
        <h2>{name}</h2>
        <p><strong>Candidate:</strong> {status}</p>
        <p><strong>Benchmark run:</strong> <code>{run_id}</code></p>
        <p><strong>Dashboard:</strong> {dashboard_state}</p>
      </section>
      <section class="panel">
        <h2>Radar Context</h2>
        <p><strong>Source packet:</strong> {source}</p>
        <p><strong>Report:</strong> {report}</p>
      </section>
    </div>
    <section class="panel" style="margin-top:16px">
      <h2>Dashboard Import</h2>
      <p>This imports only existing local CSV files from this artifact's <code>dashboard-import</code> directory.</p>
      {import_control}
      {import_guidance}
    </section>
    <section style="margin-top:16px"><h2>Artifact Files</h2>{files}</section>
    """.format(
        name=_text(artifact_name),
        status=candidate_state,
        run_id=_text(benchmark_run_id),
        dashboard_state=dashboard_state,
        source=_path_cell(candidate.get("source_packet_path") if candidate else ""),
        report=_path_cell(candidate.get("report_path") if candidate else ""),
        import_control=_artifact_import_control(
            benchmark_run_id,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
            eval_results_dir=eval_results_dir,
        ),
        import_guidance=_artifact_import_guidance(
            benchmark_run_id,
            database_path,
            eval_results_dir,
        ),
        files=_table(
            ["Name", "Type", "Path"], file_rows, empty_message="Artifact directory not found."
        ),
    )
    return _layout("Benchmark Artifact", "", body)

__all__ = ('_artifact_detail',)
