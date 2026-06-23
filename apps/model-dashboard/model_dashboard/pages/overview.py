"""Dashboard overview page."""

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

def _overview(conn, query=None):
    counts = _real_counts(conn)
    all_summaries = db.list_model_summaries(conn)
    summaries = _real_rows(all_summaries)
    filters = _filter_values(query or {})
    filtered_summaries = _filter_summaries(summaries, filters)
    score_values = [
        float(row["total_score"]) for row in summaries if row["total_score"] not in (None, "")
    ]
    avg_score = sum(score_values) / len(score_values) if score_values else None
    keep_count = sum(1 for row in summaries if row["keep_installed"] == 1)
    # v3: TTFT/latency once captured.
    score_chart = charts.horizontal_bars(
        [(_model_chart_label(row), row["total_score"]) for row in filtered_summaries],
        value_format="{:.2f}",
        title="Model total scores",
    )
    throughput_chart = charts.horizontal_bars(
        [(_model_chart_label(row), row["tokens_per_sec"]) for row in filtered_summaries],
        value_format="{:.1f} tok/s",
        title="Model throughput",
    )
    ram_chart = charts.horizontal_bars(
        [(_model_chart_label(row), row["ram_usage_gb"]) for row in filtered_summaries],
        value_format="{:.1f} GB",
        title="Model RAM usage",
    )
    rows = []
    for row in filtered_summaries:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["id"], name=_text(row["model_name"])
                ),
                _text(row["provider"]),
                _number(row["params_b"]),
                _text(row["backend"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _number(row["total_score"], 2),
                _status_pill(row["score_status"]),
                _pill(row["final_label"]),
                _text(row["decision"]),
            ]
        )
    body = """
    {notice}
    <section class="grid">
      {models_stat}
      {runs_stat}
      {avg_stat}
      {kept_stat}
    </section>
    <section class="chart-grid" aria-label="Overview charts">
      {score_chart}
      {throughput_chart}
      {ram_chart}
    </section>
    <section>
      {filters}
      <h2>Ranked Local Models{filtered_count}</h2>
      {table}
    </section>
    """.format(
        notice=_real_data_notice(counts["demo_models"]),
        models_stat=_stat_card("Models", counts["models"], "ti-cube"),
        runs_stat=_stat_card("Runs", counts["model_runs"], "ti-player-play"),
        avg_stat=_stat_card("Average score", _number(avg_score, 1, "0.0"), "ti-chart-line"),
        kept_stat=_stat_card("Kept installed", keep_count, "ti-checkup-list"),
        score_chart=_chart_panel("Total Score", score_chart),
        throughput_chart=_chart_panel("Throughput", throughput_chart),
        ram_chart=_chart_panel("RAM Footprint", ram_chart),
        filters=_overview_filters(summaries, filters),
        filtered_count=(
            f" ({len(filtered_summaries)} of {len(summaries)})" if any(filters.values()) else ""
        ),
        table=_table(
            [
                "Model",
                "Provider",
                "Params B",
                "Backend",
                "Tok/s",
                "RAM GB",
                "Score",
                "Status",
                "Label",
                "Decision",
            ],
            rows,
            empty_message="No real benchmark imports yet.",
            table_class="overview-table",
        ),
    )
    return _layout("Overview", "/", body)

__all__ = ('_overview',)
