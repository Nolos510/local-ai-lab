"""Dashboard overview page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

import csv
from html import escape
from pathlib import Path

from .. import capability, charts, db, discover, recommend
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


def _home_next_action(
    ready_count,
    installed_count,
    artifact_counts,
    real_counts,
    pending_import_count=None,
):
    importable_gap = (
        max(0, artifact_counts["with_dashboard_import"] - real_counts["model_runs"])
        if pending_import_count is None
        else pending_import_count
    )
    score_decision_gap = max(0, real_counts["eval_scores"] - real_counts["decisions"])
    if importable_gap:
        artifact_word = "set is" if importable_gap == 1 else "sets are"
        return {
            "title": "Import benchmark artifacts",
            "detail": f"{importable_gap} dashboard-import artifact {artifact_word} not reflected in the active dashboard database yet.",
            "href": "/runs",
            "label": "Open Benchmark",
            "kind": "import",
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


def _home_action_card(action, enable_import_actions=False, action_token=""):
    import_control = (
        _artifact_import_all_control(
            action.get("pending_import_count", 0),
            enable_import_actions=enable_import_actions,
            action_token=action_token,
        )
        if action.get("kind") == "import"
        else ""
    )
    return """
    <section class="panel do-next">
      <h2>Do This Next</h2>
      <h3>{title}</h3>
      <p class="empty">{detail}</p>
      <div class="home-actions">
        <a class="action-link" href="{href}">{label}</a>
        {import_control}
        <a class="action-link secondary" href="/reports">Export report</a>
      </div>
    </section>
    """.format(
        title=_text(action["title"]),
        detail=_text(action["detail"]),
        href=_text(action["href"]),
        label=_text(action["label"]),
        import_control=import_control,
    )


def _top_result_rows(summaries, *, limit=5):
    scored = [row for row in summaries if row["total_score"] not in (None, "")]
    scored.sort(
        key=lambda row: (
            0 if row["score_status"] == "confirmed" else 1,
            -float(row["total_score"]),
            str(row["model_name"]).casefold(),
        )
    )
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
                _number(row["tokens_per_sec"], fallback="—"),
                _number(row["ram_usage_gb"], fallback="—"),
                _text(row["decision"] if row["decision"] not in (None, "") else "—"),
            ]
        )
    return rows


def _machine_card(hardware_profiles, ready_count, artifact_counts, current_hardware_profile=None):
    profile = hardware_profiles[-1] if hardware_profiles else (current_hardware_profile or {})
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
    fit_summary = _fit_capacity_summary(profile.get("memory_gb"))
    if hardware_profiles:
        runtime_text = (
            ", ".join(runtimes) if isinstance(runtimes, list) and runtimes else "not recorded"
        )
        captured = profile.get("captured_at") or "capture time not recorded"
    elif current_hardware_profile:
        runtime_text = (
            ", ".join(runtimes)
            if isinstance(runtimes, list) and runtimes
            else "not found on PATH"
        )
        captured = (
            profile.get("captured_at")
            or "Live local read; run uv run ai-lab hardware snapshot to save a profile."
        )
    else:
        runtime_text = "not recorded"
        captured = "No saved hardware snapshot; run uv run ai-lab hardware snapshot."
    return """
    <section class="panel home-card">
      <h2>This Machine</h2>
      <dl class="machine-facts">
        <div><dt>Machine</dt><dd>{machine}</dd></div>
        <div><dt>Chip</dt><dd>{chip}</dd></div>
        <div><dt>Memory</dt><dd>{memory}</dd></div>
        <div><dt>Fit</dt><dd>{fit_summary}</dd></div>
        <div><dt>Runtimes</dt><dd>{runtimes}</dd></div>
        <div><dt>Snapshot</dt><dd>{captured}</dd></div>
        <div><dt>Readiness</dt><dd>{ready} ready candidates; {artifacts} benchmark artifact directories.</dd></div>
      </dl>
    </section>
    """.format(
        machine=_text(machine),
        chip=_text(chip),
        memory=_text(memory),
        fit_summary=fit_summary,
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
    upstream_state_path=RADAR_UPSTREAM_STATE_PATH,
    current_hardware_profile=None,
    enable_import_actions=False,
    action_token="",
    import_sync_result=None,
):
    counts = _real_counts(conn)
    candidates = _load_radar_candidates(registry_path, local_inventory_path)
    all_summaries = _authoritative_model_summaries(conn, candidates)
    summaries = _real_rows(all_summaries)
    task_summary = recommend.task_recommendations(_real_rows(db.list_score_details(conn)))
    score_values = [
        float(row["total_score"]) for row in summaries if row["total_score"] not in (None, "")
    ]
    avg_score = sum(score_values) / len(score_values) if score_values else None
    keep_count = sum(1 for row in summaries if row["keep_installed"] == 1)
    candidates = discover.candidate_lifecycle_rows(
        conn,
        candidates,
        upstream_state_path,
    )
    ungraduated_candidates = [row for row in candidates if not row.get("_graduated")]
    discover_count = len(ungraduated_candidates)
    ready_count = sum(
        1 for row in ungraduated_candidates if row.get("status") == "ready_for_eval"
    )
    installed_count = _count_local_inventory_models(local_inventory_path)
    artifact_counts = capability.benchmark_artifact_counts(Path(eval_results_dir))
    pending_import_count = len(_pending_artifact_run_ids(conn, eval_results_dir))
    hardware_profiles = capability.load_hardware_profiles(Path(hardware_profiles_dir), limit=1)
    action = _home_next_action(
        ready_count,
        installed_count,
        artifact_counts,
        counts,
        pending_import_count=pending_import_count,
    )
    action["pending_import_count"] = pending_import_count
    top_rows = _top_result_rows(summaries)
    body = """
    {import_sync_notice}
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
    {task_leaders}
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
        import_sync_notice=_import_sync_notice(import_sync_result),
        notice=_real_data_notice(counts["demo_models"]),
        discover_step=_workflow_step(
            "Discover",
            discover_count,
            "candidates to evaluate",
            "/radar",
        ),
        install_step=_workflow_step("Install", installed_count, "detected local models", "/inventory"),
        benchmark_step=_workflow_step("Benchmark", artifact_counts["total"], "artifact directories", "/runs"),
        compare_step=_workflow_step("Compare", counts["eval_scores"], "imported scores", "/runs"),
        decide_step=_workflow_step("Decide", counts["decisions"], "recorded decisions", "/inventory"),
        task_leaders=_task_leaders(task_summary, surface_class="task-leaders-home"),
        next_action=_home_action_card(
            action,
            enable_import_actions=enable_import_actions,
            action_token=action_token,
        ),
        models_stat=_stat_card("Models", counts["models"], "ti-cube"),
        runs_stat=_stat_card("Runs", counts["model_runs"], "ti-player-play"),
        avg_stat=_stat_card("Average Score", _number(avg_score, 1, "—"), "ti-chart-line"),
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
