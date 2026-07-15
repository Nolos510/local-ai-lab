"""Dashboard runs page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path

from .. import capability, charts, db, recommend
from ..components import *
from ..filters import *
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS
from ..sorting import _sort_rows, _sortable_headers
from .compare import _compare_section

RUN_SORT_COLUMNS = {
    "date": (lambda row: row["date_tested"], "text"),
    "model": (lambda row: row["model_name"], "text"),
    "backend": (lambda row: row["backend"], "text"),
    "format": (lambda row: row["format"], "text"),
    "quant": (lambda row: row["quantization"], "text"),
    "context": (lambda row: row["context_window"], "number"),
    "tokens_per_sec": (lambda row: row["tokens_per_sec"], "number"),
    "ram_usage_gb": (lambda row: row["ram_usage_gb"], "number"),
    "efficiency": (
        lambda row: charts.efficiency(row["tokens_per_sec"], row["ram_usage_gb"]),
        "number",
    ),
    "score": (lambda row: row["total_score"], "number"),
    "status": (lambda row: row["score_status"], "text"),
    "label": (lambda row: row["final_label"], "text"),
    "artifact": (lambda row: _benchmark_run_id_from_notes(row["run_notes"]), "text"),
    "stability": (lambda row: row["stability_notes"], "text"),
}
RUN_SORT_HEADERS = {
    "Date": "date",
    "Model": "model",
    "Backend": "backend",
    "Format": "format",
    "Quant": "quant",
    "Context": "context",
    "Tok/s": "tokens_per_sec",
    "RAM GB": "ram_usage_gb",
    "Efficiency": "efficiency",
    "Score": "score",
    "Status": "status",
    "Label": "label",
    "Artifact": "artifact",
    "Stability": "stability",
}


def _artifact_score_state(row):
    has_score = row["scores"] == "yes" or row["draft_scores"] == "yes"
    if row["dashboard_import"] != "yes":
        return "Export dashboard CSVs first."
    if has_score and row["decision"] == "yes":
        return "Scored artifact: import updates model, run, score, label, and decision."
    if has_score:
        return "Scored artifact: import updates score and label; decision still needs review."
    return "Raw run artifact: import updates model, run, and performance fields. Label needs reviewed scores and a decision."


def _pluralized_exclusion(count, singular, plural):
    verb = "is" if count == 1 else "are"
    noun = singular if count == 1 else plural
    return f"{count} {noun} {verb} excluded."


def _efficiency_frontier(runs):
    latest_confirmed_by_model = {}
    unconfirmed_count = 0
    for row in runs:
        if row["score_status"] != "confirmed":
            unconfirmed_count += 1
            continue
        if row["model_id"] not in latest_confirmed_by_model:
            latest_confirmed_by_model[row["model_id"]] = row

    items = []
    incomplete_count = 0
    for row in latest_confirmed_by_model.values():
        if charts.efficiency(row["tokens_per_sec"], row["ram_usage_gb"]) is None:
            incomplete_count += 1
            continue
        items.append(
            (
                row["model_name"],
                row["tokens_per_sec"],
                row["total_score"],
                row["ram_usage_gb"],
            )
        )

    notes = ["One point per model from its latest confirmed run."]
    if unconfirmed_count:
        notes.append(
            _pluralized_exclusion(
                unconfirmed_count,
                "run without confirmed scores",
                "runs without confirmed scores",
            )
        )
    else:
        notes.append("Runs without confirmed scores are excluded.")
    if incomplete_count:
        notes.append(
            _pluralized_exclusion(
                incomplete_count,
                "latest confirmed run missing usable throughput or peak RAM",
                "latest confirmed runs missing usable throughput or peak RAM",
            )
        )
    chart = charts.scatter(
        items,
        title="Efficiency frontier",
        empty_message="No latest confirmed runs with throughput and peak RAM yet",
    )
    return chart, " ".join(notes)


def _runs(
    conn,
    query=None,
    database_path=DEFAULT_DASHBOARD_DB,
    eval_results_dir=EVAL_RESULTS_DIR,
    enable_import_actions=False,
    action_token="",
    import_sync_result=None,
):
    rows = []
    all_runs = db.list_runs(conn)
    runs = _real_rows(all_runs)
    task_summary = recommend.task_recommendations(_real_rows(db.list_score_details(conn)))
    filters = _run_filter_values(query or {})
    filtered_runs = _filter_runs(runs, filters)
    frontier_chart, frontier_note = _efficiency_frontier(filtered_runs)
    sorted_runs = _sort_rows(filtered_runs, query or {}, RUN_SORT_COLUMNS)
    for row in sorted_runs:
        efficiency_value = charts.efficiency(row["tokens_per_sec"], row["ram_usage_gb"])
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
                _number(row["tokens_per_sec"], fallback="—"),
                _number(row["ram_usage_gb"], fallback="—"),
                _number(efficiency_value, 2, "—"),
                _number(row["total_score"], 2, "—"),
                _status_pill(row["score_status"]) if row["score_status"] else "—",
                _pill(row["final_label"]),
                _artifact_link_from_notes(row["run_notes"]),
                _text(row["stability_notes"]),
            ]
        )
    artifact_rows = []
    dashboard_runs = _dashboard_runs_by_benchmark_id(conn)
    decisions_by_model = _latest_decisions_by_model_id(conn)
    pending_import_count = len(_pending_artifact_run_ids(conn, eval_results_dir))
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
    {import_sync_notice}
    {notice}
    <section class="panel page-intro">
      <p>Benchmark runs and side-by-side comparisons. Higher score and throughput are better; lower latency is better when latency fields exist.</p>
      <p class="empty">Benchmark reads local dashboard imports and artifact folders only. It does not download, install, run, or score a model by itself.</p>
    </section>
    {task_leaders}
    <section class="runs-section efficiency-frontier-section">
      {frontier_panel}
      <p class="section-note">{frontier_note}</p>
    </section>
    <section class="runs-section">
      <h2>Model Runs{filtered_count}</h2>
      <p class="section-note">Model Runs are imported local benchmark run records. A row may have raw performance fields before reviewed scores or keep/watch decisions exist.</p>
      {filters}
      {table}
    </section>
    <section class="runs-section runs-compare-section">
      {compare_section}
    </section>
    <section class="runs-section runs-artifact-section">
      <h2>Local Artifact Import Queue</h2>
      <p class="section-note">Use this queue for benchmark artifacts already written under <code>data/eval_results</code>. Importing a raw run updates model/run/performance data; labels and stability reports appear only after reviewed score and decision files exist.</p>
      {import_all_control}
      {artifact_table}
    </section>
    """.format(
        import_sync_notice=_import_sync_notice(import_sync_result),
        notice=_real_data_notice(len(_demo_rows(all_runs))),
        task_leaders=_task_leaders(task_summary, surface_class="task-leaders-benchmark"),
        frontier_panel=_chart_panel("Efficiency Frontier", frontier_chart),
        frontier_note=_text(frontier_note),
        filters=_runs_filters(runs, filters),
        filtered_count=(f" ({len(filtered_runs)} of {len(runs)})" if any(filters.values()) else ""),
        compare_section=_compare_section(
            conn,
            include_notice=False,
            include_filters=False,
            include_deep_link=True,
        ),
        import_all_control=_artifact_import_all_control(
            pending_import_count,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
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
                "Efficiency",
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
            sortable_headers=_sortable_headers(
                "/runs",
                query or {},
                RUN_SORT_HEADERS,
            ),
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
