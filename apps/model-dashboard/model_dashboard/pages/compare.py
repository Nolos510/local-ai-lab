"""Dashboard compare page."""

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


def _compare_section(
    conn,
    query=None,
    *,
    include_notice=True,
    include_filters=True,
    include_deep_link=False,
):
    headers = ["Model", "Score", "Status", "Label"] + [
        field.replace("_", " ").title() for field in METRIC_FIELDS
    ]
    rows = []
    all_scores = db.list_score_details(conn)
    scores = _real_rows(all_scores)
    filters = _score_filter_values(query or {})
    filtered_scores = _filter_scores(scores, filters)
    score_chart = charts.horizontal_bars(
        [(_model_chart_label(row), row["total_score"]) for row in filtered_scores],
        value_format="{:.2f}",
        max_value=100,
        title="Compare total scores",
    )
    dimension_chart = charts.horizontal_bars(
        _average_metric_items(filtered_scores),
        value_format="{:.1f}",
        max_value=100,
        title="Average score dimensions",
    )
    tokens_chart = _performance_chart(
        filtered_scores,
        "tokens_per_sec",
        "Tokens per second",
        "{:.1f} tok/s",
        "No tokens/sec values imported yet",
    )
    ttft_chart = _performance_chart(
        filtered_scores,
        "ttft_seconds",
        "TTFT seconds",
        "{:.2f}s",
        "No TTFT values imported yet",
    )
    latency_chart = _performance_chart(
        filtered_scores,
        "total_latency_seconds",
        "Total latency seconds",
        "{:.2f}s",
        "No total latency values imported yet",
    )
    for row in filtered_scores:
        cells = [
            '<a href="/models/{id}">{name}</a>'.format(
                id=row["model_id"], name=_text(row["model_name"])
            ),
            _number(row["total_score"], 2),
            _status_pill(row["score_status"]),
            _pill(row["final_label"]),
        ]
        cells.extend(_number(row[field], 0) for field in METRIC_FIELDS)
        rows.append(cells)
    heading = """
    <div class="section-heading-row">
      <div>
        <h2>Compare Models{filtered_count}</h2>
        <p class="section-note">Compare imported local benchmark scores side by side. Higher total score and throughput are better; lower latency is better when latency fields exist.</p>
      </div>
      {deep_link}
    </div>
    """.format(
        filtered_count=(
            f" ({len(filtered_scores)} of {len(scores)})" if any(filters.values()) else ""
        ),
        deep_link=(
            '<a class="action-link secondary" href="/compare">Open compare filters</a>'
            if include_deep_link
            else ""
        ),
    )
    return """
    {notice}
    {filters}
    {heading}
    <section class="chart-grid" aria-label="Compare charts">
      {score_chart}
      {dimension_chart}
    </section>
    {table}
    <section style="margin-top:16px">
      <h2>Performance Signals</h2>
      <p class="empty">Latency values come from approved local benchmark artifacts when imported; lower latency is better, higher tokens/sec is better.</p>
      <div class="chart-grid" aria-label="Compare performance charts">
        {tokens_chart}
        {ttft_chart}
        {latency_chart}
      </div>
    </section>
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_scores))) if include_notice else "",
        filters=_compare_filters(scores, filters) if include_filters else "",
        heading=heading,
        score_chart=_chart_panel("Total Score", score_chart),
        dimension_chart=_chart_panel("Dimension Averages", dimension_chart),
        tokens_chart=_chart_panel("Tokens / Sec", tokens_chart),
        ttft_chart=_chart_panel("TTFT", ttft_chart),
        latency_chart=_chart_panel("Total Latency", latency_chart),
        table=_table(
            headers,
            rows,
            empty_message="No real confirmed or draft score rows match these filters.",
            table_class="compare-table",
            scroll_controls=True,
            scroll_id="compare-models-table-scroll",
            scroll_label="Compare models table",
            header_tip_keys=RESULT_TABLE_HEADER_TIPS,
        ),
    )


def _compare(conn, query=None):
    body = _compare_section(conn, query)
    return _layout("Compare Models", "/compare", body)

__all__ = ('_compare', '_compare_section')
