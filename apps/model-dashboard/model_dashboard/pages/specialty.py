"""Dashboard specialty page."""

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

def _specialty(conn, query=None, registry_path=CANDIDATE_REGISTRY_PATH):
    candidates = [
        row for row in _load_radar_candidates(registry_path) if _is_specialty_candidate(row)
    ]
    filters = _specialty_filter_values(query or {})
    filtered_candidates = _filter_specialty_candidates(candidates, filters)
    model_links = _dashboard_model_links(conn)
    ready_count = sum(1 for row in candidates if row.get("status") == "ready_for_eval")
    watchlist_count = sum(1 for row in candidates if row.get("status") == "watchlist")
    security_review_count = sum(
        1 for row in candidates if _candidate_security_status(row) in ("needs_review", "unreviewed")
    )

    rows = []
    for row in filtered_candidates:
        model_id = model_links.get(row.get("model_name", "").lower())
        model_name = _text(row.get("model_name"))
        if model_id:
            model_name = f'<a href="/models/{model_id}">{model_name}</a>'
        rows.append(
            [
                '<div class="cell-stack"><div>{name}</div><code>{id}</code></div>'.format(
                    name=model_name,
                    id=_text(row.get("candidate_id")),
                ),
                '<div class="cell-stack"><div>{lane}</div>{status}</div>'.format(
                    lane=_text(_specialty_lane_label(row)),
                    status=_pill(row.get("status")),
                ),
                _candidate_availability(row),
                """
                <div class="cell-stack">
                  <div><strong>Why</strong><br>{why}</div>
                  <div><strong>Risk</strong><br>{risk}</div>
                </div>
                """.format(
                    why=_text(row.get("why_interesting")),
                    risk=_text(row.get("risk_notes")),
                ),
                _candidate_security(row),
                _text(row.get("proposed_eval")),
                _artifact_link(row.get("benchmark_run_id")),
            ]
        )

    body = """
    <section class="grid">
      {total_stat}
      {ready_stat}
      {watchlist_stat}
      {security_stat}
    </section>
    <section class="panel" style="margin-bottom:16px">
      <h2>Abliterated / Dolphin Models</h2>
      <p>This tab collects specialty radar candidates for refusal-boundary and Dolphin-style model testing. They remain candidates until local evidence, scores, and decisions exist.</p>
      <p>Low-refusal or uncensored claims are not safety approval. Download and runtime approval stay blocked until the security gate is reviewed.</p>
      <p>The same rows remain searchable in <a href="/radar?q=abliterated">Radar Candidates</a>.</p>
    </section>
    {filters}
    <h2>Specialty Candidates{filtered_count}</h2>
    {table}
    """.format(
        total_stat=_stat_card("Specialty candidates", len(candidates), "ti-sparkles"),
        ready_stat=_stat_card("Ready for eval", ready_count, "ti-list-check"),
        watchlist_stat=_stat_card("Watchlist", watchlist_count, "ti-eye"),
        security_stat=_stat_card("Security reviews needed", security_review_count, "ti-shield"),
        filters=_specialty_filters(candidates, filters),
        filtered_count=(
            f" ({len(filtered_candidates)} of {len(candidates)})" if any(filters.values()) else ""
        ),
        table=_table(
            [
                "Candidate",
                "Lane",
                "Availability",
                "Review notes",
                "Security gate",
                "Proposed eval",
                "Artifact",
            ],
            rows,
            empty_message="No abliterated or Dolphin candidates match these filters.",
            table_class="radar-table",
        ),
    )
    return _layout("Specialty Models", "/specialty", body)

__all__ = ('_specialty',)
