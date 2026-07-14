"""Dashboard projects page."""

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

def _projects(query=None, registry_path=PROJECT_REGISTRY_PATH):
    projects = _load_project_repos(registry_path)
    filters = _project_filter_values(query or {})
    filtered_projects = _filter_projects(projects, filters)
    ready_count = sum(1 for row in projects if row.get("status") == "ready_for_review")
    watchlist_count = sum(1 for row in projects if row.get("status") == "watchlist")
    local_count = sum(
        1
        for row in projects
        if "local" in row.get("local_fit", "").lower()
        or "self-host" in row.get("local_fit", "").lower()
    )

    rows = []
    for row in filtered_projects:
        repo = _external_link_or_text(row.get("repo_url"), row.get("repo_name"))
        identity = '<div class="cell-stack project-identity"><div class="project-name">{repo}</div><code>{owner}</code></div>'.format(
            repo=repo,
            owner=_text(row.get("owner")),
        )
        signal = """
        <div class="cell-stack">
          <div><strong>Category</strong><br>{category}</div>
          <div><strong>Stars observed</strong><br>{stars}</div>
          <div><strong>License</strong><br>{license}</div>
        </div>
        """.format(
            category=_text(row.get("category")),
            stars=_text(row.get("stars_observed")),
            license=_text(row.get("license")),
        )
        review = """
        <div class="cell-stack">
          <div><strong>Why learn/use this</strong><br>{priority}</div>
          <div><strong>Why</strong><br>{why}</div>
          <div><strong>Business</strong><br>{business}</div>
          <div><strong>Local fit</strong><br>{local_fit}</div>
          <div><strong>Risk</strong><br>{risk}</div>
        </div>
        """.format(
            priority=_text(row.get("priority_rationale")),
            why=_text(row.get("why_interesting")),
            business=_text(row.get("business_tie_in")),
            local_fit=_text(row.get("local_fit")),
            risk=_text(row.get("risk_notes")),
        )
        links = """
        <div class="cell-stack">
          <div><strong>Source</strong><br>{source}</div>
          <div><strong>Report</strong><br>{report}</div>
        </div>
        """.format(
            source=_path_cell(row.get("source_packet_path")),
            report=_path_cell(row.get("report_path")),
        )
        rows.append(
            [
                identity,
                _pill("P{}".format(_project_priority_score(row) or "?")),
                _pill(row.get("status")),
                signal,
                review,
                _text(row.get("recommended_next_step")),
                links,
            ]
        )

    body = """
    <section class="grid projects-stats-grid">
      {projects_stat}
      {ready_stat}
      {watchlist_stat}
      {local_stat}
      {priority_stat}
    </section>
    <section class="projects-radar-section">
      {filters}
      <h2>Project Radar{filtered_count}</h2>
      {table}
    </section>
    """.format(
        projects_stat=_stat_card("Projects", len(projects), "ti-brand-github"),
        ready_stat=_stat_card("Ready for review", ready_count, "ti-list-check"),
        watchlist_stat=_stat_card("Watchlist", watchlist_count, "ti-eye"),
        local_stat=_stat_card("Local/self-host signal", local_count, "ti-server"),
        priority_stat=_stat_card(
            "Priority 5",
            sum(1 for row in projects if _project_priority_score(row) == 5),
            "ti-flame",
        ),
        filters=_project_filters(projects, filters),
        filtered_count=(
            f" ({len(filtered_projects)} of {len(projects)})" if any(filters.values()) else ""
        ),
        table=_table(
            [
                "Project",
                "Priority",
                "Status",
                "Signal",
                "Why learn / use this",
                "Next step",
                "Links",
            ],
            rows,
            empty_message="No projects match these filters.",
            table_class="project-table",
            scroll_controls=True,
            scroll_id="project-radar-table-scroll",
            scroll_label="Project radar table",
        ),
    )
    return _layout("Project Radar", "/projects", body)

__all__ = ('_projects',)
