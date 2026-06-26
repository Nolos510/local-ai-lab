"""Dashboard filter parsing, matching, and filter form renderers."""

# ruff: noqa: E501,F403,F405
from __future__ import annotations

from .components import *

SPECIALTY_LANE_TERMS = ("abliterated", "dolphin")

def _query_value(query, key):
    value = query.get(key, "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _option(value, label, selected):
    selected_attr = " selected" if value == selected else ""
    return f'<option value="{_text(value)}"{selected_attr}>{_text(label)}</option>'


def _field_options(rows, field):
    values = {str(row[field]) for row in rows if row[field] not in (None, "")}
    return sorted(values, key=lambda value: value.lower())


def _filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "label": _query_value(query, "label"),
        "decision": _query_value(query, "decision"),
        "keep": _query_value(query, "keep"),
    }


def _matches_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        str(row[field] or "")
        for field in (
            "model_name",
            "model_family",
            "provider",
            "backend",
            "quantization",
            "final_label",
            "decision",
            "best_use_case",
        )
    )
    return search.lower() in haystack.lower()


def _radar_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "status": _query_value(query, "status"),
        "family": _query_value(query, "family"),
        "runtime": _query_value(query, "runtime"),
        "security": _query_value(query, "security"),
        "lane": _query_value(query, "lane"),
    }


def _matches_candidate_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        row.get(field, "")
        for field in (
            "candidate_id",
            "model_name",
            "model_family",
            "provider_or_org",
            "status",
            "format_or_runtime",
            "why_interesting",
            "risk_notes",
            "proposed_eval",
            "benchmark_run_id",
            "model_page_url",
            "github_url",
            "lm_studio_url",
            "ollama_url",
            "runtime_availability",
            "security_review_status",
            "download_approval",
            "license_review_status",
            "provenance_status",
            "security_notes",
            "isolation_notes",
            "security_review_path",
        )
    )
    return search.lower() in haystack.lower()


def _filter_candidates(candidates, filters):
    filtered = []
    for row in candidates:
        if filters.get("lane") == "specialty" and not _is_specialty_candidate(row):
            continue
        if filters["status"] and row.get("status") != filters["status"]:
            continue
        if filters["family"] and row.get("model_family") != filters["family"]:
            continue
        if filters["runtime"] and row.get("format_or_runtime") != filters["runtime"]:
            continue
        if filters["security"] and _candidate_security_status(row) != filters["security"]:
            continue
        if not _matches_candidate_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _project_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "status": _query_value(query, "status"),
        "category": _query_value(query, "category"),
    }


def _matches_project_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        row.get(field, "")
        for field in (
            "repo_id",
            "repo_name",
            "owner",
            "category",
            "status",
            "why_interesting",
            "business_tie_in",
            "local_fit",
            "risk_notes",
            "priority_score",
            "priority_rationale",
            "recommended_next_step",
        )
    )
    return search.lower() in haystack.lower()


def _project_priority_score(row):
    try:
        return max(1, min(5, int(row.get("priority_score", "0") or 0)))
    except ValueError:
        return 0


def _project_status_rank(row):
    ranks = {
        "ready_for_review": 0,
        "ready_for_eval": 1,
        "watchlist": 2,
        "needs_more_info": 3,
        "skip": 4,
    }
    return ranks.get(row.get("status", ""), 9)


def _project_stars_value(row):
    raw = str(row.get("stars_observed", "")).strip().lower().replace(",", "")
    if not raw:
        return 0.0
    multiplier = 1.0
    if raw.endswith("k"):
        multiplier = 1000.0
        raw = raw[:-1]
    elif raw.endswith("m"):
        multiplier = 1000000.0
        raw = raw[:-1]
    try:
        return float(raw) * multiplier
    except ValueError:
        return 0.0


def _project_sort_key(row):
    return (
        -_project_priority_score(row),
        _project_status_rank(row),
        -_project_stars_value(row),
        row.get("repo_name", "").lower(),
    )


def _filter_projects(projects, filters):
    filtered = []
    for row in projects:
        if filters["status"] and row.get("status") != filters["status"]:
            continue
        if filters["category"] and row.get("category") != filters["category"]:
            continue
        if not _matches_project_search(row, filters["q"]):
            continue
        filtered.append(row)
    return sorted(filtered, key=_project_sort_key)


def _is_specialty_candidate(row):
    haystack = " ".join(
        row.get(field, "")
        for field in (
            "candidate_id",
            "model_name",
            "model_family",
            "provider_or_org",
            "why_interesting",
            "risk_notes",
            "proposed_eval",
        )
    ).lower()
    return any(term in haystack for term in SPECIALTY_LANE_TERMS)


def _specialty_lane_label(row):
    haystack = " ".join(
        row.get(field, "") for field in ("candidate_id", "model_name", "model_family")
    ).lower()
    labels = []
    if "abliterated" in haystack:
        labels.append("Abliterated")
    if "dolphin" in haystack:
        labels.append("Dolphin")
    return " / ".join(labels) if labels else "Specialty"


def _radar_filters(candidates, filters):
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in _field_options(candidates, "status")
    )
    family_options = "".join(
        _option(family, family, filters["family"])
        for family in _field_options(candidates, "model_family")
    )
    runtime_options = "".join(
        _option(runtime, runtime, filters["runtime"])
        for runtime in _field_options(candidates, "format_or_runtime")
    )
    security_options = "".join(
        _option(security, security, filters["security"])
        for security in sorted(
            {_candidate_security_status(row) for row in candidates},
            key=lambda value: value.lower(),
        )
    )
    clear_link = '<a class="clear-link" href="/radar">Clear</a>' if any(filters.values()) else ""
    lane_input = (
        f'<input type="hidden" name="lane" value="{_text(filters.get("lane", ""))}">'
        if filters.get("lane")
        else ""
    )
    return """
    <form class="filters filters-wide" method="get" action="/radar">
      {lane_input}
      <div class="field field-wide">
        <label for="radar-q">Search</label>
        <input id="radar-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="radar-status">Status</label>
        <select id="radar-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="field">
        <label for="radar-family">Family</label>
        <select id="radar-family" name="family">
          {all_families}
          {family_options}
        </select>
      </div>
      <div class="field">
        <label for="radar-runtime">Runtime</label>
        <select id="radar-runtime" name="runtime">
          {all_runtimes}
          {runtime_options}
        </select>
      </div>
      <div class="field">
        <label for="radar-security">Security</label>
        <select id="radar-security" name="security">
          {all_security}
          {security_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        all_families=_option("", "All families", filters["family"]),
        family_options=family_options,
        all_runtimes=_option("", "All runtimes", filters["runtime"]),
        runtime_options=runtime_options,
        all_security=_option("", "All security states", filters["security"]),
        security_options=security_options,
        lane_input=lane_input,
        clear_link=clear_link,
    )


def _project_filters(projects, filters):
    status_options = "".join(
        _option(status, status, filters["status"]) for status in _field_options(projects, "status")
    )
    category_options = "".join(
        _option(category, category, filters["category"])
        for category in _field_options(projects, "category")
    )
    clear_link = '<a class="clear-link" href="/projects">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters filters-compact" method="get" action="/projects">
      <div class="field field-wide">
        <label for="project-q">Search</label>
        <input id="project-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="project-status">Status</label>
        <select id="project-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="field">
        <label for="project-category">Category</label>
        <select id="project-category" name="category">
          {all_categories}
          {category_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        all_categories=_option("", "All categories", filters["category"]),
        category_options=category_options,
        clear_link=clear_link,
    )


def _specialty_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "status": _query_value(query, "status"),
        "lane": _query_value(query, "lane"),
        "security": _query_value(query, "security"),
    }


def _filter_specialty_candidates(candidates, filters):
    filtered = []
    for row in candidates:
        if filters["status"] and row.get("status") != filters["status"]:
            continue
        if filters["lane"] and _specialty_lane_label(row) != filters["lane"]:
            continue
        if filters["security"] and _candidate_security_status(row) != filters["security"]:
            continue
        if not _matches_candidate_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _specialty_filters(candidates, filters):
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in _field_options(candidates, "status")
    )
    lane_options = "".join(
        _option(lane, lane, filters["lane"])
        for lane in sorted(
            {_specialty_lane_label(row) for row in candidates},
            key=lambda value: value.lower(),
        )
    )
    security_options = "".join(
        _option(security, security, filters["security"])
        for security in sorted(
            {_candidate_security_status(row) for row in candidates},
            key=lambda value: value.lower(),
        )
    )
    clear_link = (
        '<a class="clear-link" href="/specialty">Clear</a>' if any(filters.values()) else ""
    )
    return """
    <form class="filters" method="get" action="/specialty">
      <div class="field field-wide">
        <label for="specialty-q">Search</label>
        <input id="specialty-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="specialty-status">Status</label>
        <select id="specialty-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="field">
        <label for="specialty-lane">Lane</label>
        <select id="specialty-lane" name="lane">
          {all_lanes}
          {lane_options}
        </select>
      </div>
      <div class="field">
        <label for="specialty-security">Security</label>
        <select id="specialty-security" name="security">
          {all_security}
          {security_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        all_lanes=_option("", "All lanes", filters["lane"]),
        lane_options=lane_options,
        all_security=_option("", "All security states", filters["security"]),
        security_options=security_options,
        clear_link=clear_link,
    )


def _filter_summaries(rows, filters):
    filtered = []
    for row in rows:
        if filters["label"] and row["final_label"] != filters["label"]:
            continue
        if filters["decision"] and row["decision"] != filters["decision"]:
            continue
        if filters["keep"] == "yes" and row["keep_installed"] != 1:
            continue
        if filters["keep"] == "no" and row["keep_installed"] != 0:
            continue
        if not _matches_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _run_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "backend": _query_value(query, "backend"),
        "label": _query_value(query, "label"),
        "status": _query_value(query, "status"),
    }


def _matches_run_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        str(row[field] or "")
        for field in (
            "model_name",
            "model_family",
            "provider",
            "backend",
            "format",
            "quantization",
            "final_label",
            "score_status",
            "stability_notes",
            "run_notes",
        )
    )
    return search.lower() in haystack.lower()


def _filter_runs(rows, filters):
    filtered = []
    for row in rows:
        if filters["backend"] and row["backend"] != filters["backend"]:
            continue
        if filters["label"] and row["final_label"] != filters["label"]:
            continue
        if filters["status"] and row["score_status"] != filters["status"]:
            continue
        if not _matches_run_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _score_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "label": _query_value(query, "label"),
        "status": _query_value(query, "status"),
    }


def _matches_score_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        str(row[field] or "")
        for field in (
            "model_name",
            "provider",
            "backend",
            "quantization",
            "final_label",
            "score_status",
        )
    )
    return search.lower() in haystack.lower()


def _filter_scores(rows, filters):
    filtered = []
    for row in rows:
        if filters["label"] and row["final_label"] != filters["label"]:
            continue
        if filters["status"] and row["score_status"] != filters["status"]:
            continue
        if not _matches_score_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _storage_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "decision": _query_value(query, "decision"),
        "keep": _query_value(query, "keep"),
    }


def _matches_storage_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        str(row[field] or "")
        for field in (
            "model_name",
            "model_family",
            "provider",
            "decision",
            "best_use_case",
            "weakness",
            "retest_condition",
        )
    )
    return search.lower() in haystack.lower()


def _filter_storage_decisions(rows, filters):
    filtered = []
    for row in rows:
        if filters["decision"] and row["decision"] != filters["decision"]:
            continue
        if filters["keep"] == "yes" and row["keep_installed"] != 1:
            continue
        if filters["keep"] == "no" and row["keep_installed"] != 0:
            continue
        if not _matches_storage_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _overview_filters(rows, filters):
    label_options = "".join(
        _option(label, label, filters["label"]) for label in _field_options(rows, "final_label")
    )
    decision_options = "".join(
        _option(decision, decision, filters["decision"])
        for decision in _field_options(rows, "decision")
    )
    clear_link = '<a class="clear-link" href="/">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters" method="get" action="/">
      <div class="field field-wide">
        <label for="filter-q">Search</label>
        <input id="filter-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="filter-label">Label</label>
        <select id="filter-label" name="label">
          {all_labels}
          {label_options}
        </select>
      </div>
      <div class="field">
        <label for="filter-decision">Decision</label>
        <select id="filter-decision" name="decision">
          {all_decisions}
          {decision_options}
        </select>
      </div>
      <div class="field">
        <label for="filter-keep">Install</label>
        <select id="filter-keep" name="keep">
          {any_keep}
          {keep_yes}
          {keep_no}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_labels=_option("", "All labels", filters["label"]),
        label_options=label_options,
        all_decisions=_option("", "All decisions", filters["decision"]),
        decision_options=decision_options,
        any_keep=_option("", "Any", filters["keep"]),
        keep_yes=_option("yes", "Keep", filters["keep"]),
        keep_no=_option("no", "Not kept", filters["keep"]),
        clear_link=clear_link,
    )


def _runs_filters(rows, filters):
    backend_options = "".join(
        _option(backend, backend, filters["backend"]) for backend in _field_options(rows, "backend")
    )
    label_options = "".join(
        _option(label, label, filters["label"]) for label in _field_options(rows, "final_label")
    )
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in _field_options(rows, "score_status")
    )
    clear_link = '<a class="clear-link" href="/runs">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters" method="get" action="/runs">
      <div class="field field-wide">
        <label for="runs-q">Search</label>
        <input id="runs-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="runs-backend">Backend</label>
        <select id="runs-backend" name="backend">
          {all_backends}
          {backend_options}
        </select>
      </div>
      <div class="field">
        <label for="runs-label">Label</label>
        <select id="runs-label" name="label">
          {all_labels}
          {label_options}
        </select>
      </div>
      <div class="field">
        <label for="runs-status">Score status</label>
        <select id="runs-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_backends=_option("", "All backends", filters["backend"]),
        backend_options=backend_options,
        all_labels=_option("", "All labels", filters["label"]),
        label_options=label_options,
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        clear_link=clear_link,
    )


def _compare_filters(rows, filters):
    label_options = "".join(
        _option(label, label, filters["label"]) for label in _field_options(rows, "final_label")
    )
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in _field_options(rows, "score_status")
    )
    clear_link = '<a class="clear-link" href="/compare">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters filters-compact" method="get" action="/compare">
      <div class="field field-wide">
        <label for="compare-q">Search</label>
        <input id="compare-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="compare-label">Label</label>
        <select id="compare-label" name="label">
          {all_labels}
          {label_options}
        </select>
      </div>
      <div class="field">
        <label for="compare-status">Score status</label>
        <select id="compare-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_labels=_option("", "All labels", filters["label"]),
        label_options=label_options,
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        clear_link=clear_link,
    )


def _storage_filters(rows, filters):
    decision_options = "".join(
        _option(decision, decision, filters["decision"])
        for decision in _field_options(rows, "decision")
    )
    clear_link = '<a class="clear-link" href="/storage">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters filters-compact" method="get" action="/storage">
      <div class="field field-wide">
        <label for="storage-q">Search</label>
        <input id="storage-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="storage-decision">Decision</label>
        <select id="storage-decision" name="decision">
          {all_decisions}
          {decision_options}
        </select>
      </div>
      <div class="field">
        <label for="storage-keep">Keep installed</label>
        <select id="storage-keep" name="keep">
          {any_keep}
          {keep_yes}
          {keep_no}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_decisions=_option("", "All decisions", filters["decision"]),
        decision_options=decision_options,
        any_keep=_option("", "Any", filters["keep"]),
        keep_yes=_option("yes", "Yes", filters["keep"]),
        keep_no=_option("no", "No", filters["keep"]),
        clear_link=clear_link,
    )

__all__ = ('_query_value', '_option', '_field_options', '_filter_values', '_matches_search', '_radar_filter_values', '_matches_candidate_search', '_filter_candidates', '_project_filter_values', '_matches_project_search', '_project_priority_score', '_project_status_rank', '_project_stars_value', '_project_sort_key', '_filter_projects', '_is_specialty_candidate', '_specialty_lane_label', '_radar_filters', '_project_filters', '_specialty_filter_values', '_filter_specialty_candidates', '_specialty_filters', '_filter_summaries', '_run_filter_values', '_matches_run_search', '_filter_runs', '_score_filter_values', '_matches_score_search', '_filter_scores', '_storage_filter_values', '_matches_storage_search', '_filter_storage_decisions', '_overview_filters', '_runs_filters', '_compare_filters', '_storage_filters', 'SPECIALTY_LANE_TERMS')
