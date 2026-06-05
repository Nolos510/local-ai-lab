"""A dependency-free local web dashboard for model eval results."""

import csv
import ipaddress
import json
import shutil
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import subprocess
import sys
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from . import db
from .reports import generate_markdown_report
from .scoring import METRIC_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_REGISTRY_PATH = REPO_ROOT / "data" / "model_registry" / "candidates.csv"
PROJECT_REGISTRY_PATH = REPO_ROOT / "data" / "project_registry" / "github_repos.csv"
EVAL_RESULTS_DIR = REPO_ROOT / "data" / "eval_results"
HARNESS_PATH = REPO_ROOT / "evals" / "local-llm-benchmark" / "harness.py"
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


def _text(value, fallback=""):
    return escape(fallback if value is None else str(value))


def _number(value, digits=1, fallback=""):
    if value is None:
        return fallback
    return "{:.{}f}".format(float(value), digits)


def _pill(value):
    label = _text(value, "UNLABELED")
    return '<span class="pill">{}</span>'.format(label)


def _status_pill(value):
    status = value or "confirmed"
    class_name = "pill score-status"
    if status == "draft":
        class_name += " draft"
    return '<span class="{}">{}</span>'.format(class_name, _text(status.upper()))


def _table(headers, rows, empty_message="No rows yet.", table_class=""):
    if not rows:
        return '<p class="empty">{}</p>'.format(escape(empty_message))
    header_html = "".join("<th>{}</th>".format(escape(header)) for header in headers)
    row_html = []
    for row in rows:
        row_html.append("<tr>{}</tr>".format("".join("<td>{}</td>".format(cell) for cell in row)))
    class_attr = ' class="{}"'.format(escape(table_class)) if table_class else ""
    table = "<table{}><thead><tr>{}</tr></thead><tbody>{}</tbody></table>".format(
        class_attr, header_html, "".join(row_html)
    )
    return '<div class="table-wrap">{}</div>'.format(table)


def _query_value(query, key):
    value = query.get(key, "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _option(value, label, selected):
    selected_attr = " selected" if value == selected else ""
    return '<option value="{}"{}>{}</option>'.format(
        _text(value), selected_attr, _text(label)
    )


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
    provider = str(row["provider"] if "provider" in row.keys() else row.get("provider", "") or "")
    source_url = str(
        row["source_url"] if "source_url" in row.keys() else row.get("source_url", "") or ""
    )
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
    return """
    <section class="panel" style="margin-bottom:16px">
      <h2>Real Data View</h2>
      <p>This page hides {count} demo fixture model rows. Demo rows are examples for dashboard testing, not installed models.</p>
      <p><a href="/demo">View demo data</a> when you want to inspect fixture examples.</p>
    </section>
    """.format(count=demo_count)


def _load_radar_candidates(path=CANDIDATE_REGISTRY_PATH):
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {key: (value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]


def _load_project_repos(path=PROJECT_REGISTRY_PATH):
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {key: (value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]


def _radar_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "status": _query_value(query, "status"),
        "family": _query_value(query, "family"),
        "runtime": _query_value(query, "runtime"),
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
    clear_link = '<a class="clear-link" href="/radar">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters" method="get" action="/radar">
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
        clear_link=clear_link,
    )


def _project_filters(projects, filters):
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in _field_options(projects, "status")
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


def _path_cell(value):
    if not value:
        return '<span class="empty">None</span>'
    return "<code>{}</code>".format(_text(value))


def _external_link(url, label):
    value = str(url or "").strip()
    if not value:
        return '<span class="empty">None</span>'
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        return '<span class="empty">Unsupported link</span>'
    return '<a href="{url}" target="_blank" rel="noreferrer">{label}</a>'.format(
        url=_text(value),
        label=_text(label),
    )


def _candidate_review_links(row):
    links = []
    for field, label in (
        ("model_page_url", "Model/source page"),
        ("github_url", "GitHub"),
        ("lm_studio_url", "LM Studio"),
        ("ollama_url", "Ollama"),
    ):
        if row.get(field):
            links.append("<div>{}</div>".format(_external_link(row.get(field), label)))
    if not links:
        return '<span class="empty">No verified model/store links</span>'
    return "".join(links)


def _candidate_availability(row):
    runtime = row.get("runtime_availability") or row.get("format_or_runtime") or "unknown"
    return """
    <div class="cell-stack">
      <div><strong>Runtime availability</strong><br>{runtime}</div>
      <div><strong>Model/store links</strong><br>{links}</div>
    </div>
    """.format(
        runtime=_text(runtime),
        links=_candidate_review_links(row),
    )


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
            '<div class="empty">Runner: {}</div>'
        ).format(_text(_candidate_runner_label(row)))
    if not enable_run_tests:
        return (
            '<div class="cell-stack">'
            '<span class="empty">Run button disabled</span>'
            '<div>Restart with <code>--enable-run-tests</code></div>'
            '<div><strong>Runner</strong><br>{runner}</div>'
            '<div><strong>Model id</strong><br><code>{model_id}</code></div>'
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
        candidate = "{}-r{}".format(base, index)
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


def _parse_lmstudio_inventory(ls_stdout, ps_stdout=""):
    loaded_ids = set()
    try:
        ps_data = json.loads(ps_stdout) if ps_stdout.strip() else []
    except json.JSONDecodeError:
        ps_data = []
    for row in _collect_json_objects(ps_data):
        if not _looks_like_lmstudio_model(row):
            continue
        value = _first_value(
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
        if value:
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
        status = (
            "loaded"
            if model_id.lower() in loaded_ids
            or display_name.lower() in loaded_ids
            or (path_id and path_id in loaded_ids)
            else "installed"
        )
        models.append(
            {
                "runtime": "LM Studio",
                "model_id": model_id,
                "display_name": display_name or model_id,
                "status": status,
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
        if lm_ls["status"] == "ok":
            models.extend(_parse_lmstudio_inventory(lm_ls["stdout"], lm_ps["stdout"]))
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
    matches = [
        row
        for row in candidates
        if row.get("local_model_id", "").lower() == model_id
        or row.get("model_name", "").lower() == model_id
    ]
    if len(matches) == 1:
        return "registered", matches[0]
    if len(matches) > 1:
        return "ambiguous", None
    return "unregistered", None


def _inventory(
    query=None,
    inventory_result=None,
    action_token="",
    enable_run_tests=False,
    enable_refresh=True,
):
    candidates = _load_radar_candidates()
    result = inventory_result
    check_rows = []
    model_rows = []
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
            candidate_cell = (
                '<a href="/radar?q={id}">{id}</a>'.format(id=_text(candidate["candidate_id"]))
                if candidate
                else _pill(match_state)
            )
            action_cell = (
                _run_test_control(candidate, enable_run_tests, action_token)
                if candidate and _candidate_run_ready(candidate)
                else '<span class="empty">Register exact local model id first</span>'
            )
            model_rows.append(
                [
                    _text(model["runtime"]),
                    "<code>{}</code>".format(_text(model["model_id"])),
                    _text(model["display_name"]),
                    _pill(model["status"]),
                    candidate_cell,
                    action_cell,
                ]
            )

    body = """
    <section class="panel" style="margin-bottom:16px">
      <h2>Installed Models</h2>
      <p>This page checks local runtime inventory on demand. It does not download, install, benchmark, score, or import models.</p>
      <form class="inline-form" method="post" action="/actions/refresh-inventory">
        <input type="hidden" name="token" value="{token}">
        <button type="submit"{disabled}>Refresh Inventory</button>
      </form>
      {disabled_note}
      <p class="empty">Last refresh: {checked_at}</p>
    </section>
    <section>
      <h2>Detected Models</h2>
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
        models=_table(
            ["Runtime", "Model id", "Display name", "Status", "Registry match", "Action"],
            model_rows,
            empty_message="No inventory refresh has run yet.",
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
        raise ValueError("Unsupported local runner: {}".format(runner))
    return init_command, capture_command


def _run_candidate_test(candidate_id, registry_path, eval_results_dir, timeout):
    candidates = _load_radar_candidates(registry_path)
    row = next((item for item in candidates if item.get("candidate_id") == candidate_id), None)
    if row is None:
        raise ValueError("Candidate not found: {}".format(candidate_id))
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
        return '<p class="empty">{} did not run.</p>'.format(_text(label))
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
    return '<a href="/artifacts/{id}"><code>{id}</code></a>'.format(
        id=_text(benchmark_run_id)
    )


def _benchmark_run_id_from_notes(notes):
    for part in str(notes or "").split("|"):
        part = part.strip()
        if part.startswith("benchmark_run_id="):
            return part.split("=", 1)[1].strip()
    return ""


def _artifact_link_from_notes(notes):
    return _artifact_link(_benchmark_run_id_from_notes(notes))


def _command_block(command):
    return '<pre class="command">{}</pre>'.format(_text(command))


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
        '<div>{score} {status}</div>'
        '<div>decision: {decision}</div>'
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


def _layout(title, current_path, body):
    nav = []
    for path, label in NAV_ITEMS:
        active = " active" if current_path == path else ""
        nav.append('<a class="nav{}" href="{}">{}</a>'.format(active, path, escape(label)))
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - Local Model Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f5ef;
      --panel: #ffffff;
      --ink: #202124;
      --muted: #62676f;
      --line: #ded9cf;
      --accent: #196f6b;
      --accent-2: #9b4d1f;
      --good: #1f7a42;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      line-height: 1.45;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: #fffdf8;
    }}
    .topbar {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 18px 20px 12px;
    }}
    h1 {{
      margin: 0 0 14px;
      font-size: 28px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .nav {{
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 7px 10px;
      text-decoration: none;
      background: #fbfaf6;
    }}
    .nav.active {{
      border-color: var(--accent);
      color: #ffffff;
      background: var(--accent);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .stat, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 4px;
    }}
    .stat .value {{
      font-size: 26px;
      font-weight: 700;
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(140px, 1fr)) auto;
      gap: 10px;
      align-items: end;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin: 0 0 14px;
    }}
    .filters-compact {{
      grid-template-columns: minmax(220px, 2fr) repeat(2, minmax(140px, 1fr)) auto;
    }}
    .field label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin: 0 0 4px;
    }}
    input, select {{
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fffdf8;
      color: var(--ink);
      font: inherit;
      padding: 7px 9px;
    }}
    button {{
      min-height: 36px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      font: inherit;
      font-weight: 700;
      padding: 7px 12px;
      cursor: pointer;
    }}
    .inline-form {{
      display: grid;
      gap: 6px;
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
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    table {{
      width: 100%;
      min-width: 760px;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 9px;
      text-align: left;
      vertical-align: top;
      white-space: normal;
      overflow-wrap: anywhere;
    }}
    th {{
      background: #ede7dc;
      color: #393b3f;
      font-size: 13px;
    }}
    .table-wrap {{
      width: 100%;
      overflow-x: auto;
      border-radius: 8px;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    a {{ color: var(--accent); }}
    .pill {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 8px;
      background: #e4f0ed;
      color: #185a55;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .score-status {{
      background: #e9ecef;
      color: #3d434a;
      text-transform: uppercase;
    }}
    .score-status.draft {{
      background: #fff1d6;
      color: #7a4a10;
    }}
    .empty {{ color: var(--muted); }}
    .report {{
      background: #1e2227;
      color: #f6f0e6;
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      white-space: pre-wrap;
    }}
    .command {{
      margin: 0;
      background: #1e2227;
      color: #f6f0e6;
      border-radius: 8px;
      padding: 10px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 13px;
    }}
    .workflow-table td:nth-child(1) {{
      width: 150px;
      font-weight: 700;
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
      gap: 16px;
    }}
    .cell-stack {{
      display: grid;
      gap: 6px;
    }}
    .cell-stack strong {{
      color: var(--muted);
      font-size: 12px;
    }}
    .radar-table {{
      min-width: 1120px;
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
    .radar-table th:nth-child(7),
    .radar-table td:nth-child(7) {{
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
      th, td {{ padding: 8px 7px; }}
    }}
  </style>
</head>
<body>
  <header><div class="topbar"><h1>Local Model Performance Dashboard</h1><nav>{nav}</nav></div></header>
  <main>{body}</main>
</body>
</html>""".format(
        title=escape(title), nav="".join(nav), body=body
    )


def _overview(conn, query=None):
    counts = _real_counts(conn)
    all_summaries = db.list_model_summaries(conn)
    summaries = _real_rows(all_summaries)
    filters = _filter_values(query or {})
    filtered_summaries = _filter_summaries(summaries, filters)
    score_values = [
        float(row["total_score"])
        for row in summaries
        if row["total_score"] not in (None, "")
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
      <div class="stat"><div class="label">Models</div><div class="value">{models}</div></div>
      <div class="stat"><div class="label">Runs</div><div class="value">{runs}</div></div>
      <div class="stat"><div class="label">Average score</div><div class="value">{avg}</div></div>
      <div class="stat"><div class="label">Kept installed</div><div class="value">{kept}</div></div>
    </section>
    <section>
      {filters}
      <h2>Ranked Local Models{filtered_count}</h2>
      {table}
    </section>
    """.format(
        notice=_real_data_notice(counts["demo_models"]),
        models=counts["models"],
        runs=counts["model_runs"],
        avg=_number(avg_score, 1, "0.0"),
        kept=keep_count,
        filters=_overview_filters(summaries, filters),
        filtered_count=(
            " ({} of {})".format(len(filtered_summaries), len(summaries))
            if any(filters.values())
            else ""
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
    action_token="",
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
    ready_candidates = [
        row for row in candidates if row.get("status") == "ready_for_eval"
    ]
    specialty_candidates = [row for row in candidates if _is_specialty_candidate(row)]
    ready_projects = [row for row in projects if row.get("status") == "ready_for_review"]
    artifact_ids = {row["benchmark_run_id"] for row in artifacts}
    linked_imports = len(artifact_ids & imported_run_ids)

    stage_rows = [
        [
            "Radar",
            _pill("ready"),
            "{} ready candidates".format(len(ready_candidates)),
            '<a href="/radar?status=ready_for_eval">Review ready queue</a>',
        ],
        [
            "Project Radar",
            _pill("review"),
            "{} GitHub repos tracked".format(len(projects)),
            '<a href="/projects">Review project opportunities</a>',
        ],
        [
            "Benchmark",
            _pill("active"),
            "{} artifact directories".format(len(artifacts)),
            "Run a local endpoint benchmark for the next approved candidate.",
        ],
        [
            "Score",
            _status_pill("draft") if score_counts["draft"] else _status_pill("confirmed"),
            "{} draft / {} confirmed".format(
                score_counts["draft"], score_counts["confirmed"]
            ),
            "Use draft scores for review, then export confirmed scores.",
        ],
        [
            "Import",
            _pill("linked"),
            "{} artifacts linked to active DB".format(linked_imports),
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
            '<a href="/models/{id}">imported</a>'.format(id=model_id)
            if model_id
            else '<span class="empty">not imported</span>'
        )
        artifact_state = (
            _artifact_link(run_id)
            if run_id
            else '<span class="empty">no artifact yet</span>'
        )
        proposed_run_id = run_id or "YYYYMMDD-{}-local".format(
            row.get("candidate_id", "candidate").replace("_", "-")
        )
        command = "\n".join(
            [
                "python3 evals/local-llm-benchmark/harness.py init-run \\",
                "  --benchmark-run-id {} \\".format(proposed_run_id),
                '  --model-name "{}" \\'.format(row.get("model_name", "")),
                '  --backend "Local OpenAI-compatible" \\',
                "  --temperature 0.2 \\",
                "  --top-p 0.9",
                "",
                "python3 evals/local-llm-benchmark/harness.py run-local \\",
                "  --run-dir data/eval_results/{} \\".format(proposed_run_id),
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
        dashboard_state = _import_state_for_run(
            dashboard_runs.get(run_id), decisions_by_model
        )
        artifact_rows.append(
            [
                _artifact_link(run_id),
                _text(row["raw_responses"]),
                _text(row["scores"]),
                _text(row["draft_scores"]),
                _text(row["decision"]),
                _text(row["dashboard_import"]),
                dashboard_state,
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
      <div class="stat"><div class="label">Ready candidates</div><div class="value">{ready}</div></div>
      <div class="stat"><div class="label">Artifacts</div><div class="value">{artifacts}</div></div>
      <div class="stat"><div class="label">Draft scores</div><div class="value">{drafts}</div></div>
      <div class="stat"><div class="label">Confirmed scores</div><div class="value">{confirmed}</div></div>
      <div class="stat"><div class="label">Abliterated / Dolphin</div><div class="value">{specialty}</div></div>
      <div class="stat"><div class="label">GitHub projects</div><div class="value">{projects}</div></div>
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
        ready=len(ready_candidates),
        artifacts=len(artifacts),
        drafts=score_counts["draft"],
        confirmed=score_counts["confirmed"],
        specialty=len(specialty_candidates),
        projects=len(projects),
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
            ],
            artifact_rows,
            empty_message="No benchmark artifacts found.",
        ),
    )
    return _layout("Lab Dashboard", "/lab", body)


def _runs(conn):
    rows = []
    all_runs = db.list_runs(conn)
    for row in _real_rows(all_runs):
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
    body = "{}<h2>Model Runs</h2>{}".format(
        _real_data_notice(len(_demo_rows(all_runs))),
        _table(
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
            empty_message="No real benchmark runs imported yet.",
        )
    )
    return _layout("Model Runs", "/runs", body)


def _compare(conn):
    headers = ["Model", "Score", "Status", "Label"] + [
        field.replace("_", " ").title() for field in METRIC_FIELDS
    ]
    rows = []
    all_scores = db.list_score_details(conn)
    for row in _real_rows(all_scores):
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
    body = "{}<h2>Compare Models</h2>{}".format(
        _real_data_notice(len(_demo_rows(all_scores))),
        _table(headers, rows, empty_message="No real confirmed or draft score rows imported yet."),
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

    rows = []
    for row in filtered_candidates:
        model_id = model_links.get(row.get("model_name", "").lower())
        model_name = _text(row.get("model_name"))
        if model_id:
            model_name = '<a href="/models/{id}">{name}</a>'.format(
                id=model_id, name=model_name
            )
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
                _text(row.get("proposed_eval")),
                links,
            ]
        )

    body = """
    <section class="grid">
      <div class="stat"><div class="label">Candidates</div><div class="value">{candidates}</div></div>
      <div class="stat"><div class="label">Ready for eval</div><div class="value">{ready}</div></div>
      <div class="stat"><div class="label">Watchlist</div><div class="value">{watchlist}</div></div>
      <div class="stat"><div class="label">Linked artifacts</div><div class="value">{linked}</div></div>
      <div class="stat"><div class="label">Abliterated / Dolphin</div><div class="value">{specialty}</div></div>
    </section>
    <section>
      {filters}
      <h2>Radar Candidates{filtered_count}</h2>
      {table}
    </section>
    """.format(
        candidates=len(candidates),
        ready=ready_count,
        watchlist=watchlist_count,
        linked=linked_count,
        specialty=specialty_count,
        filters=_radar_filters(candidates, filters),
        filtered_count=(
            " ({} of {})".format(len(filtered_candidates), len(candidates))
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
                "Proposed eval",
                "Links",
            ],
            rows,
            empty_message="No candidates match these filters.",
            table_class="radar-table",
        ),
    )
    return _layout("Radar Candidates", "/radar", body)


def _specialty(conn, registry_path=CANDIDATE_REGISTRY_PATH):
    candidates = [
        row
        for row in _load_radar_candidates(registry_path)
        if _is_specialty_candidate(row)
    ]
    model_links = _dashboard_model_links(conn)
    ready_count = sum(1 for row in candidates if row.get("status") == "ready_for_eval")
    watchlist_count = sum(1 for row in candidates if row.get("status") == "watchlist")

    rows = []
    for row in candidates:
        model_id = model_links.get(row.get("model_name", "").lower())
        model_name = _text(row.get("model_name"))
        if model_id:
            model_name = '<a href="/models/{id}">{name}</a>'.format(
                id=model_id, name=model_name
            )
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
                _text(row.get("proposed_eval")),
                _artifact_link(row.get("benchmark_run_id")),
            ]
        )

    body = """
    <section class="grid">
      <div class="stat"><div class="label">Specialty candidates</div><div class="value">{total}</div></div>
      <div class="stat"><div class="label">Ready for eval</div><div class="value">{ready}</div></div>
      <div class="stat"><div class="label">Watchlist</div><div class="value">{watchlist}</div></div>
    </section>
    <section class="panel" style="margin-bottom:16px">
      <h2>Abliterated / Dolphin Models</h2>
      <p>This tab collects specialty radar candidates for refusal-boundary and Dolphin-style model testing. They remain candidates until local evidence, scores, and decisions exist.</p>
      <p>The same rows remain searchable in <a href="/radar?q=abliterated">Radar Candidates</a>.</p>
    </section>
    {table}
    """.format(
        total=len(candidates),
        ready=ready_count,
        watchlist=watchlist_count,
        table=_table(
            [
                "Candidate",
                "Lane",
                "Availability",
                "Review notes",
                "Proposed eval",
                "Artifact",
            ],
            rows,
            empty_message="No abliterated or Dolphin candidates are registered yet.",
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
      <div class="stat"><div class="label">Projects</div><div class="value">{projects}</div></div>
      <div class="stat"><div class="label">Ready for review</div><div class="value">{ready}</div></div>
      <div class="stat"><div class="label">Watchlist</div><div class="value">{watchlist}</div></div>
      <div class="stat"><div class="label">Local/self-host signal</div><div class="value">{local_count}</div></div>
      <div class="stat"><div class="label">Priority 5</div><div class="value">{priority_five}</div></div>
    </section>
    <section>
      {filters}
      <h2>Project Radar{filtered_count}</h2>
      {table}
    </section>
    """.format(
        projects=len(projects),
        ready=ready_count,
        watchlist=watchlist_count,
        local_count=local_count,
        priority_five=sum(1 for row in projects if _project_priority_score(row) == 5),
        filters=_project_filters(projects, filters),
        filtered_count=(
            " ({} of {})".format(len(filtered_projects), len(projects))
            if any(filters.values())
            else ""
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


def _artifact_detail(conn, benchmark_run_id, registry_path=CANDIDATE_REGISTRY_PATH):
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
        _pill(candidate.get("status"))
        if candidate
        else '<span class="empty">not registered</span>'
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
    <section style="margin-top:16px"><h2>Artifact Files</h2>{files}</section>
    """.format(
        name=_text(artifact_name),
        status=candidate_state,
        run_id=_text(benchmark_run_id),
        dashboard_state=dashboard_state,
        source=_path_cell(candidate.get("source_packet_path") if candidate else ""),
        report=_path_cell(candidate.get("report_path") if candidate else ""),
        files=_table(["Name", "Type", "Path"], file_rows, empty_message="Artifact directory not found."),
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


def _storage(conn):
    rows = []
    all_decisions = db.list_decisions(conn)
    for row in _real_rows(all_decisions):
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
    {table}
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_decisions))),
        table=
        _table(
            ["Model", "Decision", "Keep installed", "Best use case", "Weakness", "Retest"],
            rows,
            empty_message="No real storage/install decisions logged yet.",
        ),
    )
    return _layout("Storage / Install Status", "/storage", body)


def _reports(conn, database_path):
    report = generate_markdown_report(database_path)
    body = """
    <section class="panel" style="margin-bottom:16px">
      <h2>What This Means</h2>
      <p>Ranked models are imported benchmark results, not installed-model inventory.</p>
      <p>Radar candidates are possible models to evaluate, not scored models.</p>
      <p>Installed Models checks local LM Studio and Ollama inventory on demand.</p>
      <p>Scores are valid only after raw responses, confirmed scores, and decisions exist.</p>
      <p>Demo rows are examples only and are hidden from real dashboard views by default.</p>
    </section>
    <h2>Reports</h2><pre class="report">{report}</pre>
    """.format(report=escape(report))
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
                html = _layout("Error", "", "<h2>Error</h2><p>{}</p>".format(_text(exc)))
                self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def do_POST(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path not in ("/actions/run-test", "/actions/refresh-inventory"):
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
                html = _layout("Run Test Error", "", "<h2>Run Test Error</h2><p>{}</p>".format(_text(exc)))
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
                    action_token=action_token,
                )
            if path == "/":
                return _overview(conn, query)
            if path == "/runs":
                return _runs(conn)
            if path == "/compare":
                return _compare(conn)
            if path == "/inventory":
                return _inventory(
                    inventory_result=inventory_cache["result"],
                    action_token=action_token,
                    enable_run_tests=enable_run_tests,
                    enable_refresh=enable_inventory_refresh,
                )
            if path == "/radar":
                return _radar(conn, query)
            if path == "/specialty":
                return _specialty(conn)
            if path == "/projects":
                return _projects(query)
            if path == "/storage":
                return _storage(conn)
            if path == "/reports":
                return _reports(conn, database_path)
            if path == "/demo":
                return _demo(conn)
            if path.startswith("/artifacts/"):
                benchmark_run_id = path.rsplit("/", 1)[-1]
                return _artifact_detail(conn, benchmark_run_id)
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
    run_test_timeout=3600,
    inventory_timeout=5,
):
    if enable_run_tests and not _is_loopback_host(host):
        raise ValueError("Run-test actions require a localhost or loopback bind host.")
    enable_inventory_refresh = _is_loopback_host(host)
    action_token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(
        (host, port),
        make_handler(
            database_path,
            enable_run_tests=enable_run_tests,
            action_token=action_token,
            run_test_timeout=run_test_timeout,
            inventory_timeout=inventory_timeout,
            enable_inventory_refresh=enable_inventory_refresh,
        ),
    )
    print("Serving Local Model Dashboard at http://{}:{}".format(host, port), flush=True)
    if enable_run_tests:
        print("Dashboard run-test actions enabled for local candidates.", flush=True)
    if enable_inventory_refresh:
        print("Installed-model inventory refresh enabled for local runtimes.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
