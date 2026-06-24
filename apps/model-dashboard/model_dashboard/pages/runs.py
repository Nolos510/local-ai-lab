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

def _runs(conn, query=None):
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
    body = """
    {notice}
    {filters}
    <h2>Model Runs{filtered_count}</h2>
    {table}
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_runs))),
        filters=_runs_filters(runs, filters),
        filtered_count=(f" ({len(filtered_runs)} of {len(runs)})" if any(filters.values()) else ""),
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
    )
    return _layout("Model Runs", "/runs", body)

__all__ = ('_runs',)
