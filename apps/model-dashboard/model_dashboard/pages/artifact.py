"""Dashboard artifact detail and raw-response comparison pages."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

import json
from pathlib import Path

from .. import capability, charts, db
from ..components import *
from ..filters import *
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS


EM_DASH = "—"
RESPONSE_PREVIEW_CHARS = 180


def _load_json_object(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_raw_responses(artifact_dir):
    raw_path = Path(artifact_dir) / "raw_responses.jsonl"
    if not raw_path.is_file():
        return {"exists": False, "records": [], "skipped": 0, "read_error": False}

    records = []
    seen_prompt_ids = set()
    skipped = 0
    try:
        with raw_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    skipped += 1
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue
                if not isinstance(record, dict):
                    skipped += 1
                    continue
                prompt_id = record.get("prompt_id")
                if prompt_id in (None, "") or str(prompt_id) in seen_prompt_ids:
                    skipped += 1
                    continue
                seen_prompt_ids.add(str(prompt_id))
                records.append(record)
    except (OSError, UnicodeError):
        return {"exists": True, "records": [], "skipped": skipped, "read_error": True}
    return {
        "exists": True,
        "records": records,
        "skipped": skipped,
        "read_error": False,
    }


def _raw_response_notes(result, run_id=""):
    prefix = f"{run_id}: " if run_id else ""
    notes = []
    if not result["exists"]:
        suffix = f" for {run_id}" if run_id else " for this run"
        return [f"No raw response artifact is available{suffix}."]
    if result["read_error"]:
        notes.append(f"{prefix}The raw response artifact could not be read.")
    skipped = result["skipped"]
    if skipped:
        noun = "line" if skipped == 1 else "lines"
        notes.append(f"{prefix}Skipped {skipped} unreadable or incomplete JSONL {noun}.")
    if not result["records"] and not result["read_error"]:
        notes.append(f"{prefix}The raw response artifact has no readable prompt records.")
    return notes


def _notes_html(notes):
    return "".join(f'<p class="artifact-warning">{_text(note)}</p>' for note in notes)


def _artifact_metadata(artifact_dir):
    return _load_json_object(Path(artifact_dir) / "metadata.json")


def _prompt_set_id(metadata, records=()):
    value = metadata.get("prompt_set_id")
    if value not in (None, ""):
        return str(value)
    for record in records:
        value = record.get("prompt_set_id")
        if value not in (None, ""):
            return str(value)
    return ""


def _artifact_model_name(metadata, benchmark_run_id):
    model = metadata.get("model")
    if isinstance(model, dict) and model.get("model_name") not in (None, ""):
        return str(model["model_name"])
    return str(benchmark_run_id)


def _artifact_catalog(eval_results_dir):
    root = Path(eval_results_dir)
    if not root.is_dir():
        return []
    catalog = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir() or not SAFE_ARTIFACT_ID_RE.fullmatch(path.name):
            continue
        metadata = _artifact_metadata(path)
        prompt_set = _prompt_set_id(metadata)
        if not prompt_set:
            prompt_set = _prompt_set_id(metadata, _load_raw_responses(path)["records"])
        catalog.append(
            {
                "benchmark_run_id": path.name,
                "model_name": _artifact_model_name(metadata, path.name),
                "prompt_set_id": prompt_set,
            }
        )
    return catalog


def _compare_picker(catalog, prompt_set_id, run_a, run_b):
    compatible = [row for row in catalog if row["prompt_set_id"] == prompt_set_id]
    if not prompt_set_id:
        return '<p class="empty">A/B compare is unavailable because this run has no readable prompt_set_id.</p>'
    if len(compatible) < 2:
        return '<p class="empty">No second local artifact shares this run\'s prompt_set_id yet.</p>'

    compatible_ids = [row["benchmark_run_id"] for row in compatible]
    selected_a = run_a if run_a in compatible_ids else compatible_ids[0]
    selected_b = run_b if run_b in compatible_ids and run_b != selected_a else ""
    if not selected_b:
        selected_b = next(item for item in compatible_ids if item != selected_a)

    def options(selected):
        return "".join(
            _option(
                row["benchmark_run_id"],
                f'{row["benchmark_run_id"]} — {row["model_name"]}',
                selected,
            )
            for row in compatible
        )

    run_a_options = options(selected_a)
    run_b_options = options(selected_b)
    escaped_prompt_set = _text(prompt_set_id)
    return f"""
    <form class="ab-picker" method="get" action="/artifacts/compare">
      <div class="field">
        <label for="ab-run-a">Run A</label>
        <select id="ab-run-a" name="run_a">{run_a_options}</select>
      </div>
      <div class="field">
        <label for="ab-run-b">Run B</label>
        <select id="ab-run-b" name="run_b">{run_b_options}</select>
      </div>
      <button type="submit">Compare responses</button>
    </form>
    <p class="section-note">Only artifacts with prompt set <code>{escaped_prompt_set}</code> are offered.</p>
    """


def _metric_value(record, key, suffix=""):
    value = record.get(key) if record else None
    if value in (None, ""):
        return EM_DASH
    return f"{_text(value)}{suffix}"


def _response_details(record, missing_message="No response text captured."):
    if record is None:
        return f'<span class="empty">{_text(missing_message)}</span>'
    raw_response = record.get("raw_response")
    if raw_response in (None, ""):
        return f'<span class="empty">{_text(missing_message)}</span>'
    response_text = str(raw_response)
    preview = " ".join(response_text.split())
    if len(preview) > RESPONSE_PREVIEW_CHARS:
        preview = preview[: RESPONSE_PREVIEW_CHARS - 1].rstrip() + "…"
    escaped_preview = _text(preview)
    escaped_response = _text(response_text)
    return f"""
    <details class="response-details">
      <summary><span class="response-preview">{escaped_preview}</span><span class="response-expand">Expand response</span></summary>
      <pre class="response-full">{escaped_response}</pre>
    </details>
    """


def _prompt_response_table(records):
    if not records:
        return ""
    rows = []
    for record in records:
        prompt_id = _text(record.get("prompt_id"))
        rows.append(
            """
            <tr data-prompt-id="{prompt_id}">
              <td><code>{prompt_id}</code></td>
              <td>{latency}</td>
              <td>{input_tokens}</td>
              <td>{output_tokens}</td>
              <td>{response}</td>
            </tr>
            """.format(
                prompt_id=prompt_id,
                latency=_metric_value(record, "latency_ms", " ms"),
                input_tokens=_metric_value(record, "input_tokens"),
                output_tokens=_metric_value(record, "output_tokens"),
                response=_response_details(record),
            )
        )
    return """
    <div class="table-wrap">
      <table class="prompt-responses-table">
        <thead><tr><th>Prompt ID</th><th>Latency</th><th>Input tokens</th><th>Output tokens</th><th>Response</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """.format(rows="".join(rows))


def _prompt_response_section(result):
    notes = _raw_response_notes(result)
    table = _prompt_response_table(result["records"])
    notes_html = _notes_html(notes)
    return f"""
    <section class="artifact-response-section">
      <h2>Per-prompt Responses</h2>
      <p class="section-note">Raw local responses are collapsed by default. Expand a row to inspect the complete escaped artifact text.</p>
      {notes_html}
      {table}
    </section>
    """


def _paired_prompt_records(records_a, records_b):
    by_a = {str(row["prompt_id"]): row for row in records_a}
    by_b = {str(row["prompt_id"]): row for row in records_b}
    prompt_ids = list(by_a)
    prompt_ids.extend(prompt_id for prompt_id in by_b if prompt_id not in by_a)
    return [(prompt_id, by_a.get(prompt_id), by_b.get(prompt_id)) for prompt_id in prompt_ids]


def _ab_response_cell(record):
    return """
    <div class="ab-response-cell">
      <div class="response-metrics">
        <span>Latency: {latency}</span>
        <span>Input tokens: {input_tokens}</span>
        <span>Output tokens: {output_tokens}</span>
      </div>
      {response}
    </div>
    """.format(
        latency=_metric_value(record, "latency_ms", " ms"),
        input_tokens=_metric_value(record, "input_tokens"),
        output_tokens=_metric_value(record, "output_tokens"),
        response=_response_details(record, "No response captured for this prompt."),
    )


def _ab_response_table(pairs, run_a, run_b, name_a, name_b):
    if not pairs:
        return '<p class="empty">No readable prompt responses are available to compare.</p>'
    rows = []
    for prompt_id, record_a, record_b in pairs:
        escaped_prompt_id = _text(prompt_id)
        response_a = _ab_response_cell(record_a)
        response_b = _ab_response_cell(record_b)
        rows.append(
            f"""
            <tr data-prompt-id="{escaped_prompt_id}">
              <td><code>{escaped_prompt_id}</code></td>
              <td>{response_a}</td>
              <td>{response_b}</td>
            </tr>
            """
        )
    return """
    <div class="table-wrap">
      <table class="ab-responses-table">
        <thead>
          <tr>
            <th>Prompt ID</th>
            <th><span class="ab-run-label">Run A · {name_a}</span><code>{run_a}</code></th>
            <th><span class="ab-run-label">Run B · {name_b}</span><code>{run_b}</code></th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """.format(
        name_a=_text(name_a),
        run_a=_text(run_a),
        name_b=_text(name_b),
        run_b=_text(run_b),
        rows="".join(rows),
    )


def _artifact_context_path(value):
    if value and Path(str(value)).is_absolute():
        return '<span class="empty">Private absolute path hidden</span>'
    return _path_cell(value)


def _artifact_detail(
    conn,
    benchmark_run_id,
    registry_path=CANDIDATE_REGISTRY_PATH,
    database_path=DEFAULT_DASHBOARD_DB,
    enable_import_actions=False,
    action_token="",
    eval_results_dir=None,
):
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    candidates = _load_radar_candidates(registry_path)
    candidate = next(
        (row for row in candidates if row.get("benchmark_run_id") == benchmark_run_id),
        None,
    )
    try:
        artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    except ValueError:
        return _layout("Benchmark Artifact", "", "<h2>Artifact not found</h2>")
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
    raw_result = _load_raw_responses(artifact_dir)
    metadata = _artifact_metadata(artifact_dir)
    prompt_set = _prompt_set_id(metadata, raw_result["records"])
    compare_picker = _compare_picker(
        _artifact_catalog(eval_results_dir),
        prompt_set,
        str(benchmark_run_id),
        "",
    )

    file_rows = []
    if artifact_dir.exists():
        for path in sorted(artifact_dir.iterdir(), key=lambda item: item.name.lower()):
            kind = "directory" if path.is_dir() else "file"
            display_path = Path(benchmark_run_id) / path.relative_to(artifact_dir)
            file_rows.append([_text(path.name), _text(kind), _path_cell(display_path)])

    body = """
    <div class="split">
      <section class="panel">
        <h2>{name}</h2>
        <p><strong>Candidate:</strong> {status}</p>
        <p><strong>Benchmark run:</strong> <code>{run_id}</code></p>
        <p><strong>Prompt set:</strong> {prompt_set}</p>
        <p><strong>Dashboard:</strong> {dashboard_state}</p>
      </section>
      <section class="panel">
        <h2>Radar Context</h2>
        <p><strong>Source packet:</strong> {source}</p>
        <p><strong>Report:</strong> {report}</p>
      </section>
    </div>
    <section class="panel artifact-ab-picker" style="margin-top:16px">
      <h2>A/B Response Viewer</h2>
      <p>Choose two local runs with the same prompt set to inspect their responses side by side.</p>
      {compare_picker}
    </section>
    {responses}
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
        prompt_set=(f"<code>{_text(prompt_set)}</code>" if prompt_set else EM_DASH),
        dashboard_state=dashboard_state,
        source=_artifact_context_path(candidate.get("source_packet_path") if candidate else ""),
        report=_artifact_context_path(candidate.get("report_path") if candidate else ""),
        compare_picker=compare_picker,
        responses=_prompt_response_section(raw_result),
        import_control=_artifact_import_control(
            benchmark_run_id,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
            eval_results_dir=eval_results_dir,
        ),
        import_guidance=_artifact_import_guidance(
            benchmark_run_id,
            database_path,
            eval_results_dir,
        ),
        files=_table(
            ["Name", "Type", "Path"], file_rows, empty_message="Artifact directory not found."
        ),
    )
    return _layout("Benchmark Artifact", "/runs", body)


def _artifact_compare(conn, query=None, eval_results_dir=None):
    del conn
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    query = query or {}
    run_a = _query_value(query, "run_a")
    run_b = _query_value(query, "run_b")
    catalog = _artifact_catalog(eval_results_dir)
    by_id = {row["benchmark_run_id"]: row for row in catalog}
    entry_a = by_id.get(run_a)
    entry_b = by_id.get(run_b)
    prompt_set = entry_a["prompt_set_id"] if entry_a else ""
    picker = _compare_picker(catalog, prompt_set, run_a, run_b) if entry_a else ""

    notes = []
    table = ""
    if not run_a or not run_b:
        notes.append("Choose two benchmark runs from an artifact detail page.")
    elif entry_a is None or entry_b is None:
        notes.append("One or both selected benchmark artifacts were not found.")
    elif run_a == run_b:
        notes.append("Choose two different benchmark runs.")
    elif not entry_a["prompt_set_id"] or entry_a["prompt_set_id"] != entry_b["prompt_set_id"]:
        notes.append("The selected runs do not share the same prompt_set_id.")
    else:
        artifact_a = _safe_artifact_dir(run_a, eval_results_dir)
        artifact_b = _safe_artifact_dir(run_b, eval_results_dir)
        responses_a = _load_raw_responses(artifact_a)
        responses_b = _load_raw_responses(artifact_b)
        notes.extend(_raw_response_notes(responses_a, run_a))
        notes.extend(_raw_response_notes(responses_b, run_b))
        table = _ab_response_table(
            _paired_prompt_records(responses_a["records"], responses_b["records"]),
            run_a,
            run_b,
            entry_a["model_name"],
            entry_b["model_name"],
        )

    notes_html = _notes_html(notes)
    body = f"""
    <section class="panel page-intro">
      <h2>A/B Response Viewer</h2>
      <p>Compare escaped local benchmark responses prompt by prompt. Raw responses remain collapsed until expanded.</p>
      {picker}
    </section>
    <section class="artifact-ab-section">
      <h2>Side-by-side Responses</h2>
      {notes_html}
      {table}
    </section>
    """
    return _layout("A/B Responses", "/runs", body)


__all__ = (
    "_artifact_compare",
    "_artifact_detail",
    "_load_raw_responses",
    "_paired_prompt_records",
)
