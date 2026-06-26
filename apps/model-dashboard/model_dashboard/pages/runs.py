"""Dashboard runs page."""

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
from .compare import _compare_section


def _artifact_score_state(row):
    has_score = row["scores"] == "yes" or row["draft_scores"] == "yes"
    if row["dashboard_import"] != "yes":
        return "Export dashboard CSVs first."
    if has_score and row["decision"] == "yes":
        return "Scored artifact: import updates model, run, score, label, and decision."
    if has_score:
        return "Scored artifact: import updates score and label; decision still needs review."
    return "Raw run artifact: import updates model, run, and performance fields. Label needs reviewed scores and a decision."


def _runs(
    conn,
    query=None,
    database_path=DEFAULT_DASHBOARD_DB,
    eval_results_dir=EVAL_RESULTS_DIR,
    enable_import_actions=False,
    action_token="",
):
    rows = []
    all_runs = db.list_runs(conn)
    runs = _real_rows(all_runs)
    filters = _run_filter_values(query or {})
    filtered_runs = _filter_runs(runs, filters)
    for row in filtered_runs:
        rows.append(
            [
                _text(row["date_tested"]),
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["model_id"], name=_text(row["model_name"])
                ),
                _text(row["backend"]),
                _text(row["format"]),
                _text(row["quantization"]),
                _text(row["context_window"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _number(row["total_score"], 2),
                _status_pill(row["score_status"]),
                _pill(row["final_label"]),
                _artifact_link_from_notes(row["run_notes"]),
                _text(row["stability_notes"]),
            ]
        )
    artifact_rows = []
    dashboard_runs = _dashboard_runs_by_benchmark_id(conn)
    decisions_by_model = _latest_decisions_by_model_id(conn)
    for artifact in sorted(
        _artifact_summaries(eval_results_dir),
        key=lambda row: row["benchmark_run_id"],
        reverse=True,
    ):
        run_id = artifact["benchmark_run_id"]
        artifact_rows.append(
            [
                _artifact_link(run_id),
                _text(artifact["raw_responses"]),
                _text(artifact["scores"]),
                _text(artifact["draft_scores"]),
                _text(artifact["decision"]),
                _text(artifact["dashboard_import"]),
                _import_state_for_run(dashboard_runs.get(run_id), decisions_by_model),
                _text(_artifact_score_state(artifact)),
                _artifact_import_control(
                    run_id,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                    eval_results_dir=eval_results_dir,
                ),
            ]
        )
    body = """
    {notice}
    <section class="panel page-intro">
      <p>Benchmark runs and side-by-side comparisons. Higher score and throughput are better; lower latency is better when latency fields exist.</p>
      <p class="empty">Benchmark reads local dashboard imports and artifact folders only. It does not download, install, run, or score a model by itself.</p>
    </section>
    {filters}
    <h2>Model Runs{filtered_count}</h2>
    <p class="section-note">Model Runs are imported local benchmark run records. A row may have raw performance fields before reviewed scores or keep/watch decisions exist.</p>
    {table}
    <section class="section">
      {compare_section}
    </section>
    <section class="section">
      <h2>Local Artifact Import Queue</h2>
      <p class="muted">Use this queue for benchmark artifacts already written under <code>data/eval_results</code>. Importing a raw run updates model/run/performance data; labels and stability reports appear only after reviewed score and decision files exist.</p>
      {artifact_table}
    </section>
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_runs))),
        filters=_runs_filters(runs, filters),
        filtered_count=(f" ({len(filtered_runs)} of {len(runs)})" if any(filters.values()) else ""),
        compare_section=_compare_section(
            conn,
            include_notice=False,
            include_filters=False,
            include_deep_link=True,
        ),
        table=_table(
            [
                "Date",
                "Model",
                "Backend",
                "Format",
                "Quant",
                "Context",
                "Tok/s",
                "RAM GB",
                "Score",
                "Status",
                "Label",
                "Artifact",
                "Stability",
            ],
            rows,
            empty_message="No real benchmark runs match these filters.",
            table_class="runs-table",
            scroll_controls=True,
            scroll_id="model-runs-table-scroll",
            scroll_label="Model runs table",
            header_tip_keys=RESULT_TABLE_HEADER_TIPS,
        ),
        artifact_table=_table(
            [
                "Artifact",
                "Raw responses",
                "Scores",
                "Draft scores",
                "Decision",
                "Dashboard CSVs",
                "Dashboard state",
                "What import changes",
                "Action",
            ],
            artifact_rows,
            empty_message="No local benchmark artifacts found under data/eval_results.",
            table_class="artifact-import-table",
            scroll_controls=True,
            scroll_id="artifact-import-table-scroll",
            scroll_label="Artifact import queue",
        ),
    )
    return _layout("Benchmark", "/runs", body)

__all__ = ('_artifact_score_state', '_runs',)
