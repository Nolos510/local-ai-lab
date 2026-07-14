"""Shared dashboard constants and HTML components."""

# ruff: noqa: E501

from __future__ import annotations

import csv
import ipaddress
import math
import re
import shlex
import subprocess
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from . import capability, charts, db, fit
from .icons import icon as render_icon
from .scoring import METRIC_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_REGISTRY_PATH = REPO_ROOT / "data" / "model_registry" / "candidates.csv"
PROJECT_REGISTRY_PATH = REPO_ROOT / "data" / "project_registry" / "github_repos.csv"
EVAL_RESULTS_DIR = REPO_ROOT / "data" / "eval_results"
HARNESS_PATH = REPO_ROOT / "evals" / "local-llm-benchmark" / "harness.py"
DEFAULT_DASHBOARD_DB = REPO_ROOT / "data" / "dashboard" / "model_dashboard.sqlite"
LOCAL_INVENTORY_REGISTRY_PATH = REPO_ROOT / "data" / "dashboard" / "local_inventory_candidates.csv"
SUPPORTED_LOCAL_RUNNERS = {
    "llama-cpp": "llama.cpp",
    "lmstudio-cli": "LM Studio CLI",
    "mlx-lm": "MLX-LM",
    "ollama": "Ollama",
    "openai-compatible": "OpenAI-compatible local endpoint",
}
SAFE_ARTIFACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
METRIC_EXPLANATIONS = {
    "total_score": "Summed quality score across the benchmark rubric's dimensions (instruction-following, reasoning, coding, agent-planning, etc.). Higher is better; it's a relative ranking signal, not a percentage. See the model detail page for the per-dimension breakdown.",
    "throughput": "Output tokens generated per second during the run. Higher is faster. Depends on model size, quantization, runtime, and hardware — only compare within the same setup.",
    "ram_footprint": "Whole-system RAM high-water observed during the run. For LM Studio and endpoint runners this can include other loaded models, macOS cache, and runtime overhead; it is not per-model RSS. 'No data yet' means no run captured memory.",
    "models": "Count of real benchmarked model records imported into the dashboard. Demo fixture rows are hidden from real result views.",
    "runs": "Count of real benchmark runs imported into the dashboard.",
    "average_score": "Mean Total Score across the models you've benchmarked.",
    "kept_installed": "Count of models marked to keep installed after you reviewed their results.",
    "score": "Summed quality score across the benchmark rubric's dimensions (instruction-following, reasoning, coding, agent-planning, etc.). Higher is better; it's a relative ranking signal, not a percentage. See the model detail page for the per-dimension breakdown.",
    "status": "Confirmed = a score you finalized after review. Draft = an auto-suggested score awaiting confirmation; drafts never overwrite confirmed scores.",
    "decision": "Your keep / watchlist / retest / skip verdict after reviewing results.",
    "fit": "Estimated memory = parameter count in billions × quantization bits ÷ 8 × 1.1 weight overhead, plus an 8 GB context/runtime allowance. Fit compares that estimate with machine memory after a 16 GB system reserve. It is an estimate, not a measured run; observed tok/s comes only from imported benchmark runs.",
}
METRIC_LABEL_KEYS = {
    "total score": "total_score",
    "throughput": "throughput",
    "tokens / sec": "throughput",
    "tok/s": "throughput",
    "ram footprint": "ram_footprint",
    "system ram high-water": "ram_footprint",
    "system ram gb": "ram_footprint",
    "models": "models",
    "runs": "runs",
    "average score": "average_score",
    "kept installed": "kept_installed",
    "score": "score",
    "status": "status",
    "decision": "decision",
    "fit": "fit",
}
RESULT_TABLE_HEADER_TIPS = {
    "System RAM GB": "ram_footprint",
    "Score": "score",
    "Status": "status",
    "Decision": "decision",
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


def _observed_tokens_per_second(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _fit_summary(params_b, bits, memory_gb, observed_tokens_per_sec=None):
    assessment = fit.assess_fit(params_b, bits, memory_gb)
    if assessment.status == "unknown":
        label = "Fit: unknown"
    else:
        label = f"Fit: {assessment.status} · {assessment.estimated_memory_gb:.1f} GB est."
    observed = _observed_tokens_per_second(observed_tokens_per_sec)
    observed_html = (
        f'<span class="observed-performance">Observed {observed:.1f} tok/s</span>'
        if observed is not None
        else ""
    )
    return (
        '<span class="fit-summary">'
        f'<span class="pill fit-pill fit-{_text(assessment.status)}">{_text(label)}</span>'
        f'{_metric_info("fit")}'
        f"{observed_html}"
        "</span>"
    )


def _fit_capacity_summary(memory_gb):
    capacity = fit.max_estimated_weights_gb(memory_gb)
    if capacity is None:
        label = "Fit: unknown"
        class_name = "fit-unknown"
    else:
        rounded_capacity = math.floor(capacity / 10.0) * 10
        label = f"Fit: up to ~{rounded_capacity:.0f} GB est. weights"
        class_name = "fit-capacity"
    return (
        '<span class="fit-summary">'
        f'<span class="pill fit-pill {class_name}">{_text(label)}</span>'
        f'{_metric_info("fit")}'
        "</span>"
    )


def _fit_memory_gb(
    hardware_profiles_dir,
    *,
    current_hardware_profile=None,
    read_current_hardware=False,
):
    profiles = capability.load_hardware_profiles(Path(hardware_profiles_dir), limit=1)
    profile = profiles[-1] if profiles else current_hardware_profile
    if profile is None and read_current_hardware:
        profile = capability.current_hardware_profile()
    if not profile:
        return None
    return fit.parse_parameter_count_b(profile.get("memory_gb"))


def _metric_key(label):
    return METRIC_LABEL_KEYS.get(str(label or "").strip().lower())


def _metric_info(label_or_key):
    key = label_or_key if label_or_key in METRIC_EXPLANATIONS else _metric_key(label_or_key)
    if not key:
        return ""
    tip = METRIC_EXPLANATIONS[key]
    return (
        '<span class="metric-tip" tabindex="0" data-tip="{tip}" title="{tip}" '
        'aria-label="{label}">{icon}</span>'
    ).format(
        tip=_text(tip),
        label=_text(f"Metric explanation: {tip}"),
        icon=render_icon("ti-info-circle", cls="metric-info-icon"),
    )


def _metric_label(label, tip_key=None, auto=True):
    key = tip_key or (_metric_key(label) if auto else None)
    info = _metric_info(key) if key else ""
    return f'<span class="metric-label">{_text(label)}{info}</span>'


def _stat_card(label, value, icon_name):
    return (
        '<div class="stat">'
        f"{render_icon(icon_name)}"
        f'<div><div class="label">{_metric_label(label)}</div><div class="value">{_text(value)}</div></div>'
        "</div>"
    )


def _chart_panel(title, chart):
    return (
        f'<div class="panel chart-panel"><h2>{_metric_label(title)}</h2>'
        f'<div class="chart-scroll">{chart}</div></div>'
    )


def _model_chart_label(row):
    keys = row.keys()
    backend = row["backend"] if "backend" in keys else ""
    model_name = row["model_name"]
    return f"{model_name} ({backend})" if backend else model_name


def _average_metric_items(rows):
    items = []
    for field in METRIC_FIELDS:
        values = [float(row[field]) for row in rows if row[field] not in (None, "")]
        if values:
            items.append((field.replace("_", " ").title(), sum(values) / len(values)))
    return items


def _performance_items(rows, field):
    items = []
    for row in rows:
        keys = row.keys()
        if field in keys:
            items.append((_model_chart_label(row), row[field]))
    return items


def _performance_chart(rows, field, title, value_format, empty_message):
    return charts.horizontal_bars(
        _performance_items(rows, field),
        value_format=value_format,
        title=title,
        empty_message=empty_message,
    )


def _table(
    headers,
    rows,
    empty_message="No rows yet.",
    table_class="",
    scroll_controls=False,
    scroll_id="",
    scroll_label="Table",
    header_tip_keys=None,
):
    if not rows:
        return f'<p class="empty">{escape(empty_message)}</p>'
    header_tip_keys = header_tip_keys or {}
    header_html = "".join(
        f"<th>{_metric_label(header, header_tip_keys.get(header), auto=False)}</th>"
        for header in headers
    )
    row_html = []
    for row in rows:
        row_html.append(
            "<tr>{}</tr>".format(
                "".join(f'<td><div class="cell-scroll">{cell}</div></td>' for cell in row)
            )
        )
    class_attr = f' class="{escape(table_class)}"' if table_class else ""
    table = "<table{}><thead><tr>{}</tr></thead><tbody>{}</tbody></table>".format(
        class_attr, header_html, "".join(row_html)
    )
    if not scroll_controls:
        return f'<div class="table-wrap">{table}</div>'

    target_id = _text(scroll_id or f"table-scroll-{_slug(table_class or scroll_label)}")
    label = _text(scroll_label)
    return f"""
    <div class="table-scroll-shell">
      <div class="table-scroll-toolbar" aria-label="{label} horizontal scroll controls">
        <button class="icon-button" type="button" data-scroll-target="{target_id}" data-scroll-by="-420" aria-label="Scroll {label} left" title="Scroll {label} left">{render_icon("ti-chevron-left")}</button>
        <button class="icon-button" type="button" data-scroll-target="{target_id}" data-scroll-by="420" aria-label="Scroll {label} right" title="Scroll {label} right">{render_icon("ti-chevron-right")}</button>
      </div>
      <div class="table-wrap" id="{target_id}">{table}</div>
    </div>
    """


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


def _load_candidate_rows(path):
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def _load_radar_candidates(
    path=CANDIDATE_REGISTRY_PATH,
    local_inventory_path=None,
):
    rows = _load_candidate_rows(path)
    by_id = {row.get("candidate_id", ""): index for index, row in enumerate(rows)}
    if local_inventory_path is None:
        try:
            if Path(path).resolve() == CANDIDATE_REGISTRY_PATH.resolve():
                local_inventory_path = LOCAL_INVENTORY_REGISTRY_PATH
        except OSError:
            local_inventory_path = None
    if local_inventory_path:
        for overlay in _load_candidate_rows(local_inventory_path):
            candidate_id = overlay.get("candidate_id", "")
            if candidate_id and candidate_id in by_id:
                merged = dict(rows[by_id[candidate_id]])
                merged.update({key: value for key, value in overlay.items() if value})
                rows[by_id[candidate_id]] = merged
            else:
                rows.append(overlay)
    return rows


def _load_project_repos(path=PROJECT_REGISTRY_PATH):
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


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


def _external_link_or_text(url, label):
    value = str(url or "").strip()
    if not value:
        return '<span class="empty">None</span>'
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        return _text(label or value)
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
    if runner in ("llama-cpp", "lmstudio-cli", "mlx-lm", "ollama"):
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


def _run_note_value(notes, key):
    prefix = f"{key}="
    for part in str(notes or "").split("|"):
        part = part.strip()
        if part.startswith(prefix):
            return part.split("=", 1)[1].strip()
    return ""


def _benchmark_run_id_from_notes(notes):
    return _run_note_value(notes, "benchmark_run_id")


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
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    import_dir = artifact_dir / "dashboard-import"
    return {
        "models": import_dir / "models.csv",
        "model_runs": import_dir / "model_runs.csv",
        "eval_scores": import_dir / "eval_scores.csv",
        "decisions": import_dir / "decisions.csv",
    }


def _artifact_import_ready(benchmark_run_id, eval_results_dir=None):
    try:
        return all(
            path.exists()
            for path in _artifact_csv_paths(benchmark_run_id, eval_results_dir).values()
        )
    except ValueError:
        return False


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


def _safe_artifact_dir(benchmark_run_id, eval_results_dir=None):
    benchmark_run_id = str(benchmark_run_id or "")
    if not SAFE_ARTIFACT_ID_RE.fullmatch(benchmark_run_id):
        raise ValueError(f"Invalid benchmark artifact id: {benchmark_run_id}")
    root = Path(EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir).resolve()
    artifact_dir = (root / benchmark_run_id).resolve()
    try:
        artifact_dir.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Invalid benchmark artifact id: {benchmark_run_id}") from exc
    return artifact_dir


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


def _merge_fit_evidence(target, row):
    for field in ("params_b", "quantization"):
        if target.get(field) in (None, "") and row[field] not in (None, ""):
            target[field] = row[field]
    observed = _observed_tokens_per_second(row["tokens_per_sec"])
    if target.get("tokens_per_sec") is None and observed is not None:
        target["tokens_per_sec"] = observed


def _dashboard_fit_evidence(conn):
    """Index latest model metadata and real observed throughput for fit pills."""
    by_name = {}
    by_candidate = {}
    for row in _real_rows(db.list_runs(conn)):
        model_name = str(row["model_name"] or "").strip().lower()
        if model_name:
            evidence = by_name.setdefault(model_name, {})
            _merge_fit_evidence(evidence, row)
        candidate_id = _run_note_value(row["run_notes"], "candidate_id")
        if candidate_id:
            evidence = by_candidate.setdefault(candidate_id, {})
            _merge_fit_evidence(evidence, row)
    for row in _real_rows(db.list_model_summaries(conn)):
        model_name = str(row["model_name"] or "").strip().lower()
        if model_name:
            evidence = by_name.setdefault(model_name, {})
            _merge_fit_evidence(evidence, row)
    return {"by_name": by_name, "by_candidate": by_candidate}


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

__all__ = ('_text', '_number', '_pill', '_status_pill', '_fit_summary', '_fit_capacity_summary', '_fit_memory_gb', '_stat_card', '_chart_panel', '_model_chart_label', '_average_metric_items', '_performance_items', '_performance_chart', '_table', '_is_demo_row', '_real_rows', '_demo_rows', '_real_counts', '_real_data_notice', '_load_radar_candidates', '_load_project_repos', '_path_cell', '_external_link', '_external_link_or_text', '_candidate_review_links', '_candidate_availability', '_candidate_security_status', '_candidate_security', '_slug', '_candidate_runner_label', '_candidate_run_ready', '_run_test_control', '_next_dashboard_run_id', '_append_arg', '_run_subprocess', '_command_result', '_is_loopback_host', '_relative_path', '_artifact_link', '_run_note_value', '_benchmark_run_id_from_notes', '_artifact_link_from_notes', '_command_block', '_command_lines', '_file_status', '_count_jsonl_lines', '_artifact_summaries', '_artifact_csv_paths', '_artifact_import_ready', '_artifact_import_command', '_artifact_import_guidance', '_artifact_import_control', '_safe_artifact_dir', '_score_status_counts', '_dashboard_model_links', '_dashboard_fit_evidence', '_dashboard_run_ids', '_dashboard_runs_by_benchmark_id', '_latest_decisions_by_model_id', '_import_state_for_run', 'REPO_ROOT', 'CANDIDATE_REGISTRY_PATH', 'PROJECT_REGISTRY_PATH', 'EVAL_RESULTS_DIR', 'HARNESS_PATH', 'DEFAULT_DASHBOARD_DB', 'LOCAL_INVENTORY_REGISTRY_PATH', 'SUPPORTED_LOCAL_RUNNERS', 'SAFE_ARTIFACT_ID_RE', 'METRIC_EXPLANATIONS', 'METRIC_LABEL_KEYS', 'RESULT_TABLE_HEADER_TIPS')
