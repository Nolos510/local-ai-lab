"""Dashboard overview page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

import csv
from html import escape
from pathlib import Path

from .. import capability, charts, db
from ..components import *
from ..filters import *
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS


def _count_local_inventory_models(local_inventory_path=LOCAL_INVENTORY_REGISTRY_PATH):
    path = Path(local_inventory_path)
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return sum(
            1
            for row in reader
            if (row.get("local_model_id") or row.get("model_name") or "").strip()
        )


def _workflow_step(label, count, detail, href):
    safe_href = _text(href)
    safe_label = _text(label)
    safe_count = _text(count)
    safe_detail = _text(detail)
    return f"""
    <a class="workflow-step" href="{safe_href}">
      <span>{safe_label}</span>
      <strong>{safe_count}</strong>
      <em>{safe_detail}</em>
    </a>
    """


def _home_next_action(ready_count, installed_count, artifact_counts, real_counts):
    importable_gap = max(0, artifact_counts["with_dashboard_import"] - real_counts["model_runs"])
    score_decision_gap = max(0, real_counts["eval_scores"] - real_counts["decisions"])
    if importable_gap:
        artifact_word = "set is" if importable_gap == 1 else "sets are"
        return {
            "title": "Import benchmark artifacts",
            "detail": f"{importable_gap} dashboard-import artifact {artifact_word} not reflected in the active dashboard database yet.",
            "href": "/runs",
            "label": "Open Benchmark",
        }
    if score_decision_gap:
        return {
            "title": "Decide on scored models",
            "detail": f"{score_decision_gap} scored model result needs a keep, watchlist, retest, or skip decision.",
            "href": "/inventory",
            "label": "Open My Models",
        }
    if real_counts["model_runs"] == 0 and installed_count:
        return {
            "title": "Benchmark your first local model",
            "detail": f"{installed_count} detected local model record is ready to turn into benchmark evidence.",
            "href": "/inventory",
            "label": "Open My Models",
        }
    if ready_count:
        return {
            "title": "Review ready candidates",
            "detail": f"{ready_count} candidate is marked ready_for_eval; confirm local runtime fit before running it.",
            "href": "/radar?status=ready_for_eval",
            "label": "Open Discover",
        }
    return {
        "title": "Review the current lab report",
        "detail": "No immediate benchmark queue is blocked in Home. Export the local dashboard report or refresh installed inventory from My Models.",
        "href": "/reports",
        "label": "Export report",
    }


def _home_action_card(action):
    return """
    <section class="panel do-next">
      <h2>Do This Next</h2>
      <h3>{title}</h3>
      <p class="empty">{detail}</p>
      <div class="home-actions">
        <a class="action-link" href="{href}">{label}</a>
        <a class="action-link secondary" href="/reports">Export report</a>
      </div>
    </section>
    """.format(
        title=_text(action["title"]),
        detail=_text(action["detail"]),
        href=_text(action["href"]),
        label=_text(action["label"]),
    )


def _top_result_rows(summaries, *, limit=5):
    scored = [row for row in summaries if row["total_score"] not in (None, "")]
    scored.sort(key=lambda row: float(row["total_score"]), reverse=True)
    rows = []
    for row in scored[:limit]:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["id"], name=_text(row["model_name"])
                ),
                _number(row["total_score"], 2),
                _status_pill(row["score_status"]),
                _pill(row["final_label"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _text(row["decision"]),
            ]
        )
    return rows


def _machine_card(hardware_profiles, ready_count, artifact_counts, current_hardware_profile=None):
    if hardware_profiles:
        profile = hardware_profiles[-1]
    else:
        profile = current_hardware_profile or capability.current_hardware_profile()
    machine = (
        profile.get("machine_name")
        or profile.get("machine_model")
        or profile.get("machine")
        or "Recorded Mac"
    )
    chip = profile.get("chip") or "not recorded"
    memory = (
        profile.get("memory_label")
        or (f"{profile.get('memory_gb')} GB" if profile.get("memory_gb") else "")
        or "not recorded"
    )
    runtimes = profile.get("runtimes_present") or []
    if hardware_profiles:
        runtime_text = (
            ", ".join(runtimes) if isinstance(runtimes, list) and runtimes else "not recorded"
        )
        captured = profile.get("captured_at") or "capture time not recorded"
    else:
        runtime_text = (
            ", ".join(runtimes)
            if isinstance(runtimes, list) and runtimes
            else "not found on PATH"
        )
        captured = (
            profile.get("captured_at")
            or "Live local read; run uv run ai-lab hardware snapshot to save a profile."
        )
    return """
    <section class="panel home-card">
      <h2>This Machine</h2>
      <dl class="machine-facts">
        <div><dt>Machine</dt><dd>{machine}</dd></div>
        <div><dt>Chip</dt><dd>{chip}</dd></div>
        <div><dt>Memory</dt><dd>{memory}</dd></div>
        <div><dt>Runtimes</dt><dd>{runtimes}</dd></div>
        <div><dt>Snapshot</dt><dd>{captured}</dd></div>
        <div><dt>Readiness</dt><dd>{ready} ready candidates; {artifacts} benchmark artifact directories.</dd></div>
      </dl>
    </section>
    """.format(
        machine=_text(machine),
        chip=_text(chip),
        memory=_text(memory),
        runtimes=_text(runtime_text),
        captured=_text(captured),
        ready=_text(ready_count),
        artifacts=_text(artifact_counts["total"]),
    )


def _overview(
    conn,
    query=None,
    registry_path=CANDIDATE_REGISTRY_PATH,
    eval_results_dir=EVAL_RESULTS_DIR,
    hardware_profiles_dir=REPO_ROOT / "docs" / "lab-notes",
    local_inventory_path=LOCAL_INVENTORY_REGISTRY_PATH,
    current_hardware_profile=None,
):
    counts = _real_counts(conn)
    all_summaries = db.list_model_summaries(conn)
    summaries = _real_rows(all_summaries)
    score_values = [
        float(row["total_score"]) for row in summaries if row["total_score"] not in (None, "")
    ]
    avg_score = sum(score_values) / len(score_values) if score_values else None
    keep_count = sum(1 for row in summaries if row["keep_installed"] == 1)
    candidates = _load_radar_candidates(registry_path, local_inventory_path)
    ready_count = sum(1 for row in candidates if row.get("status") == "ready_for_eval")
    installed_count = _count_local_inventory_models(local_inventory_path)
    artifact_counts = capability.benchmark_artifact_counts(Path(eval_results_dir))
    hardware_profiles = capability.load_hardware_profiles(Path(hardware_profiles_dir), limit=1)
    action = _home_next_action(ready_count, installed_count, artifact_counts, counts)
    top_rows = _top_result_rows(summaries)
    body = """
    {notice}
    <section class="panel home-hero">
      <p class="home-intro">Benchmark and decide on local models, privately on your Mac.</p>
      <p class="empty">AI Lab OS turns local radar candidates, installed model inventory, benchmark artifacts, comparison scores, and keep/watch decisions into one auditable workflow.</p>
    </section>
    <section class="workflow-strip" aria-label="AI Lab OS workflow loop">
      {discover_step}
      {install_step}
      {benchmark_step}
      {compare_step}
      {decide_step}
    </section>
    {next_action}
    <section class="grid">
      {models_stat}
      {runs_stat}
      {avg_stat}
      {kept_stat}
    </section>
    <section class="home-columns">
      <section class="panel home-card home-results">
        <h2>Top Results</h2>
        {top_results}
      </section>
      {machine_card}
    </section>
    """.format(
        notice=_real_data_notice(counts["demo_models"]),
        discover_step=_workflow_step("Discover", ready_count, "ready candidates", "/radar"),
        install_step=_workflow_step("Install", installed_count, "detected local models", "/inventory"),
        benchmark_step=_workflow_step("Benchmark", artifact_counts["total"], "artifact directories", "/runs"),
        compare_step=_workflow_step("Compare", counts["eval_scores"], "imported scores", "/runs"),
        decide_step=_workflow_step("Decide", counts["decisions"], "recorded decisions", "/inventory"),
        next_action=_home_action_card(action),
        models_stat=_stat_card("Models", counts["models"], "ti-cube"),
        runs_stat=_stat_card("Runs", counts["model_runs"], "ti-player-play"),
        avg_stat=_stat_card("Average Score", _number(avg_score, 1, "0.0"), "ti-chart-line"),
        kept_stat=_stat_card("Kept Installed", keep_count, "ti-checkup-list"),
        top_results=_table(
            [
                "Model",
                "Score",
                "Status",
                "Label",
                "Tok/s",
                "System RAM GB",
                "Decision",
            ],
            top_rows,
            empty_message="No scored benchmark imports yet.",
            table_class="overview-table",
            header_tip_keys={**RESULT_TABLE_HEADER_TIPS, "Tok/s": "throughput"},
        ),
        machine_card=_machine_card(
            hardware_profiles,
            ready_count,
            artifact_counts,
            current_hardware_profile=current_hardware_profile,
        ),
    )
    return _layout("Home", "/", body)

__all__ = ('_count_local_inventory_models', '_home_next_action', '_overview',)
