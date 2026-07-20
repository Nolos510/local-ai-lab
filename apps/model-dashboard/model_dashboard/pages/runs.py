"""Dashboard runs page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import urlencode

from .. import capability, charts, db, model_roles, recommend, score_review
from ..components import *
from ..filters import *
from ..layout import _layout
from ..pagination import _paginate, _pagination_controls
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
RUN_TABLE_HEADERS = (
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
)
GROUPED_RUN_TABLE_HEADERS = (
    "Date",
    "Model",
    "Backend",
    "Tok/s",
    "RAM GB",
    "Efficiency",
    "Score",
    "Status",
    "Label",
    "Artifact",
    "History",
)
GROUPED_RUN_HEADER_TIPS = {
    **RESULT_TABLE_HEADER_TIPS,
    "Model": "current_run",
}


def _run_text(value):
    return "—" if value in (None, "") else _text(value)


def _run_value(row, field):
    try:
        return row[field]
    except (KeyError, IndexError, TypeError):
        return row.get(field) if hasattr(row, "get") else None


def _run_config_text(row, field):
    value = _run_value(row, field)
    if value in (None, ""):
        return "—"
    run_notes = _run_value(row, "run_notes")
    source = _run_note_value(run_notes, f"{field}_source")
    if source.startswith("inferred:"):
        return (
            '<div class="cell-stack">'
            f"<span>{_text(value)}</span>"
            '<span class="empty">inferred</span>'
            "</div>"
        )
    return _text(value)


def _run_model_role(row):
    return model_roles.infer_model_role(
        _run_value(row, "model_name"),
        _run_value(row, "model_family"),
        _run_value(row, "provider"),
        _run_value(row, "format"),
    )


def _run_table_row(row, authoritative_run_ids):
    efficiency_value = charts.efficiency(row["tokens_per_sec"], row["ram_usage_gb"])
    current_badge = _current_run_badge() if row["id"] in authoritative_run_ids else ""
    return [
        _run_text(row["date_tested"]),
        '<div class="run-model-cell"><a href="/models/{id}">{name}</a>{badge}'
        '<span class="empty">{role}</span></div>'.format(
            id=row["model_id"],
            name=_text(row["model_name"]),
            badge=current_badge,
            role=_text(_run_model_role(row)),
        ),
        _run_text(row["backend"]),
        _run_text(row["format"]),
        _run_config_text(row, "quantization"),
        _run_config_text(row, "context_window"),
        _number(row["tokens_per_sec"], fallback="—"),
        _number(row["ram_usage_gb"], fallback="—"),
        _number(efficiency_value, 2, "—"),
        _number(row["total_score"], 2, "—"),
        _status_pill(row["score_status"]) if row["score_status"] else "—",
        _pill(row["final_label"]) if row["final_label"] else "—",
        _artifact_link_from_notes(row["run_notes"]) or "—",
        _run_text(row["stability_notes"]),
    ]


def _runs_view_href(query, group):
    pairs = []
    for key, value in (query or {}).items():
        if key == "group":
            continue
        values = value if isinstance(value, (list, tuple)) else (value,)
        for item in values:
            pairs.append((str(key), str(item)))
    pairs.append(("group", group))
    return f"/runs?{urlencode(pairs)}"


def _runs_grouped(query):
    mode = _query_value(query or {}, "group").lower()
    if mode == "on":
        return True
    if mode == "off":
        return False
    if any(
        _query_value(query or {}, key)
        for key in ("q", "backend", "label", "status", "model_id")
    ):
        return False
    return _query_value(query or {}, "sort") not in RUN_SORT_COLUMNS


def _runs_view_control(query, grouped):
    if grouped:
        label = "Grouped by model"
        link_label = "Show ungrouped sortable table"
        href = _runs_view_href(query, "off")
    else:
        label = "Ungrouped sortable table"
        link_label = "Group history by model"
        href = _runs_view_href(query, "on")
    return (
        '<div class="runs-view-control">'
        f'<span class="pill">{_text(label)}</span>'
        f'<a class="action-link secondary" href="{_text(href)}">{_text(link_label)}</a>'
        "</div>"
    )


def _compact_compare_section():
    return """
    <div class="section-heading-row">
      <div>
        <h2>Compare Models</h2>
        <p class="section-note">Open the dedicated comparison workspace for the complete score matrix, dimension averages, throughput, and latency charts.</p>
      </div>
      <a class="action-link secondary" href="/compare">Open compare filters</a>
    </div>
    """


def _runs_history_href(model_id):
    return "/runs?{}".format(
        urlencode(
            (
                ("group", "off"),
                ("model_id", str(model_id)),
                ("sort", "date"),
                ("dir", "desc"),
            )
        )
    )


def _run_history_control(group, model_name):
    history_count = len(group["other_runs"])
    if not history_count:
        return "—"
    history_label = f"{history_count} earlier run" + ("" if history_count == 1 else "s")
    href = _runs_history_href(group["authoritative_run"]["model_id"])
    return (
        '<details class="run-history">'
        f"<summary>{_text(history_label)}</summary>"
        '<p><a href="{href}">Open complete {model_name} history</a></p>'
        "</details>"
    ).format(
        href=_text(href),
        model_name=_text(model_name),
    )


def _grouped_run_table_row(row, group):
    full_row = _run_table_row(row, {group["authoritative_run_id"]})
    model_cell = (
        '<div class="run-model-cell"><a href="/models/{id}">{name}</a>'
        '<span class="pill current-run">current</span>'
        '<span class="empty">{role}</span></div>'
    ).format(
        id=row["model_id"],
        name=_text(row["model_name"]),
        role=_text(_run_model_role(row)),
    )
    return [
        full_row[0],
        model_cell,
        full_row[2],
        full_row[6],
        full_row[7],
        full_row[8],
        full_row[9],
        full_row[10],
        full_row[11],
        full_row[12],
        _run_history_control(group, row["model_name"]),
    ]


def _grouped_runs_table(sorted_runs, authoritative_groups):
    if not sorted_runs:
        return '<p class="empty">No real benchmark runs match these filters.</p>'
    rows_by_model = {}
    for row in sorted_runs:
        rows_by_model.setdefault(row["model_id"], []).append(row)
    current_rows = []
    outside_filter_notices = []
    for model_id, model_runs in rows_by_model.items():
        group = authoritative_groups[model_id]
        authoritative_id = group["authoritative_run_id"]
        current = next((row for row in model_runs if row["id"] == authoritative_id), None)
        if current is not None:
            current_rows.append(_grouped_run_table_row(current, group))
            continue
        model_name = model_runs[0]["model_name"]
        outside_filter_notices.append(
            '<div class="run-history-filter-note">'
            f'<strong><a href="/models/{model_id}">{_text(model_name)}</a></strong> '
            '<span class="empty">Current run is outside the active filters.</span>'
            f'{_run_history_control(group, model_name)}'
            '</div>'
        )
    table = _table(
        GROUPED_RUN_TABLE_HEADERS,
        current_rows,
        empty_message="No current runs match these filters.",
        table_class="runs-table grouped-runs-table",
        scroll_controls=True,
        scroll_id="model-runs-table-scroll",
        scroll_label="Current model runs table",
        header_tip_keys=GROUPED_RUN_HEADER_TIPS,
    )
    notices = (
        '<div class="run-history-filter-notes">{}</div>'.format(
            "".join(outside_filter_notices)
        )
        if outside_filter_notices
        else ""
    )
    return table + notices


def _artifact_score_state(row, review=None):
    if (review or {}).get("status") == "rejected":
        action = (review or {}).get("recommended_action") or "create a fresh run"
        return (
            "Rejected/quarantined audit evidence: excluded from active rankings. "
            f"Next machine action: {action.replace('_', ' ')}."
        )
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


def _artifact_review_state(row, eval_results_dir):
    run_id = _benchmark_run_id_from_notes(_run_value(row, "run_notes"))
    if not run_id:
        return {"status": "unscored"}
    try:
        artifact_dir = _safe_artifact_dir(run_id, eval_results_dir)
    except ValueError:
        return {"status": "unscored"}
    return score_review.review_state(artifact_dir)


def _efficiency_frontier(runs, eval_results_dir=EVAL_RESULTS_DIR):
    latest_confirmed_by_model = {}
    unscored_count = 0
    draft_count = 0
    quarantined_count = 0
    unconfirmed_count = 0
    non_generation_count = 0
    for row in runs:
        if not model_roles.model_supports_generation(_run_model_role(row)):
            non_generation_count += 1
            continue
        if not row["score_status"]:
            artifact_state = _artifact_review_state(row, eval_results_dir).get("status")
            if artifact_state == "rejected":
                quarantined_count += 1
            elif artifact_state in ("draft", "machine_reviewed", "disagreement"):
                draft_count += 1
            else:
                unscored_count += 1
        elif row["score_status"] == "draft":
            draft_count += 1
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

    notes = [
        "{} frontier-ready model{} shown.".format(
            len(items),
            "" if len(items) == 1 else "s",
        ),
        "One point per model from its latest confirmed run.",
    ]
    if unconfirmed_count:
        parts = []
        if unscored_count:
            parts.append(f"{unscored_count} unscored")
        if draft_count:
            parts.append(f"{draft_count} draft")
        if quarantined_count:
            parts.append(f"{quarantined_count} quarantined")
        if parts:
            notes.append(
                _pluralized_exclusion(
                    unconfirmed_count,
                    "run without confirmed scores",
                    "runs without confirmed scores",
                )
            )
            notes.append("Excluded score state: {}.".format(", ".join(parts)))
        else:
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
    if non_generation_count:
        notes.append(
            _pluralized_exclusion(
                non_generation_count,
                "embedding or reranker run",
                "embedding or reranker runs",
            )
        )
    chart = charts.scatter(
        items,
        title="Efficiency frontier",
        empty_message="No latest confirmed runs with throughput and peak RAM yet",
    )
    return chart, " ".join(notes)


def _score_resolution_counts(runs, eval_results_dir=EVAL_RESULTS_DIR):
    counts = {
        "frontier_ready": 0,
        "unscored": 0,
        "draft": 0,
        "quarantined": 0,
        "confirmed_missing_metrics": 0,
        "missing_run_config": 0,
        "non_generation": 0,
    }
    for row in runs:
        if not model_roles.model_supports_generation(_run_model_role(row)):
            counts["non_generation"] += 1
            continue
        if any(
            _run_value(row, field) in (None, "")
            for field in ("quantization", "context_window", "temperature", "top_p")
        ):
            counts["missing_run_config"] += 1
        if not row["score_status"]:
            artifact_state = _artifact_review_state(row, eval_results_dir).get("status")
            if artifact_state == "rejected":
                counts["quarantined"] += 1
            elif artifact_state in ("draft", "machine_reviewed", "disagreement"):
                counts["draft"] += 1
            else:
                counts["unscored"] += 1
            continue
        if row["score_status"] == "draft":
            counts["draft"] += 1
            continue
        if row["score_status"] == "confirmed":
            if charts.efficiency(row["tokens_per_sec"], row["ram_usage_gb"]) is None:
                counts["confirmed_missing_metrics"] += 1
            else:
                counts["frontier_ready"] += 1
    return counts


def _score_resolution_panel(runs, eval_results_dir=EVAL_RESULTS_DIR):
    counts = _score_resolution_counts(runs, eval_results_dir)
    rows = [
        [
            "Non-generative runs",
            _text(counts["non_generation"]),
            "Embedding and reranker artifacts use retrieval evaluation, not the LLM rubric.",
        ],
        [
            "Unscored raw runs",
            _text(counts["unscored"]),
            "Review raw responses, create/import scores, then mark draft or confirmed.",
        ],
        [
            "Draft scored runs",
            _text(counts["draft"]),
            "Await independent review; only valid judge agreement or disagreement reaches human confirmation.",
        ],
        [
            "Rejected or quarantined runs",
            _text(counts["quarantined"]),
            "Preserved for audit and excluded from rankings; follow the recorded rescore, rerun, or role-specific action.",
        ],
        [
            "Confirmed but missing frontier metrics",
            _text(counts["confirmed_missing_metrics"]),
            "Rerun or re-import performance so tokens/sec and RAM GB are both present.",
        ],
        [
            "Missing run config",
            _text(counts["missing_run_config"]),
            "Backfill or rerun so quantization, context window, temperature, and top_p are recorded.",
        ],
        [
            "Frontier-ready confirmed runs",
            _text(counts["frontier_ready"]),
            "Already actionable for score-vs-efficiency comparison.",
        ],
    ]
    return """
    <section class="runs-section score-resolution-section">
      <h2>Score Resolution Queue</h2>
      <p class="section-note">Every benchmark run becomes actionable in one of two ways: confirmed with score and run evidence, or quarantined with a recorded rescore, rerun, retire, or role-specific next action. Quarantined evidence remains available for audit but is not unfinished scoring work.</p>
      <p class="section-note"><strong>A draft is a judge recommendation, not a verdict.</strong> You are not expected to rescore the model from scratch. Review whether the evidence is valid, then accept the reviewed result, rerun weak evidence, or reject an invalid artifact.</p>
      <p><a href="/reviews">Open Draft Review Queue</a> to compare independent local judge scores and confirm, edit, or reject drafts.</p>
      {table}
    </section>
    """.format(
        table=_table(
            ["State", "Runs", "Next action"],
            rows,
            table_class="score-resolution-table",
        )
    )


def _score_all_control(unscored_count, enable_score_actions=False, action_token=""):
    if unscored_count <= 0:
        return '<p class="empty">No raw artifacts are awaiting draft scoring.</p>'
    noun = "artifact" if unscored_count == 1 else "artifacts"
    summary = f"{unscored_count} {noun} awaiting draft scoring"
    if not enable_score_actions:
        return (
            '<div class="cell-stack">'
            f'<span class="empty">{_text(summary)}</span>'
            '<button type="button" disabled>Score all unscored artifacts</button>'
            '<div class="empty">Restart with <code>--enable-score-actions</code> and a '
            "configured local judge.</div>"
            "</div>"
        )
    return f"""
    <form class="inline-form" method="post" action="/actions/score-all-unscored">
      <input type="hidden" name="token" value="{_text(action_token)}">
      <button type="submit">Score all unscored artifacts</button>
      <span class="empty">{_text(summary)}</span>
    </form>
    """


def _runs(
    conn,
    query=None,
    database_path=DEFAULT_DASHBOARD_DB,
    registry_path=CANDIDATE_REGISTRY_PATH,
    local_inventory_path=None,
    eval_results_dir=EVAL_RESULTS_DIR,
    enable_import_actions=False,
    enable_score_actions=False,
    action_token="",
    import_sync_result=None,
):
    all_runs = db.list_runs(conn)
    runs = _real_rows(all_runs)
    candidates = _load_radar_candidates(registry_path, local_inventory_path)
    authoritative_groups = _authoritative_run_groups(runs, candidates)
    authoritative_run_ids = {
        group["authoritative_run_id"] for group in authoritative_groups.values()
    }
    task_summary = recommend.task_recommendations(_real_rows(db.list_score_details(conn)))
    filters = _run_filter_values(query or {})
    filtered_runs = _filter_runs(runs, filters)
    frontier_chart, frontier_note = _efficiency_frontier(
        filtered_runs,
        eval_results_dir,
    )
    sorted_runs = _sort_rows(filtered_runs, query or {}, RUN_SORT_COLUMNS)
    grouped = _runs_grouped(query or {})
    if grouped:
        model_runs_table = _grouped_runs_table(sorted_runs, authoritative_groups)
    else:
        run_page = _paginate(sorted_runs, query or {})
        rows = [_run_table_row(row, authoritative_run_ids) for row in run_page.items]
        model_runs_table = _table(
            RUN_TABLE_HEADERS,
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
        ) + _pagination_controls(
            "/runs",
            query or {},
            run_page,
            label="Model runs pagination",
        )
    artifact_rows = []
    dashboard_runs = _dashboard_runs_by_benchmark_id(conn)
    decisions_by_model = _latest_decisions_by_model_id(conn)
    pending_import_count = len(_pending_artifact_run_ids(conn, eval_results_dir))
    artifacts = sorted(
        _artifact_summaries(eval_results_dir),
        key=lambda row: row["benchmark_run_id"],
        reverse=True,
    )
    unscored_artifact_count = sum(
        artifact["raw_responses"] > 0
        and model_roles.model_supports_generation(artifact.get("model_role"))
        and artifact["scores"] != "yes"
        and score_review.review_state(
            Path(eval_results_dir) / artifact["benchmark_run_id"]
        ).get("status")
        != "rejected"
        and (
            not dashboard_runs.get(artifact["benchmark_run_id"])
            or dashboard_runs[artifact["benchmark_run_id"]]["score_status"]
            not in ("draft", "confirmed")
        )
        for artifact in artifacts
    )
    for artifact in artifacts:
        run_id = artifact["benchmark_run_id"]
        review = score_review.review_state(Path(eval_results_dir) / run_id)
        artifact_rows.append(
            [
                _artifact_link(run_id),
                _pill(artifact.get("model_role") or "unknown"),
                _text(artifact["raw_responses"]),
                _text(artifact["scores"]),
                _text(artifact["draft_scores"]),
                _text(artifact["decision"]),
                _text(artifact["dashboard_import"]),
                _import_state_for_run(dashboard_runs.get(run_id), decisions_by_model),
                _text(_artifact_score_state(artifact, review)),
                _artifact_score_control(
                    run_id,
                    enable_score_actions=enable_score_actions,
                    action_token=action_token,
                    eval_results_dir=eval_results_dir,
                ),
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
      <p><a href="/retrieval">Open Retrieval Evaluation</a> for embedding-model recall@k and reranker MRR evidence.</p>
    </section>
    {task_leaders}
    <section class="runs-section efficiency-frontier-section">
      {frontier_panel}
      <p class="section-note">{frontier_note}</p>
    </section>
    {score_resolution_panel}
    <section class="runs-section">
      <h2>Model Runs{filtered_count}</h2>
      <p class="section-note">Model Runs are imported local benchmark run records. A row may have raw performance fields before reviewed scores or keep/watch decisions exist.</p>
      {filters}
      {view_control}
      {table}
    </section>
    <section class="runs-section runs-compare-section">
      {compare_section}
    </section>
    <section class="runs-section runs-artifact-section">
      <h2>Local Artifact Import Queue</h2>
      <p class="section-note">Use this queue for benchmark artifacts already written under <code>data/eval_results</code>. Importing a raw run updates model/run/performance data; labels and stability reports appear only after reviewed score and decision files exist.</p>
      {score_all_control}
      {import_all_control}
      {artifact_table}
    </section>
    """.format(
        import_sync_notice=_import_sync_notice(import_sync_result),
        notice=_real_data_notice(len(_demo_rows(all_runs))),
        task_leaders=_task_leaders(task_summary, surface_class="task-leaders-benchmark"),
        frontier_panel=_chart_panel("Efficiency Frontier", frontier_chart),
        frontier_note=_text(frontier_note),
        score_resolution_panel=_score_resolution_panel(
            filtered_runs,
            eval_results_dir,
        ),
        filters=_runs_filters(runs, filters),
        view_control=_runs_view_control(query or {}, grouped),
        filtered_count=(f" ({len(filtered_runs)} of {len(runs)})" if any(filters.values()) else ""),
        compare_section=(
            _compact_compare_section()
            if grouped and not any(filters.values())
            else _compare_section(
                conn,
                include_notice=False,
                include_filters=False,
                include_deep_link=True,
            )
        ),
        score_all_control=_score_all_control(
            unscored_artifact_count,
            enable_score_actions=enable_score_actions,
            action_token=action_token,
        ),
        import_all_control=_artifact_import_all_control(
            pending_import_count,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
        ),
        table=model_runs_table,
        artifact_table=_table(
            [
                "Artifact",
                "Role",
                "Raw responses",
                "Scores",
                "Draft scores",
                "Decision",
                "Dashboard CSVs",
                "Dashboard state",
                "What import changes",
                "Draft scoring",
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
