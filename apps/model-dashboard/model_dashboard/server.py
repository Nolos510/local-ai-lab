"""A dependency-free local web dashboard for model eval results."""

import csv
import ipaddress
import json
import secrets
import shlex
import shutil
import subprocess
import sys
from datetime import date, datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import csv_io, db
from .reports import generate_markdown_report
from .scoring import METRIC_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_REGISTRY_PATH = REPO_ROOT / "data" / "model_registry" / "candidates.csv"
PROJECT_REGISTRY_PATH = REPO_ROOT / "data" / "project_registry" / "github_repos.csv"
EVAL_RESULTS_DIR = REPO_ROOT / "data" / "eval_results"
HARNESS_PATH = REPO_ROOT / "evals" / "local-llm-benchmark" / "harness.py"
DEFAULT_DASHBOARD_DB = REPO_ROOT / "data" / "dashboard" / "model_dashboard.sqlite"
LMSTUDIO_MODELS_ROOT = Path.home() / ".lmstudio" / "models"
SPECIALTY_LANE_TERMS = ("abliterated", "dolphin")
SUPPORTED_LOCAL_RUNNERS = {
    "lmstudio-cli": "LM Studio CLI",
    "openai-compatible": "OpenAI-compatible local endpoint",
}

NAV_ITEMS = (
    ("/lab", "Lab Dashboard"),
    ("/", "Overview"),
    ("/runs", "Model Runs"),
    ("/compare", "Compare Models"),
    ("/inventory", "Installed Models"),
    ("/radar", "Radar Candidates"),
    ("/specialty", "Specialty Models"),
    ("/projects", "Project Radar"),
    ("/storage", "Storage / Install Status"),
    ("/reports", "Reports"),
)

NAV_ICONS = {
    "/lab": "ti-layout-dashboard",
    "/": "ti-chart-bar",
    "/runs": "ti-player-play",
    "/compare": "ti-git-compare",
    "/inventory": "ti-device-desktop-analytics",
    "/radar": "ti-radar",
    "/specialty": "ti-sparkles",
    "/projects": "ti-brand-github",
    "/storage": "ti-database",
    "/reports": "ti-file-analytics",
}


def _text(value, fallback=""):
    return escape(fallback if value is None else str(value))


def _number(value, digits=1, fallback=""):
    if value is None:
        return fallback
    return "{:.{}f}".format(float(value), digits)


def _pill(value):
    label = _text(value, "UNLABELED")
    return f'<span class="pill">{label}</span>'


def _status_pill(value):
    status = value or "confirmed"
    class_name = "pill score-status"
    if status == "draft":
        class_name += " draft"
    return f'<span class="{class_name}">{_text(status.upper())}</span>'


def _stat_card(label, value, icon):
    return (
        '<div class="stat">'
        f'<i class="ti {_text(icon)}" aria-hidden="true"></i>'
        f'<div><div class="label">{_text(label)}</div><div class="value">{_text(value)}</div></div>'
        "</div>"
    )


def _table(headers, rows, empty_message="No rows yet.", table_class=""):
    if not rows:
        return f'<p class="empty">{escape(empty_message)}</p>'
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = []
    for row in rows:
        row_html.append("<tr>{}</tr>".format("".join(f"<td>{cell}</td>" for cell in row)))
    class_attr = f' class="{escape(table_class)}"' if table_class else ""
    table = "<table{}><thead><tr>{}</tr></thead><tbody>{}</tbody></table>".format(
        class_attr, header_html, "".join(row_html)
    )
    return f'<div class="table-wrap">{table}</div>'


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


def _is_demo_row(row):
    keys = row.keys()
    provider = str(row["provider"] if "provider" in keys else row.get("provider", "") or "")
    source_url = str(row["source_url"] if "source_url" in keys else row.get("source_url", "") or "")
    return provider == "Local Fixture" or source_url.startswith("local-registry://")


def _real_rows(rows):
    return [row for row in rows if not _is_demo_row(row)]


def _demo_rows(rows):
    return [row for row in rows if _is_demo_row(row)]


def _real_counts(conn):
    summaries = db.list_model_summaries(conn)
    runs = db.list_runs(conn)
    scores = db.list_score_details(conn)
    decisions = db.list_decisions(conn)
    return {
        "models": len(_real_rows(summaries)),
        "model_runs": len(_real_rows(runs)),
        "eval_scores": len(_real_rows(scores)),
        "decisions": len(_real_rows(decisions)),
        "demo_models": len(_demo_rows(summaries)),
    }


def _real_data_notice(demo_count):
    if demo_count <= 0:
        return ""
    return f"""
    <section class="panel" style="margin-bottom:16px">
      <h2>Real Data View</h2>
      <p>This page hides {demo_count} demo fixture model rows. Demo rows are examples for dashboard testing, not installed models.</p>
      <p><a href="/demo">View demo data</a> when you want to inspect fixture examples.</p>
    </section>
    """


def _load_radar_candidates(path=CANDIDATE_REGISTRY_PATH):
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def _load_project_repos(path=PROJECT_REGISTRY_PATH):
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def _radar_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "status": _query_value(query, "status"),
        "family": _query_value(query, "family"),
        "runtime": _query_value(query, "runtime"),
        "security": _query_value(query, "security"),
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
    return """
    <form class="filters filters-wide" method="get" action="/radar">
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


def _path_cell(value):
    if not value:
        return '<span class="empty">None</span>'
    return f"<code>{_text(value)}</code>"


def _external_link(url, label):
    value = str(url or "").strip()
    if not value:
        return '<span class="empty">None</span>'
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        return '<span class="empty">Unsupported link</span>'
    return f'<a href="{_text(value)}" target="_blank" rel="noreferrer">{_text(label)}</a>'


def _candidate_review_links(row):
    links = []
    for field, label in (
        ("model_page_url", "Model/source page"),
        ("github_url", "GitHub"),
        ("lm_studio_url", "LM Studio"),
        ("ollama_url", "Ollama"),
    ):
        if row.get(field):
            links.append(f"<div>{_external_link(row.get(field), label)}</div>")
    if not links:
        return '<span class="empty">No verified model/store links</span>'
    return "".join(links)


def _candidate_availability(row):
    runtime = row.get("runtime_availability") or row.get("format_or_runtime") or "unknown"
    return f"""
    <div class="cell-stack">
      <div><strong>Runtime availability</strong><br>{_text(runtime)}</div>
      <div><strong>Model/store links</strong><br>{_candidate_review_links(row)}</div>
    </div>
    """


def _candidate_security_status(row):
    return row.get("security_review_status") or "unreviewed"


def _candidate_security(row):
    status = _candidate_security_status(row)
    approval = row.get("download_approval") or "not_approved"
    license_status = row.get("license_review_status") or "unknown"
    provenance = row.get("provenance_status") or "unverified"
    notes = row.get("security_notes") or "No security review notes recorded."
    isolation = (
        row.get("isolation_notes")
        or "Use local runtimes only; do not run untrusted install scripts."
    )
    review_path = row.get("security_review_path")
    return f"""
    <div class="cell-stack">
      <div><strong>Review</strong><br>{_pill(status)}</div>
      <div><strong>Download</strong><br>{_text(approval)}</div>
      <div><strong>License / provenance</strong><br>{_text(license_status)} / {_text(provenance)}</div>
      <div><strong>Review artifact</strong><br>{_path_cell(review_path)}</div>
      <div><strong>Notes</strong><br>{_text(notes)}</div>
      <div><strong>Isolation</strong><br>{_text(isolation)}</div>
    </div>
    """


def _slug(value):
    slug = []
    previous_dash = False
    for char in str(value or "").lower():
        if char.isalnum():
            slug.append(char)
            previous_dash = False
        elif not previous_dash:
            slug.append("-")
            previous_dash = True
    return "".join(slug).strip("-")[:96] or "local-model"


def _candidate_runner_label(row):
    runner = row.get("local_runner", "")
    return SUPPORTED_LOCAL_RUNNERS.get(runner, runner or "not configured")


def _candidate_run_ready(row):
    runner = row.get("local_runner", "")
    model_id = row.get("local_model_id", "")
    if runner == "lmstudio-cli":
        return bool(model_id)
    if runner == "openai-compatible":
        return bool(row.get("default_endpoint") and (model_id or row.get("model_name")))
    return False


def _run_test_control(row, enable_run_tests=False, action_token=""):
    if not _candidate_run_ready(row):
        return (
            '<span class="empty">Needs exact local model id</span>'
            f'<div class="empty">Runner: {_text(_candidate_runner_label(row))}</div>'
        )
    if not enable_run_tests:
        return (
            '<div class="cell-stack">'
            '<span class="empty">Run button disabled</span>'
            "<div>Restart with <code>--enable-run-tests</code></div>"
            "<div><strong>Runner</strong><br>{runner}</div>"
            "<div><strong>Model id</strong><br><code>{model_id}</code></div>"
            "</div>"
        ).format(
            runner=_text(_candidate_runner_label(row)),
            model_id=_text(row.get("local_model_id") or row.get("model_name")),
        )
    return """
    <form class="inline-form" method="post" action="/actions/run-test">
      <input type="hidden" name="token" value="{token}">
      <input type="hidden" name="candidate_id" value="{candidate_id}">
      <button type="submit">Run Test</button>
      <div class="empty">Runner: {runner}</div>
      <div><code>{model_id}</code></div>
    </form>
    """.format(
        token=_text(action_token),
        candidate_id=_text(row.get("candidate_id")),
        runner=_text(_candidate_runner_label(row)),
        model_id=_text(row.get("local_model_id") or row.get("model_name")),
    )


def _next_dashboard_run_id(row, eval_results_dir=EVAL_RESULTS_DIR):
    base = "{}-{}-dashboard-test".format(
        date.today().strftime("%Y%m%d"),
        _slug(row.get("model_name") or row.get("candidate_id")),
    )
    root = Path(eval_results_dir)
    candidate = base
    index = 2
    while (root / candidate).exists():
        candidate = f"{base}-r{index}"
        index += 1
    return candidate


def _append_arg(command, flag, value):
    if value not in (None, ""):
        command.extend([flag, str(value)])


def _run_subprocess(command, timeout):
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _command_result(name, command, timeout):
    try:
        result = _run_subprocess(command, timeout)
        status = "ok" if result.returncode == 0 else "error"
        return {
            "name": name,
            "command": " ".join(command),
            "status": status,
            "exit_code": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "command": " ".join(command),
            "status": "timeout",
            "exit_code": "",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }
    except Exception as exc:
        return {
            "name": name,
            "command": " ".join(command),
            "status": "error",
            "exit_code": "",
            "stdout": "",
            "stderr": str(exc),
        }


def _lmstudio_cli_path():
    bundled = Path.home() / ".lmstudio" / "bin" / "lms"
    if bundled.exists() and bundled.is_file():
        return str(bundled)
    return shutil.which("lms")


def _collect_json_objects(value):
    objects = []
    if isinstance(value, dict):
        objects.append(value)
        for item in value.values():
            objects.extend(_collect_json_objects(item))
    elif isinstance(value, list):
        for item in value:
            objects.extend(_collect_json_objects(item))
    return objects


def _first_value(row, fields):
    for field in fields:
        value = row.get(field)
        if value not in (None, ""):
            return str(value)
    return ""


def _looks_like_lmstudio_model(row):
    model_keys = (
        "modelKey",
        "identifier",
        "indexedModelIdentifier",
        "model_id",
        "modelId",
    )
    if any(row.get(field) for field in model_keys):
        return True
    return bool(row.get("type") in ("llm", "embedding") and row.get("path"))


def _lmstudio_identity_values(row):
    values = []
    for field in (
        "modelKey",
        "identifier",
        "indexedModelIdentifier",
        "model_id",
        "modelId",
        "id",
        "path",
        "name",
        "displayName",
    ):
        value = row.get(field)
        if value not in (None, ""):
            values.append(str(value))
    return values


def _parse_lmstudio_inventory(ls_stdout, ps_stdout=""):
    loaded_ids = set()
    try:
        ps_data = json.loads(ps_stdout) if ps_stdout.strip() else []
    except json.JSONDecodeError:
        ps_data = []
    for row in _collect_json_objects(ps_data):
        if not _looks_like_lmstudio_model(row):
            continue
        for value in _lmstudio_identity_values(row):
            loaded_ids.add(value.lower())

    try:
        data = json.loads(ls_stdout) if ls_stdout.strip() else []
    except json.JSONDecodeError:
        return []
    seen = set()
    models = []
    for row in _collect_json_objects(data):
        if not _looks_like_lmstudio_model(row):
            continue
        model_id = _first_value(
            row,
            (
                "modelKey",
                "identifier",
                "indexedModelIdentifier",
                "model_id",
                "modelId",
                "id",
                "path",
                "name",
                "displayName",
            ),
        )
        display_name = _first_value(
            row,
            (
                "displayName",
                "display_name",
                "modelName",
                "model_name",
                "name",
                "modelKey",
                "identifier",
                "id",
            ),
        )
        if not model_id or model_id.lower() in seen:
            continue
        seen.add(model_id.lower())
        path_id = str(row.get("path") or "").lower()
        identities = {value.lower() for value in _lmstudio_identity_values(row)}
        status = (
            "loaded"
            if identities & loaded_ids or (path_id and path_id in loaded_ids)
            else "indexed"
        )
        models.append(
            {
                "runtime": "LM Studio",
                "model_id": model_id,
                "display_name": display_name or model_id,
                "status": status,
                "source_path": row.get("path") or "",
            }
        )
    return models


def _scan_lmstudio_filesystem_models(root=LMSTUDIO_MODELS_ROOT, indexed_paths=()):
    root = Path(root)
    if not root.exists():
        return []
    indexed = {str(path).strip().lower() for path in indexed_paths if path}
    models = []
    for publisher_dir in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not publisher_dir.is_dir() or publisher_dir.name.startswith("."):
            continue
        for model_dir in sorted(publisher_dir.iterdir(), key=lambda item: item.name.lower()):
            if not model_dir.is_dir() or model_dir.name.startswith("."):
                continue
            relative_path = f"{publisher_dir.name}/{model_dir.name}"
            if relative_path.lower() in indexed:
                continue
            models.append(
                {
                    "runtime": "LM Studio",
                    "model_id": relative_path,
                    "display_name": model_dir.name,
                    "status": "filesystem_only",
                    "source_path": relative_path,
                }
            )
    return models


def _parse_ollama_inventory(stdout):
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines or not lines[0].lower().startswith("name"):
        return []
    models = []
    for line in lines[1:]:
        parts = line.split()
        model_id = parts[0] if parts else ""
        if model_id:
            models.append(
                {
                    "runtime": "Ollama",
                    "model_id": model_id,
                    "display_name": model_id,
                    "status": "installed",
                }
            )
    return models


def _refresh_inventory(timeout=5):
    checks = []
    models = []
    lms_path = _lmstudio_cli_path()
    if lms_path:
        lm_ls = _command_result("LM Studio models", [lms_path, "ls", "--json"], timeout)
        lm_ps = _command_result("LM Studio loaded models", [lms_path, "ps", "--json"], timeout)
        checks.extend([lm_ls, lm_ps])
        lmstudio_models = []
        if lm_ls["status"] == "ok":
            lmstudio_models = _parse_lmstudio_inventory(lm_ls["stdout"], lm_ps["stdout"])
            models.extend(lmstudio_models)
        models.extend(
            _scan_lmstudio_filesystem_models(
                indexed_paths=[model.get("source_path") for model in lmstudio_models]
            )
        )
    else:
        checks.append(
            {
                "name": "LM Studio models",
                "command": "lms ls --json",
                "status": "unavailable",
                "exit_code": "",
                "stdout": "",
                "stderr": "LM Studio CLI not found at ~/.lmstudio/bin/lms or on PATH.",
            }
        )

    ollama_path = shutil.which("ollama")
    if ollama_path:
        ollama = _command_result("Ollama models", [ollama_path, "list"], timeout)
        checks.append(ollama)
        if ollama["status"] == "ok":
            models.extend(_parse_ollama_inventory(ollama["stdout"]))
    else:
        checks.append(
            {
                "name": "Ollama models",
                "command": "ollama list",
                "status": "unavailable",
                "exit_code": "",
                "stdout": "",
                "stderr": "Ollama CLI not found on PATH.",
            }
        )
    return {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "models": models,
        "checks": checks,
    }


def _match_inventory_model(model, candidates):
    model_id = model["model_id"].lower()
    source_path = model.get("source_path", "").lower()
    matches = [
        row
        for row in candidates
        if row.get("local_model_id", "").lower() == model_id
        or row.get("model_name", "").lower() == model_id
        or (
            source_path
            and (
                row.get("runtime_availability", "").lower() == source_path
                or row.get("model_page_url", "").lower().rstrip("/").endswith(source_path)
            )
        )
    ]
    if len(matches) == 1:
        return "registered", matches[0]
    if len(matches) > 1:
        return "ambiguous", None
    return "unregistered", None


def _inventory_run_allowed(model, candidate):
    if not candidate or not _candidate_run_ready(candidate):
        return False
    if model.get("runtime") == "LM Studio":
        return model.get("status") in ("indexed", "loaded")
    return model.get("status") != "filesystem_only"


def _inventory_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "runtime": _query_value(query, "runtime"),
        "status": _query_value(query, "status"),
        "match": _query_value(query, "match"),
    }


def _matches_inventory_search(entry, search):
    if not search:
        return True
    model = entry["model"]
    candidate = entry.get("candidate")
    haystack = " ".join(
        [
            model.get("runtime", ""),
            model.get("model_id", ""),
            model.get("display_name", ""),
            model.get("status", ""),
            model.get("source_path", ""),
            entry.get("match_state", ""),
            candidate.get("candidate_id", "") if candidate else "",
            candidate.get("model_name", "") if candidate else "",
        ]
    )
    return search.lower() in haystack.lower()


def _filter_inventory_entries(entries, filters):
    filtered = []
    for entry in entries:
        model = entry["model"]
        if filters["runtime"] and model.get("runtime") != filters["runtime"]:
            continue
        if filters["status"] and model.get("status") != filters["status"]:
            continue
        if filters["match"] and entry.get("match_state") != filters["match"]:
            continue
        if not _matches_inventory_search(entry, filters["q"]):
            continue
        filtered.append(entry)
    return filtered


def _inventory_filters(entries, filters):
    runtime_options = "".join(
        _option(runtime, runtime, filters["runtime"])
        for runtime in sorted(
            {
                entry["model"].get("runtime", "")
                for entry in entries
                if entry["model"].get("runtime")
            },
            key=lambda value: value.lower(),
        )
    )
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in sorted(
            {entry["model"].get("status", "") for entry in entries if entry["model"].get("status")},
            key=lambda value: value.lower(),
        )
    )
    match_options = "".join(
        _option(match, match, filters["match"])
        for match in sorted(
            {entry.get("match_state", "") for entry in entries if entry.get("match_state")},
            key=lambda value: value.lower(),
        )
    )
    clear_link = (
        '<a class="clear-link" href="/inventory">Clear</a>' if any(filters.values()) else ""
    )
    return """
    <form class="filters" method="get" action="/inventory">
      <div class="field field-wide">
        <label for="inventory-q">Search</label>
        <input id="inventory-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="inventory-runtime">Runtime</label>
        <select id="inventory-runtime" name="runtime">
          {all_runtimes}
          {runtime_options}
        </select>
      </div>
      <div class="field">
        <label for="inventory-status">Status</label>
        <select id="inventory-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="field">
        <label for="inventory-match">Registry match</label>
        <select id="inventory-match" name="match">
          {all_matches}
          {match_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_runtimes=_option("", "All runtimes", filters["runtime"]),
        runtime_options=runtime_options,
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        all_matches=_option("", "All matches", filters["match"]),
        match_options=match_options,
        clear_link=clear_link,
    )


def _inventory(
    query=None,
    inventory_result=None,
    action_token="",
    enable_run_tests=False,
    enable_refresh=True,
):
    candidates = _load_radar_candidates()
    result = inventory_result
    filters = _inventory_filter_values(query or {})
    check_rows = []
    model_rows = []
    entries = []
    if result:
        for check in result["checks"]:
            output = check.get("stderr") or check.get("stdout") or ""
            check_rows.append(
                [
                    _text(check["name"]),
                    _pill(check["status"]),
                    _text(check.get("exit_code")),
                    "<code>{}</code>".format(_text(check["command"])),
                    _text(output[:500]),
                ]
            )
        for model in result["models"]:
            match_state, candidate = _match_inventory_model(model, candidates)
            entries.append(
                {
                    "model": model,
                    "match_state": match_state,
                    "candidate": candidate,
                }
            )
        for entry in _filter_inventory_entries(entries, filters):
            model = entry["model"]
            match_state = entry["match_state"]
            candidate = entry["candidate"]
            candidate_cell = (
                '<a href="/radar?q={id}">{id}</a>'.format(id=_text(candidate["candidate_id"]))
                if candidate
                else _pill(match_state)
            )
            if _inventory_run_allowed(model, candidate):
                action_cell = _run_test_control(candidate, enable_run_tests, action_token)
            elif model.get("status") == "filesystem_only":
                action_cell = (
                    '<span class="empty">Filesystem-only; index/load in LM Studio first</span>'
                )
            else:
                action_cell = '<span class="empty">Register exact local model id first</span>'
            model_rows.append(
                [
                    _text(model["runtime"]),
                    "<code>{}</code>".format(_text(model["model_id"])),
                    _text(model["display_name"]),
                    _pill(model["status"]),
                    _text(model.get("source_path", "")),
                    candidate_cell,
                    action_cell,
                ]
            )

    body = """
    <section class="panel" style="margin-bottom:16px">
      <h2>Installed Models</h2>
      <p>This page checks local runtime inventory on demand. It does not download, install, benchmark, score, or import models.</p>
      <p>LM Studio rows distinguish <code>loaded</code>, <code>indexed</code>, and <code>filesystem_only</code>. Filesystem-only folders are visible on disk but are not runnable from the dashboard until LM Studio indexes or loads them.</p>
      <form class="inline-form" method="post" action="/actions/refresh-inventory">
        <input type="hidden" name="token" value="{token}">
        <button type="submit"{disabled}>Refresh Inventory</button>
      </form>
      {disabled_note}
      <p class="empty">Last refresh: {checked_at}</p>
    </section>
    <section>
      <h2>Detected Models{filtered_count}</h2>
      {filters}
      {models}
    </section>
    <section style="margin-top:16px">
      <h2>Runtime Checks</h2>
      {checks}
    </section>
    """.format(
        token=_text(action_token),
        disabled="" if enable_refresh else " disabled",
        disabled_note=(
            ""
            if enable_refresh
            else '<p class="empty">Inventory refresh is available only on a localhost or loopback dashboard bind.</p>'
        ),
        checked_at=_text(result["checked_at"] if result else "not checked yet"),
        filtered_count=(
            f" ({len(_filter_inventory_entries(entries, filters))} of {len(entries)})"
            if any(filters.values())
            else ""
        ),
        filters=_inventory_filters(entries, filters),
        models=_table(
            ["Runtime", "Model id", "Display name", "Status", "Path", "Registry match", "Action"],
            model_rows,
            empty_message=(
                "No inventory refresh has run yet."
                if not result
                else "No detected models match these filters."
            ),
        ),
        checks=_table(
            ["Check", "Status", "Exit", "Command", "Output"],
            check_rows,
            empty_message="No runtime checks have run yet.",
        ),
    )
    return _layout("Installed Models", "/inventory", body)


def _build_candidate_commands(row, run_id, eval_results_dir):
    run_dir = Path(eval_results_dir) / run_id
    init_command = [
        sys.executable,
        str(HARNESS_PATH),
        "init-run",
        "--benchmark-run-id",
        run_id,
        "--model-name",
        row.get("model_name", ""),
        "--backend",
        _candidate_runner_label(row),
        "--output-root",
        str(eval_results_dir),
        "--run-notes",
        "benchmark_run_id={} | candidate_id={} | dashboard_run_button=yes".format(
            run_id,
            row.get("candidate_id", ""),
        ),
    ]
    _append_arg(init_command, "--model-family", row.get("model_family"))
    _append_arg(init_command, "--provider", row.get("provider_or_org"))
    _append_arg(init_command, "--source-url", row.get("model_page_url"))
    _append_arg(init_command, "--format", row.get("format_or_runtime"))

    runner = row.get("local_runner", "")
    if runner == "lmstudio-cli":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-lmstudio-cli",
            "--run-dir",
            str(run_dir),
            "--model-id",
            row.get("local_model_id", ""),
            "--force",
        ]
    elif runner == "openai-compatible":
        capture_command = [
            sys.executable,
            str(HARNESS_PATH),
            "run-local",
            "--run-dir",
            str(run_dir),
            "--endpoint",
            row.get("default_endpoint", ""),
            "--model",
            row.get("local_model_id") or row.get("model_name", ""),
            "--force",
        ]
    else:
        raise ValueError(f"Unsupported local runner: {runner}")
    return init_command, capture_command


def _run_candidate_test(candidate_id, registry_path, eval_results_dir, timeout):
    candidates = _load_radar_candidates(registry_path)
    row = next((item for item in candidates if item.get("candidate_id") == candidate_id), None)
    if row is None:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if not _candidate_run_ready(row):
        raise ValueError("Candidate is missing exact local runner metadata.")
    run_id = _next_dashboard_run_id(row, eval_results_dir)
    init_command, capture_command = _build_candidate_commands(row, run_id, eval_results_dir)
    init_result = _run_subprocess(init_command, timeout)
    if init_result.returncode != 0:
        return {
            "candidate": row,
            "run_id": run_id,
            "run_dir": str(Path(eval_results_dir) / run_id),
            "init": init_result,
            "capture": None,
        }
    capture_result = _run_subprocess(capture_command, timeout)
    return {
        "candidate": row,
        "run_id": run_id,
        "run_dir": str(Path(eval_results_dir) / run_id),
        "init": init_result,
        "capture": capture_result,
    }


def _result_block(label, result):
    if result is None:
        return f'<p class="empty">{_text(label)} did not run.</p>'
    status = "passed" if result.returncode == 0 else "failed"
    return """
    <div class="panel">
      <h2>{label} {status}</h2>
      <p>Exit code: <code>{code}</code></p>
      <pre class="command">{stdout}{stderr}</pre>
    </div>
    """.format(
        label=_text(label),
        status=_text(status),
        code=_text(result.returncode),
        stdout=_text(result.stdout or ""),
        stderr=_text(result.stderr or ""),
    )


def _run_action_page(result):
    candidate = result["candidate"]
    body = """
    <section class="panel">
      <h2>Run Test Result</h2>
      <p><strong>Candidate:</strong> {candidate}</p>
      <p><strong>Runner:</strong> {runner}</p>
      <p><strong>Artifact:</strong> {artifact}</p>
      <p class="empty">Raw responses are local artifact evidence. Scores and decisions still require human review.</p>
    </section>
    <section style="margin-top:16px">{init}</section>
    <section style="margin-top:16px">{capture}</section>
    """.format(
        candidate=_text(candidate.get("model_name")),
        runner=_text(_candidate_runner_label(candidate)),
        artifact=_artifact_link(result["run_id"]),
        init=_result_block("Init run", result["init"]),
        capture=_result_block("Capture prompts", result["capture"]),
    )
    return _layout("Run Test Result", "", body)


def _is_loopback_host(host):
    if str(host).lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _relative_path(path):
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _artifact_link(benchmark_run_id):
    if not benchmark_run_id:
        return '<span class="empty">Not linked</span>'
    return '<a href="/artifacts/{id}"><code>{id}</code></a>'.format(id=_text(benchmark_run_id))


def _benchmark_run_id_from_notes(notes):
    for part in str(notes or "").split("|"):
        part = part.strip()
        if part.startswith("benchmark_run_id="):
            return part.split("=", 1)[1].strip()
    return ""


def _artifact_link_from_notes(notes):
    return _artifact_link(_benchmark_run_id_from_notes(notes))


def _command_block(command):
    return f'<pre class="command">{_text(command)}</pre>'


def _command_lines(command):
    return " ".join(shlex.quote(str(part)) for part in command)


def _file_status(path):
    return "yes" if Path(path).exists() else "no"


def _count_jsonl_lines(path):
    path = Path(path)
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _artifact_summaries(eval_results_dir=EVAL_RESULTS_DIR):
    root = Path(eval_results_dir)
    if not root.exists():
        return []
    artifacts = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir():
            continue
        artifacts.append(
            {
                "benchmark_run_id": path.name,
                "path": path,
                "raw_responses": _count_jsonl_lines(path / "raw_responses.jsonl"),
                "scores": _file_status(path / "scores.json"),
                "draft_scores": _file_status(path / "draft-scores.json"),
                "decision": _file_status(path / "decision.json"),
                "dashboard_import": _file_status(path / "dashboard-import"),
            }
        )
    return artifacts


def _artifact_csv_paths(benchmark_run_id, eval_results_dir=None):
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    import_dir = Path(eval_results_dir) / benchmark_run_id / "dashboard-import"
    return {
        "models": import_dir / "models.csv",
        "model_runs": import_dir / "model_runs.csv",
        "eval_scores": import_dir / "eval_scores.csv",
        "decisions": import_dir / "decisions.csv",
    }


def _artifact_import_ready(benchmark_run_id, eval_results_dir=None):
    return all(
        path.exists() for path in _artifact_csv_paths(benchmark_run_id, eval_results_dir).values()
    )


def _artifact_import_command(
    benchmark_run_id,
    database_path=DEFAULT_DASHBOARD_DB,
    eval_results_dir=None,
):
    paths = _artifact_csv_paths(benchmark_run_id, eval_results_dir)
    return [
        "python3",
        "apps/model-dashboard/run_dashboard.py",
        "import-csv",
        "--db",
        _relative_path(database_path),
        "--models",
        _relative_path(paths["models"]),
        "--runs",
        _relative_path(paths["model_runs"]),
        "--scores",
        _relative_path(paths["eval_scores"]),
        "--decisions",
        _relative_path(paths["decisions"]),
    ]


def _artifact_report_command(database_path=DEFAULT_DASHBOARD_DB):
    return [
        "python3",
        "apps/model-dashboard/run_dashboard.py",
        "report",
        "--db",
        _relative_path(database_path),
    ]


def _artifact_import_guidance(
    benchmark_run_id,
    database_path=DEFAULT_DASHBOARD_DB,
    eval_results_dir=None,
):
    if not _artifact_import_ready(benchmark_run_id, eval_results_dir):
        return '<span class="empty">Dashboard CSVs are incomplete.</span>'
    return """
    <div class="cell-stack">
      <div><strong>Import</strong>{import_command}</div>
      <div><strong>Report</strong>{report_command}</div>
    </div>
    """.format(
        import_command=_command_block(
            _command_lines(
                _artifact_import_command(
                    benchmark_run_id,
                    database_path,
                    eval_results_dir,
                )
            )
        ),
        report_command=_command_block(_command_lines(_artifact_report_command(database_path))),
    )


def _artifact_import_control(
    benchmark_run_id,
    enable_import_actions=False,
    action_token="",
    eval_results_dir=None,
):
    if not _artifact_import_ready(benchmark_run_id, eval_results_dir):
        return '<span class="empty">No complete dashboard-import CSV set</span>'
    if not enable_import_actions:
        return (
            '<div class="cell-stack">'
            '<button type="button" disabled>Import Artifact</button>'
            '<div class="empty">Restart with <code>--enable-import-actions</code></div>'
            "</div>"
        )
    return f"""
    <form class="inline-form" method="post" action="/actions/import-artifact">
      <input type="hidden" name="token" value="{_text(action_token)}">
      <input type="hidden" name="benchmark_run_id" value="{_text(benchmark_run_id)}">
      <button type="submit">Import Artifact</button>
    </form>
    """


def _import_artifact(benchmark_run_id, database_path, eval_results_dir=None):
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    artifact_dir = Path(eval_results_dir) / benchmark_run_id
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise ValueError(f"Artifact not found: {benchmark_run_id}")
    paths = _artifact_csv_paths(benchmark_run_id, eval_results_dir)
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise ValueError("Artifact is missing dashboard CSVs: {}".format(", ".join(missing)))
    counts = csv_io.import_all(database_path, paths)
    return {"benchmark_run_id": benchmark_run_id, "counts": counts}


def _import_action_page(result):
    body = """
    <section class="panel">
      <h2>Artifact Imported</h2>
      <p><strong>Benchmark run:</strong> {artifact}</p>
      <p><strong>Imported rows:</strong> <code>{counts}</code></p>
      <p><a href="/runs">Inspect imported runs</a></p>
    </section>
    """.format(
        artifact=_artifact_link(result["benchmark_run_id"]),
        counts=_text(result["counts"]),
    )
    return _layout("Artifact Imported", "", body)


def _score_status_counts(conn):
    counts = {"confirmed": 0, "draft": 0}
    for row in _real_rows(db.list_score_details(conn)):
        counts[row["score_status"]] = counts.get(row["score_status"], 0) + 1
    return counts


def _dashboard_model_links(conn):
    links = {}
    for row in _real_rows(db.list_model_summaries(conn)):
        model_name = str(row["model_name"] or "")
        if model_name:
            links[model_name.lower()] = row["id"]
    return links


def _dashboard_run_ids(conn):
    run_ids = set()
    for row in _real_rows(db.list_runs(conn)):
        run_id = _benchmark_run_id_from_notes(row["run_notes"])
        if run_id:
            run_ids.add(run_id)
    return run_ids


def _dashboard_runs_by_benchmark_id(conn):
    runs = {}
    for row in _real_rows(db.list_runs(conn)):
        run_id = _benchmark_run_id_from_notes(row["run_notes"])
        if run_id:
            runs[run_id] = row
    return runs


def _latest_decisions_by_model_id(conn):
    decisions = {}
    for row in _real_rows(db.list_decisions(conn)):
        if row["model_id"] not in decisions:
            decisions[row["model_id"]] = row
    return decisions


def _import_state_for_run(run, decisions_by_model):
    if not run:
        return '<span class="empty">not imported</span>'
    decision = decisions_by_model.get(run["model_id"])
    decision_state = _text(decision["decision"]) if decision else "no decision"
    return (
        '<div class="cell-stack">'
        '<a href="/models/{id}">imported model</a>'
        "<div>{score} {status}</div>"
        "<div>decision: {decision}</div>"
        "</div>"
    ).format(
        id=run["model_id"],
        score=_number(run["total_score"], 2, "unscored"),
        status=_status_pill(run["score_status"]),
        decision=decision_state,
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


def _layout(title, current_path, body):
    nav = []
    for path, label in NAV_ITEMS:
        active = " active" if current_path == path else ""
        icon = NAV_ICONS.get(path, "ti-circle")
        nav.append(
            f'<a class="nav{active}" href="{path}"><i class="ti {escape(icon)}" aria-hidden="true"></i><span>{escape(label)}</span></a>'
        )
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - Local Model Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.26.0/dist/tabler-icons.min.css">
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #f4f1eb;
      --header: #fbfaf6;
      --panel: #fffefa;
      --panel-soft: #f9f6ef;
      --control: #fffdf8;
      --ink: #202124;
      --muted: #676b72;
      --line: rgba(32, 33, 36, 0.13);
      --line-soft: rgba(32, 33, 36, 0.08);
      --accent: #1b746f;
      --accent-ink: #ffffff;
      --accent-soft: #dff1ee;
      --accent-soft-ink: #135a55;
      --accent-2: #9b4d1f;
      --table-head: #ece5da;
      --pill-bg: #e5f1ee;
      --pill-ink: #185a55;
      --status-confirmed-bg: #e1f3e9;
      --status-confirmed-ink: #1d6540;
      --status-draft-bg: #fff0d6;
      --status-draft-ink: #805015;
      --code-bg: #202327;
      --code-ink: #f7f1e8;
      --shadow: 0 12px 32px rgba(55, 45, 30, 0.07);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #1a1b1e;
        --header: #202125;
        --panel: #24262a;
        --panel-soft: #202226;
        --control: #202226;
        --ink: #f3efe7;
        --muted: #a9a59d;
        --line: rgba(243, 239, 231, 0.14);
        --line-soft: rgba(243, 239, 231, 0.08);
        --accent: #39aaa2;
        --accent-ink: #102322;
        --accent-soft: rgba(57, 170, 162, 0.16);
        --accent-soft-ink: #8ee3da;
        --accent-2: #e0a26d;
        --table-head: #2d2b28;
        --pill-bg: rgba(57, 170, 162, 0.14);
        --pill-ink: #9ce5dd;
        --status-confirmed-bg: rgba(84, 190, 125, 0.14);
        --status-confirmed-ink: #9be7b8;
        --status-draft-bg: rgba(238, 178, 85, 0.16);
        --status-draft-ink: #f0c985;
        --code-bg: #111316;
        --code-ink: #f7f1e8;
        --shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      line-height: 1.5;
      font-weight: 400;
    }}
    strong {{ font-weight: 500; }}
    header {{
      border-bottom: 0.5px solid var(--line);
      background: var(--header);
    }}
    .topbar {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 22px 20px 16px;
    }}
    h1 {{
      margin: 0 0 16px;
      font-size: 28px;
      line-height: 1.15;
      letter-spacing: 0;
      font-weight: 500;
    }}
    nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .nav {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      color: var(--muted);
      border: 0.5px solid var(--line);
      border-radius: 8px;
      padding: 8px 11px;
      text-decoration: none;
      background: var(--panel-soft);
      font-weight: 500;
      transition: background 150ms ease, color 150ms ease, border-color 150ms ease;
    }}
    .nav .ti {{
      color: var(--accent);
      font-size: 17px;
      line-height: 1;
    }}
    .nav.active {{
      border-color: transparent;
      color: var(--accent-soft-ink);
      background: var(--accent-soft);
    }}
    .nav.active .ti {{
      color: var(--accent-soft-ink);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px 20px 32px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .stat, .panel {{
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 12px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .stat {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 12px;
      align-items: start;
    }}
    .stat .ti {{
      color: var(--accent);
      font-size: 20px;
      line-height: 1;
      margin-top: 3px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 5px;
    }}
    .stat .value {{
      font-size: 26px;
      font-weight: 500;
      line-height: 1.1;
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(140px, 1fr)) auto;
      gap: 12px;
      align-items: end;
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      margin: 0 0 18px;
      box-shadow: var(--shadow);
    }}
    .filters-compact {{
      grid-template-columns: minmax(220px, 2fr) repeat(2, minmax(140px, 1fr)) auto;
    }}
    .filters-wide {{
      grid-template-columns: minmax(220px, 2fr) repeat(4, minmax(140px, 1fr)) auto;
    }}
    .field label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
      margin: 0 0 6px;
    }}
    input, select {{
      width: 100%;
      min-height: 38px;
      border: 0.5px solid var(--line);
      border-radius: 8px;
      background: var(--control);
      color: var(--ink);
      font: inherit;
      padding: 8px 10px;
    }}
    button {{
      min-height: 38px;
      border: 0.5px solid var(--accent);
      border-radius: 8px;
      background: var(--accent);
      color: var(--accent-ink);
      font: inherit;
      font-weight: 500;
      padding: 8px 13px;
      cursor: pointer;
    }}
    button:disabled {{
      border-color: var(--line);
      background: var(--panel-soft);
      color: var(--muted);
      cursor: not-allowed;
    }}
    .inline-form {{
      display: grid;
      gap: 8px;
      align-items: start;
    }}
    .filter-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .clear-link {{
      color: var(--muted);
      font-size: 13px;
      text-decoration: none;
    }}
    h2 {{
      font-size: 20px;
      margin: 0 0 14px;
      letter-spacing: 0;
      font-weight: 500;
    }}
    table {{
      width: 100%;
      min-width: 760px;
      border-collapse: separate;
      border-spacing: 0;
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    th, td {{
      border-bottom: 0.5px solid var(--line-soft);
      padding: 13px 12px;
      text-align: left;
      vertical-align: top;
      white-space: normal;
      overflow-wrap: anywhere;
    }}
    th {{
      background: var(--table-head);
      color: var(--muted);
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .table-wrap {{
      width: 100%;
      overflow-x: auto;
      border-radius: 12px;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    a {{ color: var(--accent); }}
    .pill {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 9px;
      background: var(--pill-bg);
      color: var(--pill-ink);
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }}
    .score-status {{
      background: var(--status-confirmed-bg);
      color: var(--status-confirmed-ink);
      text-transform: uppercase;
    }}
    .score-status.draft {{
      background: var(--status-draft-bg);
      color: var(--status-draft-ink);
    }}
    .empty {{ color: var(--muted); }}
    .report {{
      background: var(--code-bg);
      color: var(--code-ink);
      border-radius: 12px;
      padding: 18px;
      overflow-x: auto;
      white-space: pre-wrap;
    }}
    .command {{
      margin: 0;
      background: var(--code-bg);
      color: var(--code-ink);
      border-radius: 12px;
      padding: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 13px;
    }}
    .workflow-table td:nth-child(1) {{
      width: 150px;
      font-weight: 500;
    }}
    .lab-queue {{
      min-width: 980px;
    }}
    .lab-queue th:nth-child(1),
    .lab-queue td:nth-child(1) {{
      width: 250px;
    }}
    .lab-queue th:nth-child(2),
    .lab-queue td:nth-child(2),
    .lab-queue th:nth-child(3),
    .lab-queue td:nth-child(3),
    .lab-queue th:nth-child(4),
    .lab-queue td:nth-child(4) {{
      width: 120px;
    }}
    .split {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
      gap: 18px;
    }}
    .cell-stack {{
      display: grid;
      gap: 7px;
    }}
    .cell-stack strong {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
    }}
    .radar-table {{
      min-width: 1520px;
    }}
    .radar-table th:nth-child(1),
    .radar-table td:nth-child(1) {{
      width: 180px;
    }}
    .radar-table th:nth-child(2),
    .radar-table td:nth-child(2) {{
      width: 112px;
    }}
    .radar-table th:nth-child(3),
    .radar-table td:nth-child(3) {{
      width: 132px;
    }}
    .radar-table th:nth-child(4),
    .radar-table td:nth-child(4) {{
      width: 220px;
    }}
    .radar-table th:nth-child(5),
    .radar-table td:nth-child(5) {{
      width: 230px;
    }}
    .radar-table th:nth-child(6),
    .radar-table td:nth-child(6) {{
      width: 260px;
    }}
    .radar-table th:nth-child(7),
    .radar-table td:nth-child(7) {{
      width: 190px;
    }}
    .radar-table th:nth-child(8),
    .radar-table td:nth-child(8) {{
      width: 190px;
    }}
    .project-table {{
      min-width: 980px;
    }}
    .project-table th:nth-child(1),
    .project-table td:nth-child(1) {{
      width: 190px;
    }}
    .project-table th:nth-child(2),
    .project-table td:nth-child(2) {{
      width: 150px;
    }}
    .project-table th:nth-child(4),
    .project-table td:nth-child(4) {{
      width: 220px;
    }}
    @media (max-width: 780px) {{
      .filters {{ grid-template-columns: 1fr; }}
      .filter-actions {{ justify-content: flex-start; }}
      .split {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 24px; }}
      th, td {{ padding: 11px 9px; }}
    }}
  </style>
</head>
<body>
  <header><div class="topbar"><h1>Local Model Performance Dashboard</h1><nav>{nav}</nav></div></header>
  <main>{body}</main>
</body>
</html>""".format(title=escape(title), nav="".join(nav), body=body)


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
        ),
    )
    return _layout("Overview", "/", body)


def _lab(
    conn,
    registry_path=CANDIDATE_REGISTRY_PATH,
    eval_results_dir=EVAL_RESULTS_DIR,
    project_registry_path=PROJECT_REGISTRY_PATH,
    enable_run_tests=False,
    enable_import_actions=False,
    action_token="",
    database_path=DEFAULT_DASHBOARD_DB,
):
    candidates = _load_radar_candidates(registry_path)
    projects = _load_project_repos(project_registry_path)
    artifacts = _artifact_summaries(eval_results_dir)
    model_links = _dashboard_model_links(conn)
    imported_run_ids = _dashboard_run_ids(conn)
    dashboard_runs = _dashboard_runs_by_benchmark_id(conn)
    decisions_by_model = _latest_decisions_by_model_id(conn)
    score_counts = _score_status_counts(conn)
    real_counts = _real_counts(conn)
    ready_candidates = [row for row in candidates if row.get("status") == "ready_for_eval"]
    specialty_candidates = [row for row in candidates if _is_specialty_candidate(row)]
    ready_projects = [row for row in projects if row.get("status") == "ready_for_review"]
    artifact_ids = {row["benchmark_run_id"] for row in artifacts}
    linked_imports = len(artifact_ids & imported_run_ids)

    stage_rows = [
        [
            "Radar",
            _pill("ready"),
            f"{len(ready_candidates)} ready candidates",
            '<a href="/radar?status=ready_for_eval">Review ready queue</a>',
        ],
        [
            "Project Radar",
            _pill("review"),
            f"{len(projects)} GitHub repos tracked",
            '<a href="/projects">Review project opportunities</a>',
        ],
        [
            "Benchmark",
            _pill("active"),
            f"{len(artifacts)} artifact directories",
            "Run a local endpoint benchmark for the next approved candidate.",
        ],
        [
            "Score",
            _status_pill("draft") if score_counts["draft"] else _status_pill("confirmed"),
            "{} draft / {} confirmed".format(score_counts["draft"], score_counts["confirmed"]),
            "Use draft scores for review, then export confirmed scores.",
        ],
        [
            "Import",
            _pill("linked"),
            f"{linked_imports} artifacts linked to active DB",
            '<a href="/runs">Inspect imported runs</a>',
        ],
        [
            "Decision",
            _pill("local"),
            "{} real decisions logged".format(real_counts["decisions"]),
            '<a href="/storage">Review keep/watch/retest state</a>',
        ],
    ]

    queue_rows = []
    for row in ready_candidates:
        run_id = row.get("benchmark_run_id")
        model_id = model_links.get(row.get("model_name", "").lower())
        dashboard_state = (
            f'<a href="/models/{model_id}">imported</a>'
            if model_id
            else '<span class="empty">not imported</span>'
        )
        artifact_state = (
            _artifact_link(run_id) if run_id else '<span class="empty">no artifact yet</span>'
        )
        proposed_run_id = run_id or "YYYYMMDD-{}-local".format(
            row.get("candidate_id", "candidate").replace("_", "-")
        )
        command = "\n".join(
            [
                "python3 evals/local-llm-benchmark/harness.py init-run \\",
                f"  --benchmark-run-id {proposed_run_id} \\",
                '  --model-name "{}" \\'.format(row.get("model_name", "")),
                '  --backend "Local OpenAI-compatible" \\',
                "  --temperature 0.2 \\",
                "  --top-p 0.9",
                "",
                "python3 evals/local-llm-benchmark/harness.py run-local \\",
                f"  --run-dir data/eval_results/{proposed_run_id} \\",
                "  --endpoint http://127.0.0.1:1234/v1 \\",
                '  --model "{}" \\'.format(row.get("model_name", "")),
                "  --force",
            ]
        )
        queue_rows.append(
            [
                '<div class="cell-stack"><div>{name}</div><code>{id}</code></div>'.format(
                    name=_text(row.get("model_name")),
                    id=_text(row.get("candidate_id")),
                ),
                _pill(row.get("status")),
                """
                <div class="cell-stack">
                  <div><strong>Artifact</strong><br>{artifact}</div>
                  <div><strong>Dashboard</strong><br>{dashboard}</div>
                  <div><strong>Availability</strong><br>{availability}</div>
                  <div><strong>Risk</strong><br>{risk}</div>
                </div>
                """.format(
                    artifact=artifact_state,
                    dashboard=dashboard_state,
                    availability=_candidate_availability(row),
                    risk=_text(row.get("risk_notes")),
                ),
                _run_test_control(row, enable_run_tests, action_token),
                _command_block(command),
            ]
        )

    artifact_rows = []
    for row in artifacts:
        run_id = row["benchmark_run_id"]
        dashboard_state = _import_state_for_run(dashboard_runs.get(run_id), decisions_by_model)
        artifact_rows.append(
            [
                _artifact_link(run_id),
                _text(row["raw_responses"]),
                _text(row["scores"]),
                _text(row["draft_scores"]),
                _text(row["decision"]),
                _text(row["dashboard_import"]),
                dashboard_state,
                _artifact_import_control(
                    run_id,
                    enable_import_actions,
                    action_token,
                    eval_results_dir,
                ),
                _artifact_import_guidance(run_id, database_path, eval_results_dir),
            ]
        )

    specialty_rows = []
    for row in specialty_candidates:
        specialty_rows.append(
            [
                '<div class="cell-stack"><div>{name}</div><code>{id}</code></div>'.format(
                    name=_text(row.get("model_name")),
                    id=_text(row.get("candidate_id")),
                ),
                '<div class="cell-stack"><div>{lane}</div>{status}</div>'.format(
                    lane=_text(_specialty_lane_label(row)),
                    status=_pill(row.get("status")),
                ),
                """
                <div class="cell-stack">
                  <div><strong>Runtime</strong><br>{runtime}</div>
                  <div><strong>Availability</strong><br>{availability}</div>
                  <div><strong>Why</strong><br>{why}</div>
                  <div><strong>Risk</strong><br>{risk}</div>
                </div>
                """.format(
                    runtime=_text(row.get("format_or_runtime")),
                    availability=_candidate_availability(row),
                    why=_text(row.get("why_interesting")),
                    risk=_text(row.get("risk_notes")),
                ),
                _text(row.get("proposed_eval")),
            ]
        )

    project_rows = []
    for row in ready_projects:
        project_rows.append(
            [
                '<div class="cell-stack"><a href="{url}">{repo}</a><code>{owner}</code></div>'.format(
                    url=_text(row.get("repo_url"), "#"),
                    repo=_text(row.get("repo_name")),
                    owner=_text(row.get("owner")),
                ),
                '<div class="cell-stack"><div>{category}</div><span class="pill">{stars}</span></div>'.format(
                    category=_text(row.get("category")),
                    stars=_text(row.get("stars_observed")),
                ),
                """
                <div class="cell-stack">
                  <div><strong>Business</strong><br>{business}</div>
                  <div><strong>Local fit</strong><br>{local_fit}</div>
                  <div><strong>Risk</strong><br>{risk}</div>
                </div>
                """.format(
                    business=_text(row.get("business_tie_in")),
                    local_fit=_text(row.get("local_fit")),
                    risk=_text(row.get("risk_notes")),
                ),
                _text(row.get("recommended_next_step")),
            ]
        )

    body = """
    <section class="grid">
      {ready_stat}
      {artifacts_stat}
      {drafts_stat}
      {confirmed_stat}
      {specialty_stat}
      {projects_stat}
    </section>
    <section>
      <h2>Product Loop</h2>
      {stages}
    </section>
    <section style="margin-top:16px">
      <h2>Abliterated / Dolphin Lane</h2>
      {specialty_table}
    </section>
    <section style="margin-top:16px">
      <h2>GitHub Project Radar</h2>
      {project_table}
    </section>
    <section style="margin-top:16px">
      <h2>Ready Queue</h2>
      {queue}
    </section>
    <section style="margin-top:16px">
      <h2>Benchmark Artifacts</h2>
      {artifacts_table}
    </section>
    """.format(
        ready_stat=_stat_card("Ready candidates", len(ready_candidates), "ti-list-check"),
        artifacts_stat=_stat_card("Artifacts", len(artifacts), "ti-archive"),
        drafts_stat=_stat_card("Draft scores", score_counts["draft"], "ti-edit"),
        confirmed_stat=_stat_card("Confirmed scores", score_counts["confirmed"], "ti-circle-check"),
        specialty_stat=_stat_card(
            "Abliterated / Dolphin", len(specialty_candidates), "ti-sparkles"
        ),
        projects_stat=_stat_card("GitHub projects", len(projects), "ti-brand-github"),
        stages=_table(
            ["Stage", "State", "Signal", "Next action"],
            stage_rows,
            table_class="workflow-table",
        ),
        specialty_table=_table(
            ["Candidate", "Lane", "Local fit", "Proposed eval"],
            specialty_rows,
            empty_message="No abliterated or Dolphin candidates are registered yet.",
            table_class="lab-queue",
        ),
        project_table=_table(
            ["Project", "Signal", "Business fit", "Next step"],
            project_rows,
            empty_message="No GitHub projects are ready for review yet.",
            table_class="project-table",
        ),
        queue=_table(
            ["Candidate", "Status", "State", "Run", "Next command"],
            queue_rows,
            empty_message="No ready candidates. Approve one in radar first.",
            table_class="lab-queue",
        ),
        artifacts_table=_table(
            [
                "Run",
                "Responses",
                "Scores",
                "Draft",
                "Decision",
                "CSV",
                "Dashboard",
                "Import action",
                "Import/report commands",
            ],
            artifact_rows,
            empty_message="No benchmark artifacts found.",
        ),
    )
    return _layout("Lab Dashboard", "/lab", body)


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
        ),
    )
    return _layout("Model Runs", "/runs", body)


def _compare(conn, query=None):
    headers = ["Model", "Score", "Status", "Label"] + [
        field.replace("_", " ").title() for field in METRIC_FIELDS
    ]
    rows = []
    all_scores = db.list_score_details(conn)
    scores = _real_rows(all_scores)
    filters = _score_filter_values(query or {})
    filtered_scores = _filter_scores(scores, filters)
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
    body = """
    {notice}
    {filters}
    <h2>Compare Models{filtered_count}</h2>
    {table}
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_scores))),
        filters=_compare_filters(scores, filters),
        filtered_count=(
            f" ({len(filtered_scores)} of {len(scores)})" if any(filters.values()) else ""
        ),
        table=_table(
            headers,
            rows,
            empty_message="No real confirmed or draft score rows match these filters.",
        ),
    )
    return _layout("Compare Models", "/compare", body)


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
        repo = '<a href="{url}">{name}</a>'.format(
            url=_text(row.get("repo_url"), "#"),
            name=_text(row.get("repo_name")),
        )
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

    body = """
    <section class="grid">
      {projects_stat}
      {ready_stat}
      {watchlist_stat}
      {local_stat}
      {priority_stat}
    </section>
    <section>
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
        ),
    )
    return _layout("Project Radar", "/projects", body)


def _artifact_detail(
    conn,
    benchmark_run_id,
    registry_path=CANDIDATE_REGISTRY_PATH,
    database_path=DEFAULT_DASHBOARD_DB,
    enable_import_actions=False,
    action_token="",
):
    candidates = _load_radar_candidates(registry_path)
    candidate = next(
        (row for row in candidates if row.get("benchmark_run_id") == benchmark_run_id),
        None,
    )
    artifact_dir = EVAL_RESULTS_DIR / benchmark_run_id
    if candidate is None and not artifact_dir.exists():
        return _layout("Benchmark Artifact", "", "<h2>Artifact not found</h2>")

    dashboard_run = _dashboard_runs_by_benchmark_id(conn).get(benchmark_run_id)
    decisions_by_model = _latest_decisions_by_model_id(conn)
    dashboard_state = _import_state_for_run(dashboard_run, decisions_by_model)
    candidate_state = (
        _pill(candidate.get("status")) if candidate else '<span class="empty">not registered</span>'
    )
    artifact_name = (
        candidate.get("model_name")
        if candidate
        else dashboard_run["model_name"]
        if dashboard_run
        else benchmark_run_id
    )
    file_rows = []
    if artifact_dir.exists():
        for path in sorted(artifact_dir.iterdir(), key=lambda item: item.name.lower()):
            kind = "directory" if path.is_dir() else "file"
            file_rows.append([_text(path.name), _text(kind), _path_cell(_relative_path(path))])

    body = """
    <div class="split">
      <section class="panel">
        <h2>{name}</h2>
        <p><strong>Candidate:</strong> {status}</p>
        <p><strong>Benchmark run:</strong> <code>{run_id}</code></p>
        <p><strong>Dashboard:</strong> {dashboard_state}</p>
      </section>
      <section class="panel">
        <h2>Radar Context</h2>
        <p><strong>Source packet:</strong> {source}</p>
        <p><strong>Report:</strong> {report}</p>
      </section>
    </div>
    <section class="panel" style="margin-top:16px">
      <h2>Dashboard Import</h2>
      <p>This imports only existing local CSV files from this artifact's <code>dashboard-import</code> directory.</p>
      {import_control}
      {import_guidance}
    </section>
    <section style="margin-top:16px"><h2>Artifact Files</h2>{files}</section>
    """.format(
        name=_text(artifact_name),
        status=candidate_state,
        run_id=_text(benchmark_run_id),
        dashboard_state=dashboard_state,
        source=_path_cell(candidate.get("source_packet_path") if candidate else ""),
        report=_path_cell(candidate.get("report_path") if candidate else ""),
        import_control=_artifact_import_control(
            benchmark_run_id,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
            eval_results_dir=EVAL_RESULTS_DIR,
        ),
        import_guidance=_artifact_import_guidance(
            benchmark_run_id,
            database_path,
            EVAL_RESULTS_DIR,
        ),
        files=_table(
            ["Name", "Type", "Path"], file_rows, empty_message="Artifact directory not found."
        ),
    )
    return _layout("Benchmark Artifact", "", body)


def _model_detail(conn, model_id):
    detail = db.get_model_detail(conn, model_id)
    if detail is None:
        return _layout("Model Detail", "", "<h2>Model not found</h2>")
    model = detail["model"]
    if _is_demo_row(model):
        return _layout(
            "Demo Model Detail",
            "",
            """
            <section class="panel">
              <h2>Demo Fixture Model</h2>
              <p><strong>{name}</strong> is bundled demo data for dashboard testing, not an installed model.</p>
              <p><a href="/demo">View demo data</a> or return to <a href="/">real benchmark results</a>.</p>
            </section>
            """.format(name=_text(model["model_name"])),
        )
    run_rows = []
    for row in detail["runs"]:
        run_rows.append(
            [
                _text(row["date_tested"]),
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
                _text(row["run_notes"]),
            ]
        )
    decision_rows = []
    for row in detail["decisions"]:
        decision_rows.append(
            [
                _text(row["created_at"]),
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    body = """
    <div class="split">
      <section class="panel">
        <h2>{name}</h2>
        <p><strong>Family:</strong> {family}</p>
        <p><strong>Provider:</strong> {provider}</p>
        <p><strong>Parameters:</strong> {params}B</p>
        <p><strong>License:</strong> {license}</p>
        <p><strong>Source:</strong> <a href="{source}">{source}</a></p>
        <p>{notes}</p>
      </section>
      <section class="panel">
        <h2>Current Read</h2>
        <p>{summary}</p>
      </section>
    </div>
    <section style="margin-top:16px"><h2>Runs</h2>{runs}</section>
    <section style="margin-top:16px"><h2>Decisions</h2>{decisions}</section>
    """.format(
        name=_text(model["model_name"]),
        family=_text(model["model_family"]),
        provider=_text(model["provider"]),
        params=_number(model["params_b"], 1),
        license=_text(model["license"]),
        source=_text(model["source_url"], "#"),
        notes=_text(model["notes"]),
        summary=_text(detail["decisions"][0]["best_use_case"] if detail["decisions"] else ""),
        runs=_table(
            [
                "Date",
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
                "Notes",
            ],
            run_rows,
        ),
        decisions=_table(
            ["Created", "Decision", "Keep", "Best use case", "Weakness", "Retest"],
            decision_rows,
        ),
    )
    return _layout("Model Detail", "", body)


def _storage(conn, query=None):
    rows = []
    all_decisions = db.list_decisions(conn)
    decisions = _real_rows(all_decisions)
    filters = _storage_filter_values(query or {})
    filtered_decisions = _filter_storage_decisions(decisions, filters)
    for row in filtered_decisions:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["model_id"], name=_text(row["model_name"])
                ),
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    body = """
    {notice}
    <section class="panel" style="margin-bottom:16px">
      <h2>Storage / Install Status</h2>
      <p>This is a benchmark decision log. It is not an installed-model inventory scanner.</p>
      <p>Use <a href="/inventory">Installed Models</a> to check local LM Studio and Ollama inventory.</p>
    </section>
    {filters}
    <h2>Decision Log{filtered_count}</h2>
    {table}
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_decisions))),
        filters=_storage_filters(decisions, filters),
        filtered_count=(
            f" ({len(filtered_decisions)} of {len(decisions)})" if any(filters.values()) else ""
        ),
        table=_table(
            ["Model", "Decision", "Keep installed", "Best use case", "Weakness", "Retest"],
            rows,
            empty_message="No real storage/install decisions match these filters.",
        ),
    )
    return _layout("Storage / Install Status", "/storage", body)


def _reports(conn, database_path):
    report = generate_markdown_report(database_path)
    body = f"""
    <section class="panel" style="margin-bottom:16px">
      <h2>What This Means</h2>
      <p>Ranked models are imported benchmark results, not installed-model inventory.</p>
      <p>Radar candidates are possible models to evaluate, not scored models.</p>
      <p>Installed Models checks local LM Studio and Ollama inventory on demand.</p>
      <p>Scores are valid only after raw responses, confirmed scores, and decisions exist.</p>
      <p>Demo rows are examples only and are hidden from real dashboard views by default.</p>
    </section>
    <h2>Reports</h2><pre class="report">{escape(report)}</pre>
    """
    return _layout("Reports", "/reports", body)


def _demo(conn):
    summaries = _demo_rows(db.list_model_summaries(conn))
    rows = []
    for row in summaries:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["id"], name=_text(row["model_name"])
                ),
                _text(row["provider"]),
                _text(row["backend"]),
                _number(row["total_score"], 2),
                _pill(row["final_label"]),
                _text(row["decision"]),
            ]
        )
    body = """
    <section class="panel" style="margin-bottom:16px">
      <h2>Demo Data</h2>
      <p>These fixture rows are bundled examples for dashboard QA. They are not installed on this machine and are hidden from real dashboard views.</p>
    </section>
    {table}
    """.format(
        table=_table(
            ["Model", "Provider", "Backend", "Score", "Label", "Decision"],
            rows,
            empty_message="No demo fixture rows found.",
        )
    )
    return _layout("Demo Data", "", body)


def make_handler(
    database_path,
    enable_run_tests=False,
    enable_import_actions=False,
    action_token="",
    run_test_timeout=3600,
    inventory_timeout=5,
    enable_inventory_refresh=True,
):
    inventory_cache = {"result": None}

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            try:
                with db.connect(database_path) as conn:
                    db.create_schema(conn)
                    html = self._route(parsed.path, parse_qs(parsed.query), conn)
                self.send_response(200)
            except Exception as exc:
                html = _layout("Error", "", f"<h2>Error</h2><p>{_text(exc)}</p>")
                self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def do_POST(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path not in (
                    "/actions/run-test",
                    "/actions/refresh-inventory",
                    "/actions/import-artifact",
                ):
                    html = _layout("Not Found", "", "<h2>Page not found</h2>")
                    self.send_response(404)
                else:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 4096:
                        raise ValueError("Request body too large.")
                    form = parse_qs(self.rfile.read(length).decode("utf-8"))
                    token = _query_value(form, "token")
                    if token != action_token:
                        raise ValueError("Invalid action token.")
                    if parsed.path == "/actions/refresh-inventory":
                        if not enable_inventory_refresh:
                            html = _layout(
                                "Inventory Refresh Disabled",
                                "",
                                "<h2>Inventory refresh disabled</h2><p>Refresh is available only on a localhost or loopback dashboard bind.</p>",
                            )
                            self.send_response(403)
                        else:
                            inventory_cache["result"] = _refresh_inventory(inventory_timeout)
                            html = _inventory(
                                inventory_result=inventory_cache["result"],
                                action_token=action_token,
                                enable_run_tests=enable_run_tests,
                                enable_refresh=enable_inventory_refresh,
                            )
                            self.send_response(200)
                    elif parsed.path == "/actions/import-artifact":
                        if not enable_import_actions:
                            html = _layout(
                                "Import Actions Disabled",
                                "",
                                "<h2>Import actions disabled</h2><p>Restart the dashboard with <code>--enable-import-actions</code>.</p>",
                            )
                            self.send_response(403)
                        else:
                            benchmark_run_id = _query_value(form, "benchmark_run_id")
                            result = _import_artifact(
                                benchmark_run_id,
                                database_path,
                                EVAL_RESULTS_DIR,
                            )
                            html = _import_action_page(result)
                            self.send_response(200)
                    elif not enable_run_tests:
                        html = _layout(
                            "Run Tests Disabled",
                            "",
                            "<h2>Run tests disabled</h2><p>Restart the dashboard with <code>--enable-run-tests</code>.</p>",
                        )
                        self.send_response(403)
                    else:
                        candidate_id = _query_value(form, "candidate_id")
                        result = _run_candidate_test(
                            candidate_id,
                            CANDIDATE_REGISTRY_PATH,
                            EVAL_RESULTS_DIR,
                            run_test_timeout,
                        )
                        html = _run_action_page(result)
                        self.send_response(200)
            except Exception as exc:
                html = _layout("Action Error", "", f"<h2>Action Error</h2><p>{_text(exc)}</p>")
                self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, fmt, *args):
            return

        def _route(self, path, query, conn):
            if path == "/lab":
                return _lab(
                    conn,
                    enable_run_tests=enable_run_tests,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                    database_path=database_path,
                )
            if path == "/":
                return _overview(conn, query)
            if path == "/runs":
                return _runs(conn, query)
            if path == "/compare":
                return _compare(conn, query)
            if path == "/inventory":
                return _inventory(
                    query=query,
                    inventory_result=inventory_cache["result"],
                    action_token=action_token,
                    enable_run_tests=enable_run_tests,
                    enable_refresh=enable_inventory_refresh,
                )
            if path == "/radar":
                return _radar(conn, query)
            if path == "/specialty":
                return _specialty(conn, query)
            if path == "/projects":
                return _projects(query)
            if path == "/storage":
                return _storage(conn, query)
            if path == "/reports":
                return _reports(conn, database_path)
            if path == "/demo":
                return _demo(conn)
            if path.startswith("/artifacts/"):
                benchmark_run_id = path.rsplit("/", 1)[-1]
                return _artifact_detail(
                    conn,
                    benchmark_run_id,
                    database_path=database_path,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                )
            if path.startswith("/models/"):
                model_id = int(path.rsplit("/", 1)[-1])
                return _model_detail(conn, model_id)
            return _layout("Not Found", "", "<h2>Page not found</h2>")

    return DashboardHandler


def serve(
    database_path,
    host="127.0.0.1",
    port=8765,
    enable_run_tests=False,
    enable_import_actions=False,
    run_test_timeout=3600,
    inventory_timeout=5,
):
    if enable_run_tests and not _is_loopback_host(host):
        raise ValueError("Run-test actions require a localhost or loopback bind host.")
    if enable_import_actions and not _is_loopback_host(host):
        raise ValueError("Import actions require a localhost or loopback bind host.")
    enable_inventory_refresh = _is_loopback_host(host)
    action_token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(
        (host, port),
        make_handler(
            database_path,
            enable_run_tests=enable_run_tests,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
            run_test_timeout=run_test_timeout,
            inventory_timeout=inventory_timeout,
            enable_inventory_refresh=enable_inventory_refresh,
        ),
    )
    print(f"Serving Local Model Dashboard at http://{host}:{port}", flush=True)
    if enable_run_tests:
        print("Dashboard run-test actions enabled for local candidates.", flush=True)
    if enable_import_actions:
        print("Dashboard artifact import actions enabled for local CSV artifacts.", flush=True)
    if enable_inventory_refresh:
        print("Installed-model inventory refresh enabled for local runtimes.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
