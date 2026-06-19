"""Dashboard capability page."""

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

def _capability(
    conn,
    registry_path=CANDIDATE_REGISTRY_PATH,
    eval_results_dir=EVAL_RESULTS_DIR,
    hardware_profiles_dir=REPO_ROOT / "docs" / "lab-notes",
):
    candidates = capability.load_candidates(Path(registry_path))
    candidate_counts = capability.candidate_readiness_counts(candidates)
    artifact_counts = capability.benchmark_artifact_counts(Path(eval_results_dir))
    hardware_profiles = capability.load_hardware_profiles(Path(hardware_profiles_dir))
    real_counts = _real_counts(conn)
    score_counts = _score_status_counts(conn)
    dashboard_runs = _real_rows(db.list_runs(conn))
    tokens_chart = _performance_chart(
        dashboard_runs,
        "tokens_per_sec",
        "Capability tokens per second",
        "{:.1f} tok/s",
        "No tokens/sec values imported yet",
    )
    ttft_chart = _performance_chart(
        dashboard_runs,
        "ttft_seconds",
        "Capability TTFT seconds",
        "{:.2f}s",
        "No TTFT values imported yet",
    )
    latency_chart = _performance_chart(
        dashboard_runs,
        "total_latency_seconds",
        "Capability total latency seconds",
        "{:.2f}s",
        "No total latency values imported yet",
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
      <p>Use this as a planning view before creating or importing benchmark artifacts.</p>
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
      <h2>Performance Signals</h2>
      <p class="empty">These charts use imported local benchmark run metadata only. Empty charts mean no approved run has imported that perf field yet.</p>
      <div class="chart-grid" aria-label="Capability performance charts">
        {tokens_chart}
        {ttft_chart}
        {latency_chart}
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
        scores_stat=_stat_card(
            "Scores",
            "{} confirmed / {} draft".format(score_counts["confirmed"], score_counts["draft"]),
            "ti-edit",
        ),
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
        tokens_chart=_chart_panel("Tokens / Sec", tokens_chart),
        ttft_chart=_chart_panel("TTFT", ttft_chart),
        latency_chart=_chart_panel("Total Latency", latency_chart),
        matrix_command=_command_block("uv run ai-lab bench matrix --limit 5"),
    )
    return _layout("Capability", "/capability", body)

__all__ = ('_capability',)
