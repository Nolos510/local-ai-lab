"""Dashboard radar page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path

from .. import capability, charts, db, discover, fit
from ..components import *
from ..filters import *
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS
from ..sorting import _sort_rows, _sortable_headers

CANDIDATE_SORT_COLUMNS = {
    "candidate": (lambda row: row.get("model_name") or row.get("candidate_id"), "text"),
    "status": (lambda row: row.get("status"), "text"),
    "metadata": (
        lambda row: f'{row.get("model_family", "")} {row.get("format_or_runtime", "")}',
        "text",
    ),
    "availability": (lambda row: row.get("runtime_availability"), "text"),
    "review_notes": (
        lambda row: f'{row.get("why_interesting", "")} {row.get("risk_notes", "")}',
        "text",
    ),
    "security": (lambda row: _candidate_security_status(row), "text"),
    "proposed_eval": (lambda row: row.get("proposed_eval"), "text"),
    "links": (
        lambda row: row.get("benchmark_run_id")
        or row.get("source_packet_path")
        or row.get("report_path"),
        "text",
    ),
}
CANDIDATE_SORT_HEADERS = {
    "Candidate": "candidate",
    "Status": "status",
    "Metadata": "metadata",
    "Availability": "availability",
    "Review notes": "review_notes",
    "Security gate": "security",
    "Proposed eval": "proposed_eval",
    "Links": "links",
}


def _upstream_update_control(row, action_token):
    update = row.get("_upstream_update")
    if not isinstance(update, dict) or not update:
        return ""
    changes = []
    old_revision = update.get("previous_revision")
    revision = update.get("revision")
    if old_revision != revision:
        old_revision_text = _text(old_revision or "—")
        revision_text = _text(revision or "—")
        changes.append(
            f"<div><strong>Revision</strong><br><code>{old_revision_text}</code> "
            f"&rarr; <code>{revision_text}</code></div>"
        )
    old_date = update.get("previous_modified_at")
    modified_at = update.get("modified_at")
    if old_date != modified_at:
        old_date_text = _text(old_date or "—")
        modified_at_text = _text(modified_at or "—")
        changes.append(
            f"<div><strong>Observed date</strong><br>{old_date_text} &rarr; "
            f"{modified_at_text}</div>"
        )
    return """
    <div class="upstream-update">
      <span class="pill upstream-update-badge">updated upstream since evaluation</span>
      {changes}
      <form class="inline-form upstream-dismiss-form" method="post" action="/actions/dismiss-upstream-update">
        <input type="hidden" name="token" value="{token}">
        <input type="hidden" name="candidate_id" value="{candidate_id}">
        <button class="secondary" type="submit">Dismiss update</button>
      </form>
    </div>
    """.format(
        changes="".join(changes),
        token=_text(action_token),
        candidate_id=_text(row.get("candidate_id")),
    )


def _candidate_rows(conn, candidates, memory_gb=None, action_token=""):
    model_links = _dashboard_model_links(conn)
    evidence = _dashboard_fit_evidence(conn)
    rows = []
    for row in candidates:
        model_id = model_links.get(row.get("model_name", "").lower())
        candidate_evidence = evidence["by_candidate"].get(row.get("candidate_id", ""), {})
        model_evidence = evidence["by_name"].get(row.get("model_name", "").lower(), {})
        params_b = fit.parse_parameter_count_b(
            row.get("params_b"),
            candidate_evidence.get("params_b"),
            model_evidence.get("params_b"),
            row.get("model_name"),
            row.get("local_model_id"),
        )
        bits = fit.parse_quantization_bits(
            row.get("quantization_bits"),
            row.get("quantization"),
            candidate_evidence.get("quantization"),
            model_evidence.get("quantization"),
            row.get("format_or_runtime"),
            row.get("local_model_id"),
            row.get("model_name"),
        )
        observed_tokens_per_sec = candidate_evidence.get("tokens_per_sec")
        if observed_tokens_per_sec is None:
            observed_tokens_per_sec = model_evidence.get("tokens_per_sec")
        fit_summary = _fit_summary(params_b, bits, memory_gb, observed_tokens_per_sec)
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
                '<div class="cell-stack radar-candidate-identity"><div class="radar-candidate-name">{name}</div><code>{id}</code>{fit_summary}{upstream_update}</div>'.format(
                    name=model_name,
                    id=_text(row.get("candidate_id")),
                    fit_summary=fit_summary,
                    upstream_update=_upstream_update_control(row, action_token),
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
    return rows


def _project_rows(projects):
    rows = []
    for row in projects:
        repo = _external_link_or_text(row.get("repo_url"), row.get("repo_name"))
        identity = '<div class="cell-stack"><div>{repo}</div><code>{owner}</code></div>'.format(
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
    return rows


def _discover_chip_row(default_count, evaluated_count, specialty_count, active_lane, active_view):
    default_active = " active" if not active_lane and active_view != "evaluated" else ""
    evaluated_active = " active" if active_view == "evaluated" else ""
    specialty_active = (
        " active" if active_lane == "specialty" and active_view != "evaluated" else ""
    )
    default_total = _text(default_count)
    evaluated_total = _text(evaluated_count)
    specialty = _text(specialty_count)
    return f"""
    <div class="filter-chip-row" aria-label="Discover quick filters">
      <a class="filter-chip{default_active}" href="/radar">To evaluate <strong>{default_total}</strong></a>
      <a class="filter-chip{evaluated_active}" href="/radar?view=evaluated">Evaluated <strong>{evaluated_total}</strong></a>
      <a class="filter-chip{specialty_active}" href="/radar?lane=specialty">Specialty <strong>{specialty}</strong></a>
      <a class="filter-chip" href="/projects">Project deep view</a>
    </div>
    """


def _project_section(projects):
    ready_count = sum(1 for row in projects if row.get("status") == "ready_for_review")
    local_count = sum(
        1
        for row in projects
        if "local" in row.get("local_fit", "").lower()
        or "self-host" in row.get("local_fit", "").lower()
    )
    return """
    <section class="radar-projects-section">
      <div class="section-heading-row">
        <div>
          <h2>Project Radar</h2>
          <p class="section-note">GitHub and tool opportunities are candidate-only learning and build records. They do not create model eval scores.</p>
        </div>
        <a class="action-link secondary" href="/projects">Open project filters</a>
      </div>
      <section class="grid grid-compact">
        {projects_stat}
        {ready_stat}
        {local_stat}
        {priority_stat}
      </section>
      {table}
    </section>
    """.format(
        projects_stat=_stat_card("Projects", len(projects), "ti-brand-github"),
        ready_stat=_stat_card("Ready for review", ready_count, "ti-list-check"),
        local_stat=_stat_card("Local/self-host signal", local_count, "ti-server"),
        priority_stat=_stat_card(
            "Priority 5",
            sum(1 for row in projects if _project_priority_score(row) == 5),
            "ti-flame",
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
            _project_rows(_filter_projects(projects, {"q": "", "status": "", "category": ""})),
            empty_message="No project radar records found.",
            table_class="project-table",
            scroll_controls=True,
            scroll_id="discover-project-radar-table-scroll",
            scroll_label="Project radar table",
        ),
    )


def _radar(
    conn,
    query=None,
    registry_path=CANDIDATE_REGISTRY_PATH,
    local_inventory_path=None,
    project_registry_path=PROJECT_REGISTRY_PATH,
    upstream_state_path=RADAR_UPSTREAM_STATE_PATH,
    action_token="",
    hardware_profiles_dir=REPO_ROOT / "docs" / "lab-notes",
    current_hardware_profile=None,
    read_current_hardware=False,
):
    candidates = _load_radar_candidates(registry_path, local_inventory_path)
    candidates = discover.candidate_lifecycle_rows(
        conn,
        candidates,
        upstream_state_path,
    )
    projects = _load_project_repos(project_registry_path)
    filters = _radar_filter_values(query or {})
    graduated_candidates = [row for row in candidates if row.get("_graduated")]
    default_candidates = [
        row
        for row in candidates
        if not row.get("_graduated") or row.get("_upstream_update")
    ]
    view_candidates = (
        graduated_candidates
        if filters.get("view") == "evaluated"
        else default_candidates
    )
    filtered_candidates = _filter_candidates(view_candidates, filters)
    sorted_candidates = _sort_rows(
        filtered_candidates,
        query or {},
        CANDIDATE_SORT_COLUMNS,
    )
    evaluated_count = len(graduated_candidates)
    ready_count = sum(1 for row in view_candidates if row.get("status") == "ready_for_eval")
    watchlist_count = sum(1 for row in view_candidates if row.get("status") == "watchlist")
    linked_count = sum(1 for row in view_candidates if row.get("benchmark_run_id"))
    specialty_count = sum(1 for row in default_candidates if _is_specialty_candidate(row))
    security_review_count = sum(
        1
        for row in view_candidates
        if _candidate_security_status(row) in ("needs_review", "unreviewed")
    )
    memory_gb = _fit_memory_gb(
        hardware_profiles_dir,
        current_hardware_profile=current_hardware_profile,
        read_current_hardware=read_current_hardware,
    )
    rows = _candidate_rows(
        conn,
        sorted_candidates,
        memory_gb,
        action_token=action_token,
    )

    body = """
    <section class="panel page-intro radar-intro">
      <p>Models worth evaluating &mdash; from your radar, specialty lanes, and GitHub projects. Approve a candidate to queue it for benchmarking.</p>
      <p class="empty">Discover records are local review metadata only. Evaluated candidates graduate from the default view unless an explicit upstream metadata check finds a newer revision. Dashboard renders never make network calls.</p>
    </section>
    <section class="grid radar-stats-grid">
      {candidates_stat}
      {ready_stat}
      {watchlist_stat}
      {linked_stat}
      {specialty_stat}
      {projects_stat}
      {security_stat}
    </section>
    <section class="panel radar-security-panel">
      <h2>Security Gate</h2>
      <p>Radar links are review metadata only. A candidate is not approved to download, install, update, or run until its source, license, artifact path, and local runtime isolation are reviewed.</p>
    </section>
    <section class="radar-candidates-section">
      <h2>{candidate_heading}{filtered_count}</h2>
      <section class="panel compact-guide radar-guide">
        <h3>What this view shows</h3>
        <p>This table is the local radar intake view: each row is a candidate-only record with source metadata, runtime availability, review notes, and the security/download gates that must clear before any local benchmark run.</p>
        <p class="empty">Use <strong>Status</strong> to find ready or watchlist candidates, <strong>Availability</strong> to confirm LM Studio/Ollama fit, and <strong>Security gate</strong> to see what still blocks download, install, or execution. Benchmark results appear on Home and Benchmark only after a local artifact is imported.</p>
      </section>
      {chips}
      {filters}
      {table}
    </section>
    {projects_section}
    """.format(
        candidates_stat=_stat_card(
            "Evaluated" if filters.get("view") == "evaluated" else "To evaluate",
            len(view_candidates),
            "ti-radar",
        ),
        ready_stat=_stat_card("Ready for eval", ready_count, "ti-list-check"),
        watchlist_stat=_stat_card("Watchlist", watchlist_count, "ti-eye"),
        linked_stat=_stat_card("Linked artifacts", linked_count, "ti-link"),
        specialty_stat=_stat_card("Abliterated / Dolphin", specialty_count, "ti-sparkles"),
        projects_stat=_stat_card("Projects", len(projects), "ti-brand-github"),
        security_stat=_stat_card("Security reviews needed", security_review_count, "ti-shield"),
        chips=_discover_chip_row(
            len(default_candidates),
            evaluated_count,
            specialty_count,
            filters.get("lane"),
            filters.get("view"),
        ),
        filters=_radar_filters(view_candidates, filters),
        candidate_heading=(
            "Evaluated Candidates"
            if filters.get("view") == "evaluated"
            else "Radar Candidates"
        ),
        filtered_count=(
            f" ({len(filtered_candidates)} of {len(view_candidates)})"
            if any(filters.values())
            else ""
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
            scroll_controls=True,
            scroll_id="radar-candidates-table-scroll",
            scroll_label="Radar candidates table",
            sortable_headers=_sortable_headers(
                "/radar",
                query or {},
                CANDIDATE_SORT_HEADERS,
            ),
        ),
        projects_section=_project_section(projects),
    )
    return _layout("Discover", "/radar", body)

__all__ = ('_candidate_rows', '_project_rows', '_radar',)
