"""Dashboard capability page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path

from .. import capability, charts, db, quant_advice
from ..components import *
from ..filters import *
from ..icons import icon as render_icon
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS

def _capability(
    conn,
    registry_path=CANDIDATE_REGISTRY_PATH,
    eval_results_dir=EVAL_RESULTS_DIR,
    hardware_profiles_dir=REPO_ROOT / "docs" / "lab-notes",
    quant_advice_dir=REPO_ROOT / "data" / "model_registry" / "quant_advice",
):
    candidates = capability.load_candidates(Path(registry_path))
    candidate_counts = capability.candidate_readiness_counts(candidates)
    artifact_counts = capability.benchmark_artifact_counts(Path(eval_results_dir))
    hardware_profiles = capability.load_hardware_profiles(Path(hardware_profiles_dir))
    quant_rows = quant_advice.load_saved_quant_advice(Path(quant_advice_dir))
    real_counts = _real_counts(conn)
    score_counts = _score_status_counts(conn)
    dashboard_runs = _real_rows(db.list_runs(conn))
    tokens_items = _performance_items(dashboard_runs, "tokens_per_sec")
    ttft_items = _performance_items(dashboard_runs, "ttft_seconds")
    latency_items = _performance_items(dashboard_runs, "total_latency_seconds")
    tokens_chart = charts.horizontal_bars(
        tokens_items,
        value_format="{:.1f} tok/s",
        title="Capability tokens per second",
        empty_message="No tokens/sec values imported yet",
    )
    ttft_chart = charts.horizontal_bars(
        ttft_items,
        value_format="{:.2f}s",
        title="Capability TTFT seconds",
        empty_message="No TTFT values imported yet",
    )
    latency_chart = charts.horizontal_bars(
        latency_items,
        value_format="{:.2f}s",
        title="Capability total latency seconds",
        empty_message="No total latency values imported yet",
    )
    tokens_panel = _capability_chart_panel(
        "Tokens / Sec",
        tokens_chart,
        tokens_items,
        "{:.1f} tok/s",
        "No tokens/sec values imported yet",
        "tokens_per_sec",
        "capability-chart-tokens",
    )
    ttft_panel = _capability_chart_panel(
        "TTFT",
        ttft_chart,
        ttft_items,
        "{:.2f}s",
        "No TTFT values imported yet",
        "ttft_seconds",
        "capability-chart-ttft",
    )
    latency_panel = _capability_chart_panel(
        "Total Latency",
        latency_chart,
        latency_items,
        "{:.2f}s",
        "No total latency values imported yet",
        "total_latency_seconds",
        "capability-chart-latency",
    )

    status_rows = [
        [_text(status), _text(count)]
        for status, count in sorted(candidate_counts.items())
        if status
        not in {
            "total",
            "runnable_ready",
            "blocked_ready",
        }
        and count
    ]

    ready_rows = []
    ready_candidates = [candidate for candidate in candidates if candidate.get("status") == "ready_for_eval"]
    for row in ready_candidates[:8]:
        blocked_reasons = capability.candidate_blocked_reasons(row)
        readiness = "blocked" if blocked_reasons else "ready"
        ready_rows.append(
            [
                '<div class="cell-stack"><div>{name}</div><code>{id}</code></div>'.format(
                    name=_text(row.get("model_name")),
                    id=_text(row.get("candidate_id")),
                ),
                _pill(readiness),
                _text(row.get("local_runner") or "not configured"),
                _text(row.get("local_model_id") or "missing"),
                _text("; ".join(blocked_reasons) or "preflight gates clear"),
                _artifact_link(row.get("benchmark_run_id")),
            ]
        )

    hardware_rows = []
    for profile in hardware_profiles:
        runtime_list = profile.get("runtimes_present") or []
        hardware_rows.append(
            [
                _text(profile.get("filename")),
                _text(profile.get("captured_at")),
                _text(profile.get("os")),
                _text(profile.get("chip") or profile.get("machine")),
                _text(profile.get("cpu_count")),
                _text(profile.get("memory_gb")),
                _text(", ".join(runtime_list) if isinstance(runtime_list, list) else ""),
            ]
        )

    artifact_rows = [
        ["Artifact directories", artifact_counts["total"]],
        ["Raw response artifacts", artifact_counts["with_raw_responses"]],
        ["Confirmed score artifacts", artifact_counts["with_scores"]],
        ["Draft score artifacts", artifact_counts["with_draft_scores"]],
        ["Decision artifacts", artifact_counts["with_decisions"]],
        ["Dashboard-import folders", artifact_counts["with_dashboard_import"]],
    ]
    quant_table_rows = [
        [
            '<div class="cell-stack"><div>{base}</div><code>{candidate}</code></div>'.format(
                base=_text(row.get("base_repo_id")),
                candidate=_text(row.get("candidate_id") or "not linked"),
            ),
            _text(row.get("artifact_repo_id")),
            _text(row.get("quantization") or "select artifact"),
            _text(row.get("runtime")),
            _pill(row.get("recommendation")),
            _text(row.get("approval_state")),
            _text(row.get("next_step")),
        ]
        for row in quant_rows
    ]

    body = """
    <section class="grid">
      {candidates_stat}
      {ready_stat}
      {blocked_stat}
      {artifacts_stat}
      {scores_stat}
      {dashboard_stat}
    </section>
    <section class="panel" style="margin-bottom:16px">
      <h2>Capability Boundary</h2>
      <p>This page reads repo-local CSV, JSON, SQLite, and artifact metadata only. It does not refresh inventory, call runtime CLIs, start local model servers, inspect model folders, run prompts, download models, or expose raw responses.</p>
      <p>Use it as a planning view for three questions: what local hardware/runtime capability is documented, which candidates are ready or blocked before a run, and which benchmark artifacts exist but may still need dashboard import.</p>
      <p>For results, use Overview, Model Runs, and Compare Models after importing an artifact into the dashboard database.</p>
    </section>
    <section>
      <h2>Hardware Profile Examples</h2>
      {hardware_table}
    </section>
    <section style="margin-top:16px">
      <h2>Candidate Readiness</h2>
      {status_table}
      {ready_table}
    </section>
    <section style="margin-top:16px">
      <h2>Benchmark Artifact Counts</h2>
      {artifact_table}
    </section>
    <section style="margin-top:16px">
      <h2>Quant Advice</h2>
      <p class="empty">Saved quant advice is local metadata only. It does not approve downloads, installs, model runs, or eval scores.</p>
      {quant_advice_table}
    </section>
    <section style="margin-top:16px">
      <h2>Performance Signals</h2>
      <p class="empty">These charts use imported local benchmark run metadata only. Empty charts mean no approved run has imported that perf field yet.</p>
      <div class="chart-grid capability-chart-grid" aria-label="Capability performance charts">
        {tokens_panel}
        {ttft_panel}
        {latency_panel}
      </div>
    </section>
    <section class="panel" style="margin-top:16px">
      <h2>Next Benchmark Matrix</h2>
      <p>Generate the current read-only benchmark queue from the CLI:</p>
      {matrix_command}
      <p class="empty">The matrix command reads <code>data/model_registry/candidates.csv</code> and does not run models.</p>
    </section>
    """.format(
        candidates_stat=_stat_card("Candidates", candidate_counts["total"], "ti-radar"),
        ready_stat=_stat_card(
            "Runnable ready",
            candidate_counts["runnable_ready"],
            "ti-circle-check",
        ),
        blocked_stat=_stat_card("Blocked ready", candidate_counts["blocked_ready"], "ti-shield"),
        artifacts_stat=_stat_card("Artifacts", artifact_counts["total"], "ti-archive"),
        scores_stat=_score_stat_card(score_counts["confirmed"], score_counts["draft"]),
        dashboard_stat=_stat_card("Dashboard runs", real_counts["model_runs"], "ti-player-play"),
        hardware_table=_table(
            ["Profile", "Captured", "OS", "Chip / machine", "CPU", "Memory GB", "Runtimes"],
            hardware_rows,
            empty_message=(
                "No committed hardware profile JSON examples found. Create one with "
                "uv run ai-lab hardware snapshot --out docs/lab-notes/hardware-snapshot-local.json."
            ),
        ),
        ready_table=_table(
            ["Candidate", "Readiness", "Runner", "Local model id", "Preflight notes", "Artifact"],
            ready_rows,
            empty_message="No ready_for_eval candidates are registered.",
        ),
        status_table=_table(
            ["Status", "Count"],
            status_rows,
            empty_message="No candidate statuses found.",
        ),
        artifact_table=_table(
            ["Signal", "Count"],
            [[_text(label), _text(value)] for label, value in artifact_rows],
        ),
        quant_advice_table=_table(
            [
                "Base model",
                "Artifact repo",
                "Quant",
                "Runtime",
                "Recommendation",
                "Approval",
                "Next step",
            ],
            quant_table_rows,
            empty_message=(
                "No saved quant advice found. Run uv run ai-lab quant advise "
                "--candidate <id> --out-json data/model_registry/quant_advice/<id>.json."
            ),
        ),
        tokens_panel=tokens_panel,
        ttft_panel=ttft_panel,
        latency_panel=latency_panel,
        matrix_command=_command_block("uv run ai-lab bench matrix --limit 5"),
    )
    return _layout("Capability", "/capability", body)


def _format_capability_value(value, value_format):
    try:
        return value_format.format(float(value))
    except (TypeError, ValueError):
        return _text(value)


def _score_stat_card(confirmed, draft):
    return """
    <div class="stat stat-breakdown">
      {icon}
      <div>
        <div class="label">Scores</div>
        <div class="stat-metrics" aria-label="Score status counts">
          <span><strong>{confirmed}</strong><em>confirmed</em></span>
          <span><strong>{draft}</strong><em>draft</em></span>
        </div>
      </div>
    </div>
    """.format(
        icon=render_icon("ti-edit"),
        confirmed=_text(confirmed),
        draft=_text(draft),
    )


def _coerce_capability_value(value):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return max(0.0, number)


def _chart_summary(items, value_format, empty_message, *, limit=3):
    values = [
        (label, number)
        for label, value in items
        if (number := _coerce_capability_value(value)) is not None
    ]
    if not values:
        return f'<p class="empty">{_text(empty_message)}</p>'
    rows = []
    for label, value in values[:limit]:
        rows.append(
            '<div class="chart-summary-row">'
            f'<strong class="chart-summary-value">{_format_capability_value(value, value_format)}</strong>'
            f'<span>{_text(label)}</span>'
            "</div>"
        )
    if len(values) > limit:
        rows.append(f'<p class="empty">+{len(values) - limit} more imported runs</p>')
    return '<div class="chart-summary">{}</div>'.format("".join(rows))


def _capability_chart_panel(title, chart, items, value_format, empty_message, field_name, dialog_id):
    safe_title = _text(title)
    safe_dialog_id = _text(dialog_id)
    heading_id = f"{safe_dialog_id}-title"
    summary = _chart_summary(items, value_format, empty_message)
    dialog_summary = _chart_summary(items, value_format, empty_message, limit=10)
    return f"""
    <div class="panel chart-panel chart-panel-large" data-field="{_text(field_name)}">
      <div class="chart-panel-head">
        <h2>{safe_title}</h2>
        <button class="chart-expand" type="button" data-chart-dialog="{safe_dialog_id}">Expand</button>
      </div>
      {summary}
      <div class="chart-preview" aria-hidden="true">{chart}</div>
      <dialog class="chart-dialog" id="{safe_dialog_id}" aria-labelledby="{heading_id}">
        <div class="chart-dialog-head">
          <h2 id="{heading_id}">{safe_title}</h2>
          <form method="dialog"><button type="submit">Close</button></form>
        </div>
        <div class="chart-dialog-body">{chart}</div>
        {dialog_summary}
      </dialog>
    </div>
    """

__all__ = ('_capability',)
