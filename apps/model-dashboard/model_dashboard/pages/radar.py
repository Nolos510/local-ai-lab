"""Dashboard radar page."""

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

def _radar(conn, query=None, registry_path=CANDIDATE_REGISTRY_PATH):
    candidates = _load_radar_candidates(registry_path)
    filters = _radar_filter_values(query or {})
    filtered_candidates = _filter_candidates(candidates, filters)
    model_links = _dashboard_model_links(conn)
    ready_count = sum(1 for row in candidates if row.get("status") == "ready_for_eval")
    watchlist_count = sum(1 for row in candidates if row.get("status") == "watchlist")
    linked_count = sum(1 for row in candidates if row.get("benchmark_run_id"))
    specialty_count = sum(1 for row in candidates if _is_specialty_candidate(row))
    security_review_count = sum(
        1 for row in candidates if _candidate_security_status(row) in ("needs_review", "unreviewed")
    )

    rows = []
    for row in filtered_candidates:
        model_id = model_links.get(row.get("model_name", "").lower())
        model_name = _text(row.get("model_name"))
        if model_id:
            model_name = f'<a href="/models/{model_id}">{model_name}</a>'
        metadata = """
        <div class="cell-stack">
          <div><strong>Family</strong><br>{family}</div>
          <div><strong>Runtime</strong><br>{runtime}</div>
        </div>
        """.format(
            family=_text(row.get("model_family")),
            runtime=_text(row.get("format_or_runtime")),
        )
        context = """
        <div class="cell-stack">
          <div><strong>Why</strong><br>{why}</div>
          <div><strong>Risk</strong><br>{risk}</div>
        </div>
        """.format(
            why=_text(row.get("why_interesting")),
            risk=_text(row.get("risk_notes")),
        )
        links = """
        <div class="cell-stack">
          <div><strong>Benchmark</strong><br>{artifact}</div>
          <div><strong>Source</strong><br>{source}</div>
          <div><strong>Report</strong><br>{report}</div>
        </div>
        """.format(
            artifact=_artifact_link(row.get("benchmark_run_id")),
            source=_path_cell(row.get("source_packet_path")),
            report=_path_cell(row.get("report_path")),
        )
        rows.append(
            [
                '<div class="cell-stack"><div>{name}</div><code>{id}</code></div>'.format(
                    name=model_name,
                    id=_text(row.get("candidate_id")),
                ),
                _pill(row.get("status")),
                metadata,
                _candidate_availability(row),
                context,
                _candidate_security(row),
                _text(row.get("proposed_eval")),
                links,
            ]
        )

    body = """
    <section class="grid">
      {candidates_stat}
      {ready_stat}
      {watchlist_stat}
      {linked_stat}
      {specialty_stat}
      {security_stat}
    </section>
    <section class="panel" style="margin-bottom:16px">
      <h2>Security Gate</h2>
      <p>Radar links are review metadata only. A candidate is not approved to download, install, update, or run until its source, license, artifact path, and local runtime isolation are reviewed.</p>
    </section>
    <section>
      {filters}
      <h2>Radar Candidates{filtered_count}</h2>
      {table}
    </section>
    """.format(
        candidates_stat=_stat_card("Candidates", len(candidates), "ti-radar"),
        ready_stat=_stat_card("Ready for eval", ready_count, "ti-list-check"),
        watchlist_stat=_stat_card("Watchlist", watchlist_count, "ti-eye"),
        linked_stat=_stat_card("Linked artifacts", linked_count, "ti-link"),
        specialty_stat=_stat_card("Abliterated / Dolphin", specialty_count, "ti-sparkles"),
        security_stat=_stat_card("Security reviews needed", security_review_count, "ti-shield"),
        filters=_radar_filters(candidates, filters),
        filtered_count=(
            f" ({len(filtered_candidates)} of {len(candidates)})" if any(filters.values()) else ""
        ),
        table=_table(
            [
                "Candidate",
                "Status",
                "Metadata",
                "Availability",
                "Review notes",
                "Security gate",
                "Proposed eval",
                "Links",
            ],
            rows,
            empty_message="No candidates match these filters.",
            table_class="radar-table",
        ),
    )
    return _layout("Radar Candidates", "/radar", body)

__all__ = ('_radar',)
