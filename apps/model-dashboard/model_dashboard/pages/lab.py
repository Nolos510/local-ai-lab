"""Dashboard lab page."""

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
            "Capability",
            _pill("read-only"),
            "Hardware profile examples, readiness counts, and artifact counts",
            '<a href="/capability">Open capability view</a>',
        ],
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
        init_command = [
            "python3",
            "evals/local-llm-benchmark/harness.py",
            "init-run",
            "--benchmark-run-id",
            proposed_run_id,
            "--model-name",
            row.get("model_name", ""),
            "--backend",
            "Local OpenAI-compatible",
            "--temperature",
            "0.2",
            "--top-p",
            "0.9",
        ]
        run_command = [
            "python3",
            "evals/local-llm-benchmark/harness.py",
            "run-local",
            "--run-dir",
            f"data/eval_results/{proposed_run_id}",
            "--endpoint",
            "http://127.0.0.1:1234/v1",
            "--model",
            row.get("model_name", ""),
            "--force",
        ]
        command = "\n\n".join(
            [
                _command_lines(init_command),
                _command_lines(run_command),
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
                '<div class="cell-stack">{repo}<code>{owner}</code></div>'.format(
                    repo=_external_link_or_text(row.get("repo_url"), row.get("repo_name")),
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

__all__ = ('_lab',)
