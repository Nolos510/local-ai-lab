import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import csv_io, db, reports, server  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402

FIXTURE_DIR = APP_DIR / "fixtures"
CANDIDATE_FIELDS = [
    "candidate_id",
    "model_name",
    "model_family",
    "provider_or_org",
    "status",
    "format_or_runtime",
    "source_packet_path",
    "report_path",
    "benchmark_run_id",
    "model_page_url",
    "github_url",
    "lm_studio_url",
    "ollama_url",
    "runtime_availability",
    "local_runner",
    "local_model_id",
    "default_endpoint",
    "why_interesting",
    "risk_notes",
    "proposed_eval",
    "security_review_status",
    "download_approval",
    "license_review_status",
    "provenance_status",
    "security_notes",
    "isolation_notes",
    "security_review_path",
]
PROJECT_FIELDS = [
    "repo_id",
    "repo_name",
    "owner",
    "repo_url",
    "category",
    "status",
    "priority_score",
    "priority_rationale",
    "stars_observed",
    "license",
    "source_packet_path",
    "report_path",
    "why_interesting",
    "business_tie_in",
    "local_fit",
    "risk_notes",
    "recommended_next_step",
]


def write_candidate_registry(path, extra_rows=None):
    rows = [
        {
            "candidate_id": "20260603-ready-local",
            "model_name": "Ready Local 7B",
            "model_family": "Ready",
            "provider_or_org": "local",
            "status": "ready_for_eval",
            "format_or_runtime": "llama.cpp",
            "source_packet_path": "automations/ai-lab-radar/inputs/ready.md",
            "report_path": "automations/ai-lab-radar/reports/ready.md",
            "benchmark_run_id": "20260603-ready-local",
            "model_page_url": "https://huggingface.co/example/ready-local-7b",
            "github_url": "https://github.com/example/ready-local",
            "lm_studio_url": "",
            "ollama_url": "https://ollama.com/library/ready-local",
            "runtime_availability": "GGUF; LM Studio and Ollama metadata",
            "local_runner": "lmstudio-cli",
            "local_model_id": "ready-local-7b",
            "default_endpoint": "",
            "why_interesting": "Already installed for a local retest.",
            "risk_notes": "Needs scored evidence.",
            "proposed_eval": "Run the local benchmark prompt set.",
            "security_review_status": "local_inventory_reviewed",
            "download_approval": "not_needed_local",
            "license_review_status": "needs_review",
            "provenance_status": "local_inventory",
            "security_notes": "Already installed locally; no new download is approved.",
            "isolation_notes": "Run through the configured local runner only.",
            "security_review_path": "",
        },
        {
            "candidate_id": "20260603-watch-local",
            "model_name": "Watch Local 13B",
            "model_family": "Watch",
            "provider_or_org": "local",
            "status": "watchlist",
            "format_or_runtime": "MLX",
            "source_packet_path": "automations/ai-lab-radar/inputs/watch.md",
            "report_path": "automations/ai-lab-radar/reports/watch.md",
            "benchmark_run_id": "",
            "model_page_url": "",
            "github_url": "",
            "lm_studio_url": "",
            "ollama_url": "",
            "runtime_availability": "unknown",
            "local_runner": "",
            "local_model_id": "",
            "default_endpoint": "",
            "why_interesting": "Interesting but not ready.",
            "risk_notes": "Runtime unknown.",
            "proposed_eval": "Confirm local artifact first.",
            "security_review_status": "needs_review",
            "download_approval": "not_approved",
            "license_review_status": "unknown",
            "provenance_status": "unverified_local_note",
            "security_notes": "Publisher, license, artifact path, and checksum are unknown.",
            "isolation_notes": "Do not install or run until provenance is reviewed.",
            "security_review_path": (
                "automations/ai-lab-radar/security-reviews/watch-local-13b.md"
            ),
        },
    ]
    if extra_rows:
        rows.extend(extra_rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_project_registry(path):
    rows = [
        {
            "repo_id": "20260605-local-runtime",
            "repo_name": "Local Runtime",
            "owner": "example",
            "repo_url": "https://github.com/example/local-runtime",
            "category": "local inference",
            "status": "ready_for_review",
            "priority_score": "5",
            "priority_rationale": "Core local runtime for larger models.",
            "stars_observed": "100k",
            "license": "MIT",
            "source_packet_path": "automations/ai-lab-radar/inputs/projects.md",
            "report_path": "automations/ai-lab-radar/reports/projects.md",
            "why_interesting": "Strong local inference candidate.",
            "business_tie_in": "Supports benchmark serving.",
            "local_fit": "Self-hosted local path.",
            "risk_notes": "Review before install.",
            "recommended_next_step": "Inspect runtime path.",
        },
        {
            "repo_id": "20260605-agent-watch",
            "repo_name": "Agent Watch",
            "owner": "example",
            "repo_url": "https://github.com/example/agent-watch",
            "category": "multi-agent framework",
            "status": "watchlist",
            "priority_score": "2",
            "priority_rationale": "Interesting reference but less urgent.",
            "stars_observed": "50k",
            "license": "MIT",
            "source_packet_path": "automations/ai-lab-radar/inputs/projects.md",
            "report_path": "automations/ai-lab-radar/reports/projects.md",
            "why_interesting": "Agent orchestration reference.",
            "business_tie_in": "Could support business process simulations.",
            "local_fit": "Needs provider review.",
            "risk_notes": "Telemetry unclear.",
            "recommended_next_step": "Review local provider support.",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROJECT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_dashboard_import_fixture(artifact_dir, run_id="20260605-import-fixture"):
    import_dir = artifact_dir / "dashboard-import"
    import_dir.mkdir(parents=True)
    rows_by_table = {
        "models": [
            {
                "id": "101",
                "model_name": "Import Fixture Model",
                "model_family": "Import",
                "provider": "local",
                "params_b": "24",
                "license": "reviewed",
                "source_url": "local-registry://import-fixture",
                "notes": "Fixture artifact for import action tests.",
            }
        ],
        "model_runs": [
            {
                "id": "202",
                "model_id": "101",
                "date_tested": "2026-06-05",
                "backend": "LM Studio CLI",
                "format": "MLX",
                "quantization": "4bit",
                "context_window": "4096",
                "hardware": "test hardware",
                "temperature": "0.2",
                "top_p": "0.9",
                "tokens_per_sec": "42",
                "ram_usage_gb": "32",
                "stability_notes": "Fixture only.",
                "run_notes": f"benchmark_run_id={run_id} | artifact_import_test=yes",
            }
        ],
        "eval_scores": [
            {
                "id": "303",
                "run_id": "202",
                **{field: "70" for field in METRIC_FIELDS},
                "total_score": "70",
                "final_label": "WATCHLIST",
                "score_status": "confirmed",
            }
        ],
        "decisions": [
            {
                "id": "404",
                "model_id": "101",
                "decision": "watchlist",
                "keep_installed": "0",
                "best_use_case": "Fixture import validation.",
                "weakness": "Synthetic.",
                "retest_condition": "Never.",
                "created_at": "2026-06-05T12:00:00",
            }
        ],
    }
    for table_name, rows in rows_by_table.items():
        with (import_dir / f"{table_name}.csv").open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=csv_io.TABLE_FIELDS[table_name])
            writer.writeheader()
            writer.writerows(rows)
    return import_dir


class ModelDashboardQaTests(unittest.TestCase):
    def test_fixture_import_loads_expected_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"

            counts = csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            self.assertEqual(
                counts,
                {
                    "models": 4,
                    "model_runs": 4,
                    "eval_scores": 4,
                    "decisions": 4,
                },
            )
            with db.connect(db_path) as conn:
                self.assertEqual(db.table_count(conn, "models"), 4)
                self.assertEqual(db.table_count(conn, "model_runs"), 4)
                self.assertEqual(db.table_count(conn, "eval_scores"), 4)
                self.assertEqual(db.table_count(conn, "decisions"), 4)
                summaries = db.list_model_summaries(conn)
                self.assertEqual(len(summaries), 4)
                self.assertEqual(summaries[0]["model_name"], "Qwen2.5-Coder 14B Instruct")

    def test_sqlite_schema_enforces_foreign_keys_and_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)

            with db.connect(db_path) as conn:
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute(
                        """
                        INSERT INTO model_runs (id, model_id, date_tested, backend)
                        VALUES (1, 999, '2026-05-01', 'llama.cpp')
                        """
                    )

                conn.execute(
                    """
                    INSERT INTO models (id, model_name)
                    VALUES (1, 'Schema Test Model')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend)
                    VALUES (1, 1, '2026-05-01', 'llama.cpp')
                    """
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute(
                        """
                        INSERT INTO eval_scores (
                            id,
                            run_id,
                            instruction_following,
                            truthfulness_uncertainty,
                            reasoning,
                            coding_debugging,
                            agent_planning,
                            local_ai_lab_usefulness,
                            research_synthesis,
                            business_seo_strategy,
                            long_context,
                            creativity,
                            speed_practicality,
                            total_score,
                            final_label,
                            score_status
                        )
                        VALUES (
                            1, 1, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
                            'NOT_A_LABEL', 'confirmed'
                        )
                        """
                    )

    def test_csv_export_round_trips_importable_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_db = tmp_path / "source.sqlite"
            exported_dir = tmp_path / "exports"
            round_trip_db = tmp_path / "round-trip.sqlite"

            csv_io.import_fixture_set(source_db, FIXTURE_DIR)
            exported = csv_io.export_all(source_db, exported_dir)

            for table_name, path in exported.items():
                self.assertTrue(path.exists(), table_name)
                with path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    self.assertEqual(tuple(reader.fieldnames), csv_io.TABLE_FIELDS[table_name])

            counts = csv_io.import_all(round_trip_db, exported)
            self.assertEqual(
                counts,
                {
                    "models": 4,
                    "model_runs": 4,
                    "eval_scores": 4,
                    "decisions": 4,
                },
            )

    def test_markdown_report_hides_fixture_data_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            report = reports.generate_markdown_report(db_path)

            self.assertIn("Models tracked: 0", report)
            self.assertIn("Demo fixture models hidden: 4", report)
            self.assertIn("No real benchmark imports yet.", report)
            self.assertNotIn("ResearchLite Local 7B", report)
            self.assertNotIn("TinyCoder Local 1.1B", report)
            self.assertNotIn("Qwen2.5-Coder 14B Instruct", report)

    def test_markdown_report_can_include_demo_data_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            report = reports.generate_markdown_report(db_path, include_demo=True)

            self.assertIn("Models tracked: 4", report)
            self.assertIn("ResearchLite Local 7B", report)
            self.assertIn("TinyCoder Local 1.1B", report)
            self.assertIn("Qwen2.5-Coder 14B Instruct", report)

    def test_overview_hides_fixture_data_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            with db.connect(db_path) as conn:
                html = server._overview(conn)

            self.assertIn("Real Data View", html)
            self.assertIn("This page hides 4 demo fixture model rows", html)
            self.assertIn("No real benchmark imports yet.", html)
            self.assertNotIn("TinyCoder Local 1.1B</a>", html)
            self.assertNotIn("Qwen2.5-Coder 14B Instruct</a>", html)

    def test_demo_page_shows_fixture_data_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            with db.connect(db_path) as conn:
                html = server._demo(conn)

            self.assertIn("Demo Data", html)
            self.assertIn("TinyCoder Local 1.1B", html)
            self.assertIn("Qwen2.5-Coder 14B Instruct", html)

    def test_radar_filters_candidate_registry_by_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._radar(
                    conn,
                    {"status": ["ready_for_eval"]},
                    registry_path=registry_path,
                )

            self.assertIn("Radar Candidates (1 of 2)", html)
            self.assertIn("Ready Local 7B", html)
            self.assertIn("/artifacts/20260603-ready-local", html)
            self.assertNotIn("Watch Local 13B", html)

    def test_radar_shows_model_store_links_and_runtime_availability(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._radar(conn, {"q": ["Ollama"]}, registry_path=registry_path)

            self.assertIn("Radar Candidates (1 of 2)", html)
            self.assertIn("Runtime availability", html)
            self.assertIn("GGUF; LM Studio and Ollama metadata", html)
            self.assertIn("Model/source page", html)
            self.assertIn("https://huggingface.co/example/ready-local-7b", html)
            self.assertIn("GitHub", html)
            self.assertIn("https://github.com/example/ready-local", html)
            self.assertIn("Ollama", html)
            self.assertIn("https://ollama.com/library/ready-local", html)
            self.assertNotIn("Watch Local 13B", html)

    def test_radar_shows_and_filters_security_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._radar(
                    conn,
                    {"security": ["needs_review"]},
                    registry_path=registry_path,
                )

            self.assertIn("Security Gate", html)
            self.assertIn("Radar Candidates (1 of 2)", html)
            self.assertIn("Watch Local 13B", html)
            self.assertIn("Security gate", html)
            self.assertIn("Download", html)
            self.assertIn("not_approved", html)
            self.assertIn("Review artifact", html)
            self.assertIn(
                "automations/ai-lab-radar/security-reviews/watch-local-13b.md",
                html,
            )
            self.assertIn("Publisher, license, artifact path, and checksum are unknown.", html)
            self.assertNotIn("Ready Local 7B", html)

    def test_radar_missing_registry_renders_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)

            with db.connect(db_path) as conn:
                html = server._radar(conn, registry_path=Path(tmp) / "missing.csv")

            self.assertIn("Radar Candidates", html)
            self.assertIn("No candidates match these filters.", html)

    def test_artifact_detail_links_only_registry_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._artifact_detail(
                    conn,
                    "20260603-ready-local",
                    registry_path=registry_path,
                )
                missing_html = server._artifact_detail(
                    conn,
                    "20260603-unregistered",
                    registry_path=registry_path,
                )

            self.assertIn("Ready Local 7B", html)
            self.assertIn("not imported", html)
            self.assertIn("Artifact not found", missing_html)

    def test_artifact_detail_renders_import_guidance_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            eval_results = tmp_path / "eval_results"
            run_id = "20260603-ready-local"
            artifact_dir = eval_results / run_id
            artifact_dir.mkdir(parents=True)
            write_dashboard_import_fixture(artifact_dir, run_id)
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            old_eval_results_dir = server.EVAL_RESULTS_DIR
            try:
                server.EVAL_RESULTS_DIR = eval_results
                with db.connect(db_path) as conn:
                    html = server._artifact_detail(
                        conn,
                        run_id,
                        registry_path=registry_path,
                        database_path=db_path,
                    )
            finally:
                server.EVAL_RESULTS_DIR = old_eval_results_dir

        self.assertIn("Dashboard Import", html)
        self.assertIn('<button type="button" disabled>Import Artifact</button>', html)
        self.assertIn("--enable-import-actions", html)
        self.assertIn("python3", html)
        self.assertIn("apps/model-dashboard/run_dashboard.py", html)
        self.assertIn("import-csv", html)
        self.assertIn("dashboard-import/models.csv", html)
        self.assertIn("report", html)

    def test_artifact_import_action_imports_existing_dashboard_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            eval_results = tmp_path / "eval_results"
            run_id = "20260605-import-fixture"
            artifact_dir = eval_results / run_id
            artifact_dir.mkdir(parents=True)
            write_dashboard_import_fixture(artifact_dir, run_id)

            result = server._import_artifact(run_id, db_path, eval_results)

            self.assertEqual(
                result["counts"],
                {
                    "models": 1,
                    "model_runs": 1,
                    "eval_scores": 1,
                    "decisions": 1,
                },
            )
            with db.connect(db_path) as conn:
                self.assertEqual(db.table_count(conn, "models"), 1)
                self.assertEqual(db.table_count(conn, "model_runs"), 1)
                self.assertEqual(db.table_count(conn, "eval_scores"), 1)
                self.assertEqual(db.table_count(conn, "decisions"), 1)

    def test_artifact_import_rejects_traversal_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            eval_results = tmp_path / "eval_results"
            outside = tmp_path / "outside"
            outside.mkdir(parents=True)
            write_dashboard_import_fixture(outside, "outside")

            with self.assertRaises(ValueError):
                server._import_artifact("../outside", db_path, eval_results)

    def test_artifact_detail_rejects_traversal_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)

            with db.connect(db_path) as conn:
                html = server._artifact_detail(conn, "../")

            self.assertIn("Artifact not found", html)

    def test_artifact_import_control_enabled_only_with_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            eval_results = tmp_path / "eval_results"
            run_id = "20260605-import-fixture"
            artifact_dir = eval_results / run_id
            artifact_dir.mkdir(parents=True)
            write_dashboard_import_fixture(artifact_dir, run_id)

            disabled_html = server._artifact_import_control(
                run_id,
                enable_import_actions=False,
                action_token="fixture-token",
                eval_results_dir=eval_results,
            )
            enabled_html = server._artifact_import_control(
                run_id,
                enable_import_actions=True,
                action_token="fixture-token",
                eval_results_dir=eval_results,
            )

        self.assertIn("disabled", disabled_html)
        self.assertIn("--enable-import-actions", disabled_html)
        self.assertNotIn('method="post"', disabled_html)
        self.assertIn('method="post" action="/actions/import-artifact"', enabled_html)
        self.assertIn('name="token" value="fixture-token"', enabled_html)
        self.assertIn('name="benchmark_run_id" value="20260605-import-fixture"', enabled_html)

    def test_model_detail_renders_unsafe_source_url_as_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, provider, source_url)
                    VALUES (1, 'Unsafe Source Model', 'local', 'javascript:alert(1)')
                    """
                )
                html = server._model_detail(conn, 1)

            self.assertIn("Unsafe Source Model", html)
            self.assertNotIn('href="javascript:alert(1)"', html)

    def test_model_detail_tables_use_expandable_column_layouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (5, 'Detail Layout Model', 'Qwen', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, run_notes
                    )
                    VALUES (
                        10,
                        5,
                        '2026-06-05',
                        'LM Studio CLI',
                        'benchmark_run_id=20260605-detail-layout'
                    )
                    """
                )
                score_fields = ", ".join(METRIC_FIELDS)
                score_placeholders = ", ".join("72" for _ in METRIC_FIELDS)
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id,
                        run_id,
                        {score_fields},
                        total_score,
                        final_label,
                        score_status
                    )
                    VALUES (11, 10, {score_placeholders}, 72.5, 'WATCHLIST', 'confirmed')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO decisions (
                        id,
                        model_id,
                        decision,
                        keep_installed,
                        best_use_case,
                        weakness,
                        retest_condition,
                        created_at
                    )
                    VALUES (
                        12,
                        5,
                        'watchlist',
                        1,
                        'Fast local coding',
                        'Needs retest',
                        'Retest after import',
                        '2026-06-06T12:18:06+00:00'
                    )
                    """
                )
                html = server._model_detail(conn, 5)

            self.assertIn('class="model-detail-runs-table"', html)
            self.assertIn('class="model-detail-decisions-table"', html)
            self.assertIn(".model-detail-runs-table {", html)
            self.assertIn(".model-detail-decisions-table {", html)
            self.assertIn("min-width: 1280px", html)
            self.assertIn("min-width: 1180px", html)
            self.assertIn("white-space: nowrap", html)

    def test_project_repo_url_rejects_unsafe_scheme(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "github_repos.csv"
            write_project_registry(registry_path)
            with registry_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["repo_url"] = "javascript:alert(1)"
            with registry_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=PROJECT_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

            html = server._projects(registry_path=registry_path)

            self.assertIn("Local Runtime", html)
            self.assertNotIn('href="javascript:alert(1)"', html)

    def test_dashboard_loop_links_imported_runs_to_artifacts_and_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            eval_results = tmp_path / "eval_results"
            run_id = "20260605-loop-test"
            artifact_dir = eval_results / run_id
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "raw_responses.jsonl").write_text(
                '{"prompt_id": "LLMCORE-v0.1-001"}\n', encoding="utf-8"
            )
            write_candidate_registry(
                registry_path,
                extra_rows=[
                    {
                        "candidate_id": "20260605-loop-candidate",
                        "model_name": "Loop Link Model",
                        "model_family": "Loop",
                        "provider_or_org": "local",
                        "status": "ready_for_eval",
                        "format_or_runtime": "LM Studio",
                        "source_packet_path": "automations/ai-lab-radar/inputs/loop.md",
                        "report_path": "automations/ai-lab-radar/reports/loop.md",
                        "benchmark_run_id": run_id,
                        "why_interesting": "Tests the dashboard product loop.",
                        "risk_notes": "Fixture only.",
                        "proposed_eval": "Inspect links.",
                    }
                ],
            )
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (42, 'Loop Link Model', 'Loop', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes)
                    VALUES (
                        77,
                        42,
                        '2026-06-05',
                        'LM Studio',
                        'benchmark_run_id=20260605-loop-test | raw_artifact=local'
                    )
                    """
                )
                score_fields = ", ".join(METRIC_FIELDS)
                score_placeholders = ", ".join("80" for _ in METRIC_FIELDS)
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id,
                        run_id,
                        {score_fields},
                        total_score,
                        final_label,
                        score_status
                    )
                    VALUES (5, 77, {score_placeholders}, 80, 'DAILY_DRIVER', 'confirmed')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO decisions (
                        id,
                        model_id,
                        decision,
                        keep_installed,
                        best_use_case,
                        weakness,
                        retest_condition
                    )
                    VALUES (
                        6,
                        42,
                        'keep',
                        1,
                        'Loop validation',
                        'Fixture only',
                        'Retest never'
                    )
                    """
                )
                old_eval_results_dir = server.EVAL_RESULTS_DIR
                try:
                    server.EVAL_RESULTS_DIR = eval_results
                    runs_html = server._runs(conn)
                    detail_html = server._model_detail(conn, 42)
                    artifact_html = server._artifact_detail(
                        conn, run_id, registry_path=registry_path
                    )
                finally:
                    server.EVAL_RESULTS_DIR = old_eval_results_dir

            self.assertIn("/artifacts/20260605-loop-test", runs_html)
            self.assertIn("/artifacts/20260605-loop-test", detail_html)
            self.assertIn("imported model", artifact_html)
            self.assertIn("decision: keep", artifact_html)
            self.assertIn("Loop Link Model", artifact_html)

    def test_runs_compare_and_storage_filters_real_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (1, 'Qwen Filter Model', 'Qwen', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (2, 'Research Filter Model', 'Research', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes)
                    VALUES (1, 1, '2026-06-05', 'LM Studio CLI', 'benchmark_run_id=qwen-filter')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes)
                    VALUES (2, 2, '2026-06-05', 'Ollama', 'benchmark_run_id=research-filter')
                    """
                )
                score_fields = ", ".join(METRIC_FIELDS)
                score_values = ", ".join("80" for _ in METRIC_FIELDS)
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id, run_id, {score_fields}, total_score, final_label, score_status
                    )
                    VALUES (1, 1, {score_values}, 80, 'CODING_SPECIALIST', 'confirmed')
                    """
                )
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id, run_id, {score_fields}, total_score, final_label, score_status
                    )
                    VALUES (2, 2, {score_values}, 80, 'RESEARCH_SPECIALIST', 'draft')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO decisions (
                        id, model_id, decision, keep_installed, best_use_case
                    )
                    VALUES (1, 1, 'keep', 1, 'Coding')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO decisions (
                        id, model_id, decision, keep_installed, best_use_case
                    )
                    VALUES (2, 2, 'watchlist', 0, 'Research')
                    """
                )

                runs_html = server._runs(conn, {"backend": ["LM Studio CLI"]})
                compare_html = server._compare(conn, {"status": ["draft"]})
                storage_html = server._storage(conn, {"keep": ["yes"]})

            self.assertIn("Model Runs (1 of 2)", runs_html)
            self.assertIn('class="runs-table"', runs_html)
            self.assertIn("Qwen Filter Model", runs_html)
            self.assertNotIn("Research Filter Model", runs_html)
            self.assertIn("Compare Models (1 of 2)", compare_html)
            self.assertIn("Research Filter Model", compare_html)
            self.assertNotIn("Qwen Filter Model", compare_html)
            self.assertIn("Decision Log (1 of 2)", storage_html)
            self.assertIn("Qwen Filter Model", storage_html)
            self.assertNotIn("Research Filter Model", storage_html)

    def test_compare_page_renders_perf_empty_state_for_null_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (1, 'Perf Empty Model', 'Perf', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend)
                    VALUES (1, 1, '2026-06-18', 'LM Studio CLI')
                    """
                )
                score_fields = ", ".join(METRIC_FIELDS)
                score_values = ", ".join("70" for _ in METRIC_FIELDS)
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id, run_id, {score_fields}, total_score, final_label, score_status
                    )
                    VALUES (1, 1, {score_values}, 70, 'WATCHLIST', 'confirmed')
                    """
                )

                html = server._compare(conn)

            self.assertIn("Performance Signals", html)
            self.assertIn("No tokens/sec values imported yet", html)
            self.assertIn("No TTFT values imported yet", html)
            self.assertIn("No total latency values imported yet", html)

    def test_compare_page_renders_perf_values_when_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (1, 'Perf Populated Model', 'Perf', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend,
                        tokens_per_sec, ttft_seconds, total_latency_seconds
                    )
                    VALUES (1, 1, '2026-06-18', 'LM Studio CLI', 27.5, 0.42, 12.3)
                    """
                )
                score_fields = ", ".join(METRIC_FIELDS)
                score_values = ", ".join("75" for _ in METRIC_FIELDS)
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id, run_id, {score_fields}, total_score, final_label, score_status
                    )
                    VALUES (1, 1, {score_values}, 75, 'CODING_SPECIALIST', 'confirmed')
                    """
                )

                html = server._compare(conn)

            self.assertIn("Performance Signals", html)
            self.assertIn("Perf Populated Model (LM Studio CLI)", html)
            self.assertIn("27.5 tok/s", html)
            self.assertIn("0.42s", html)
            self.assertIn("12.30s", html)

    def test_lab_dashboard_shows_product_loop_and_next_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            eval_results = tmp_path / "eval_results"
            artifact_dir = eval_results / "20260603-ready-local"
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "raw_responses.jsonl").write_text(
                '{"prompt_id": "LLMCORE-v0.1-001"}\n', encoding="utf-8"
            )
            write_dashboard_import_fixture(artifact_dir, "20260603-ready-local")

            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._lab(
                    conn,
                    registry_path=registry_path,
                    eval_results_dir=eval_results,
                    project_registry_path=tmp_path / "missing-projects.csv",
                )

            self.assertIn("Lab Dashboard", html)
            self.assertIn("Product Loop", html)
            self.assertIn("Ready Local 7B", html)
            self.assertIn("python3 evals/local-llm-benchmark/harness.py run-local", html)
            self.assertIn("/artifacts/20260603-ready-local", html)
            self.assertIn("Benchmark Artifacts", html)
            self.assertIn("Run button disabled", html)
            self.assertIn("Import Artifact", html)
            self.assertIn("--enable-import-actions", html)
            self.assertIn("import-csv", html)
            self.assertIn("ready-local-7b", html)
            self.assertIn("/capability", html)

    def test_capability_page_renders_empty_hardware_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "missing-candidates.csv"
            eval_results = tmp_path / "missing-eval-results"
            hardware_profiles = tmp_path / "missing-hardware"
            db.init_db(db_path, reset=True)

            with db.connect(db_path) as conn:
                html = server._capability(
                    conn,
                    registry_path=registry_path,
                    eval_results_dir=eval_results,
                    hardware_profiles_dir=hardware_profiles,
                )

            self.assertIn("Capability", html)
            self.assertIn("Capability Boundary", html)
            self.assertIn("No committed hardware profile JSON examples found", html)
            self.assertIn("uv run ai-lab bench matrix --limit 5", html)
            self.assertIn("No ready_for_eval candidates are registered.", html)
            self.assertIn("Performance Signals", html)
            self.assertIn("No tokens/sec values imported yet", html)
            self.assertIn("No TTFT values imported yet", html)
            self.assertIn("No total latency values imported yet", html)
            self.assertIn("capability-chart-grid", html)
            self.assertIn('data-chart-dialog="capability-chart-tokens"', html)
            self.assertIn('<dialog class="chart-dialog" id="capability-chart-tokens"', html)

    def test_capability_page_renders_candidate_and_artifact_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            eval_results = tmp_path / "eval_results"
            hardware_profiles = tmp_path / "lab-notes"
            artifact_dir = eval_results / "20260603-ready-local"
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "raw_responses.jsonl").write_text(
                '{"prompt_id": "LLMCORE-v0.1-001"}\n',
                encoding="utf-8",
            )
            (artifact_dir / "scores.json").write_text("{}", encoding="utf-8")
            (artifact_dir / "decision.json").write_text("{}", encoding="utf-8")
            (artifact_dir / "dashboard-import").mkdir()
            hardware_profiles.mkdir()
            (hardware_profiles / "hardware-snapshot-example.json").write_text(
                json.dumps(
                    {
                        "schema_version": "hardware-snapshot-v0.1",
                        "captured_at": "2026-06-17T12:00:00Z",
                        "os": {"system": "Darwin", "release": "26.3.1"},
                        "python": {"implementation": "CPython", "version": "3.12.0"},
                        "machine": {"machine": "arm64", "cpu_count": 32},
                        "macos": {
                            "chip_brand": "Apple M3 Ultra",
                            "memory_bytes": 274877906944,
                        },
                        "runtimes": {
                            "lms": {"present": True, "version": "0.3"},
                            "ollama": {"present": False, "version": None},
                        },
                    }
                ),
                encoding="utf-8",
            )
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._capability(
                    conn,
                    registry_path=registry_path,
                    eval_results_dir=eval_results,
                    hardware_profiles_dir=hardware_profiles,
                )

            self.assertIn("hardware-snapshot-example.json", html)
            self.assertIn("Apple M3 Ultra", html)
            self.assertIn("256.0", html)
            self.assertIn("lms", html)
            self.assertIn("Ready Local 7B", html)
            self.assertIn("preflight gates clear", html)
            self.assertIn("watchlist", html)
            self.assertNotIn("/Users/", html)
            self.assertIn("Artifact directories", html)
            self.assertIn("Dashboard-import folders", html)
            self.assertIn("/artifacts/20260603-ready-local", html)

    def test_capability_page_renders_perf_values_when_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (1, 'Capability Perf Model', 'Perf', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend,
                        tokens_per_sec, ttft_seconds, total_latency_seconds
                    )
                    VALUES (1, 1, '2026-06-18', 'LM Studio CLI', 33.3, 0.77, 14.9)
                    """
                )
                html = server._capability(
                    conn,
                    registry_path=tmp_path / "missing-candidates.csv",
                    eval_results_dir=tmp_path / "missing-eval-results",
                    hardware_profiles_dir=tmp_path / "missing-hardware",
                )

            self.assertIn("Performance Signals", html)
            self.assertIn("Capability Perf Model (LM Studio CLI)", html)
            self.assertIn("33.3 tok/s", html)
            self.assertIn("0.77s", html)
            self.assertIn("14.90s", html)
            self.assertIn('<strong class="chart-summary-value">33.3 tok/s</strong>', html)
            self.assertIn('<strong class="chart-summary-value">0.77s</strong>', html)
            self.assertIn('<strong class="chart-summary-value">14.90s</strong>', html)
            self.assertIn('data-field="tokens_per_sec"', html)
            self.assertIn('data-chart-dialog="capability-chart-tokens"', html)
            self.assertIn('data-chart-dialog="capability-chart-ttft"', html)
            self.assertIn('data-chart-dialog="capability-chart-latency"', html)

    def test_capability_perf_summary_hides_missing_perf_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider)
                    VALUES (1, 'Partial Perf Model', 'Perf', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec
                    )
                    VALUES (1, 1, '2026-06-18', 'LM Studio CLI', 66.5)
                    """
                )
                html = server._capability(
                    conn,
                    registry_path=tmp_path / "missing-candidates.csv",
                    eval_results_dir=tmp_path / "missing-eval-results",
                    hardware_profiles_dir=tmp_path / "missing-hardware",
                )

            self.assertIn('<strong class="chart-summary-value">66.5 tok/s</strong>', html)
            self.assertIn("No TTFT values imported yet", html)
            self.assertIn("No total latency values imported yet", html)

    def test_capability_chart_dialog_styles_and_script_are_inline(self):
        html = server._layout("Capability", "/capability", "<p>Body</p>")

        self.assertIn(".chart-panel-large {", html)
        self.assertIn(".chart-summary-value {", html)
        self.assertIn(".chart-dialog {", html)
        self.assertIn("dialog.showModal()", html)
        self.assertIn("document.querySelectorAll('[data-chart-dialog]')", html)

    def test_capability_page_uses_no_external_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._capability(
                    conn,
                    registry_path=registry_path,
                    eval_results_dir=tmp_path / "eval_results",
                    hardware_profiles_dir=tmp_path / "lab-notes",
                )

            for chunk in html.split("<script")[1:]:
                opening_tag = chunk.split(">", 1)[0]
                self.assertNotIn(
                    "src=", opening_tag, "dashboard scripts must be inline (no external src)"
                )
            self.assertNotIn("<link", html)
            self.assertNotIn("http://", html)
            self.assertNotIn("https://", html)

    def test_collapsed_sidebar_keeps_labels_and_uses_css_tooltips(self):
        html = server._layout("Fixture", "/lab", "<p>Body</p>")

        self.assertIn('data-label="Lab Dashboard"', html)
        self.assertIn('title="Lab Dashboard"', html)
        self.assertIn("<span>Lab Dashboard</span>", html)
        self.assertIn(".app.collapsed .sidebar .nav::after", html)
        self.assertIn("content: attr(data-label)", html)
        self.assertIn("clip: rect(0 0 0 0)", html)
        self.assertNotIn(".app.collapsed .sidebar .nav span { display: none", html)

    def test_table_wrapper_keeps_horizontal_scroll_after_theme_styles(self):
        html = server._layout("Fixture", "/radar", "<p>Body</p>")
        table_wrap_rules = [
            rule.split("}", 1)[0]
            for rule in html.split(".table-wrap {")[1:]
        ]

        self.assertGreaterEqual(len(table_wrap_rules), 2)
        self.assertIn("overflow-x: auto", table_wrap_rules[-1])
        self.assertIn("overflow-y: hidden", table_wrap_rules[-1])
        self.assertNotIn("overflow: hidden", table_wrap_rules[-1])

    def test_table_cells_scroll_when_content_is_tall(self):
        table_html = server._table(["Long"], [["A long note"]])
        layout_html = server._layout("Fixture", "/runs", table_html)

        self.assertIn('<div class="cell-scroll">A long note</div>', table_html)
        self.assertIn(".cell-scroll {", layout_html)
        self.assertIn("max-height: 220px", layout_html)
        self.assertIn("overflow: auto", layout_html)
        self.assertIn("overscroll-behavior: contain", layout_html)

    def test_model_runs_table_keeps_date_column_readable(self):
        html = server._layout("Fixture", "/runs", "<p>Body</p>")

        self.assertIn(".runs-table {", html)
        self.assertIn("min-width: 1380px", html)
        self.assertIn(".runs-table th:nth-child(1)", html)
        self.assertIn("white-space: nowrap", html)
        self.assertIn("overflow-wrap: normal", html)

    def test_lab_dashboard_can_enable_run_test_button_for_local_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(registry_path)

            with db.connect(db_path) as conn:
                html = server._lab(
                    conn,
                    registry_path=registry_path,
                    eval_results_dir=tmp_path / "eval_results",
                    project_registry_path=tmp_path / "missing-projects.csv",
                    enable_run_tests=True,
                    action_token="fixture-token",
                )

            self.assertIn('method="post" action="/actions/run-test"', html)
            self.assertIn('name="token" value="fixture-token"', html)
            self.assertIn('name="candidate_id" value="20260603-ready-local"', html)
            self.assertIn("Run Test", html)
            self.assertIn("LM Studio CLI", html)

    def test_run_button_command_builder_uses_fixed_lmstudio_cli_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = {
                "candidate_id": "20260603-ready-local",
                "model_name": "Ready Local 7B",
                "model_family": "Ready",
                "provider_or_org": "local",
                "format_or_runtime": "MLX",
                "model_page_url": "https://huggingface.co/example/ready-local-7b",
                "local_runner": "lmstudio-cli",
                "local_model_id": "ready-local-7b",
            }

            init_command, capture_command = server._build_candidate_commands(
                row,
                "20260605-ready-local-test",
                Path(tmp),
            )

            self.assertIn("init-run", init_command)
            self.assertIn("--benchmark-run-id", init_command)
            self.assertIn("run-lmstudio-cli", capture_command)
            self.assertIn("--model-id", capture_command)
            self.assertIn("ready-local-7b", capture_command)
            self.assertNotIn("download", " ".join(capture_command))

    def test_run_test_actions_require_loopback_host(self):
        self.assertTrue(server._is_loopback_host("localhost"))
        self.assertTrue(server._is_loopback_host("127.0.0.1"))
        self.assertFalse(server._is_loopback_host("192.168.1.10"))

    def test_inventory_renders_manual_refresh_empty_state(self):
        html = server._inventory(action_token="fixture-token")

        self.assertIn("Installed Models", html)
        self.assertIn('action="/actions/refresh-inventory"', html)
        self.assertIn("Last refresh: not checked yet", html)
        self.assertIn('method="get" action="/inventory"', html)
        self.assertIn("No inventory refresh has run yet.", html)

    def test_inventory_filters_detected_models_by_runtime_and_registry_match(self):
        result = {
            "checked_at": "2026-06-05T12:00:00-07:00",
            "checks": [],
            "models": [
                {
                    "runtime": "LM Studio",
                    "model_id": "qwen3-coder-30b-a3b-instruct-mlx",
                    "display_name": "Qwen3 Coder 30B",
                    "status": "loaded",
                },
                {
                    "runtime": "Ollama",
                    "model_id": "unregistered:latest",
                    "display_name": "Unregistered",
                    "status": "installed",
                },
            ],
        }

        html = server._inventory(
            {"runtime": ["LM Studio"], "match": ["registered"]},
            inventory_result=result,
            action_token="fixture-token",
            enable_run_tests=True,
        )

        self.assertIn("Qwen3 Coder 30B", html)
        self.assertIn("20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit", html)
        self.assertIn("Run Test", html)
        self.assertIn("Detected Models (1 of 2)", html)
        self.assertNotIn("unregistered:latest", html)

    def test_inventory_filesystem_only_rows_do_not_show_run_button(self):
        result = {
            "checked_at": "2026-06-05T12:00:00-07:00",
            "checks": [],
            "models": [
                {
                    "runtime": "LM Studio",
                    "model_id": "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
                    "display_name": "Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
                    "status": "filesystem_only",
                    "source_path": "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
                    "local_path": (
                        "/Users/example/.lmstudio/models/"
                        "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit"
                    ),
                },
            ],
        }

        html = server._inventory(
            {"status": ["filesystem_only"]},
            inventory_result=result,
            action_token="fixture-token",
            enable_run_tests=True,
        )

        self.assertIn("filesystem_only", html)
        self.assertIn("Local file path", html)
        self.assertIn(
            "/Users/example/.lmstudio/models/"
            "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
            html,
        )
        self.assertIn("Filesystem-only; index/load in LM Studio first", html)
        self.assertIn("20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit", html)
        self.assertNotIn('action="/actions/run-test"', html)

    def test_inventory_stale_lmstudio_path_does_not_show_remove_button(self):
        with tempfile.TemporaryDirectory() as tmp:
            lmstudio_root = Path(tmp) / "lmstudio"
            result = {
                "checked_at": "2026-06-05T12:00:00-07:00",
                "checks": [],
                "models": [
                    {
                        "runtime": "LM Studio",
                        "model_id": "nomic-ai/nomic-embed-text-v1.5-GGUF/model.gguf",
                        "display_name": "Nomic Embed Text",
                        "status": "indexed",
                        "source_path": "nomic-ai/nomic-embed-text-v1.5-GGUF/model.gguf",
                        "local_path": str(
                            lmstudio_root / "nomic-ai" / "nomic-embed-text-v1.5-GGUF" / "model.gguf"
                        ),
                    },
                ],
            }

            with mock.patch("model_dashboard.pages.inventory.LMSTUDIO_MODELS_ROOT", lmstudio_root):
                html = server._inventory(
                    inventory_result=result,
                    action_token="fixture-token",
                    enable_delete_actions=True,
                )

        self.assertIn("Nomic Embed Text", html)
        self.assertIn("Removal unavailable for this row", html)
        self.assertNotIn('action="/actions/delete-model"', html)

    def test_inventory_existing_lmstudio_folder_shows_remove_button(self):
        with tempfile.TemporaryDirectory() as tmp:
            lmstudio_root = Path(tmp) / "lmstudio"
            model_dir = lmstudio_root / "publisher" / "Model"
            model_dir.mkdir(parents=True)
            (model_dir / "model.gguf").write_text("weights", encoding="utf-8")
            result = {
                "checked_at": "2026-06-05T12:00:00-07:00",
                "checks": [],
                "models": [
                    {
                        "runtime": "LM Studio",
                        "model_id": "publisher/Model/model.gguf",
                        "display_name": "Model",
                        "status": "indexed",
                        "source_path": "publisher/Model/model.gguf",
                        "local_path": str(model_dir / "model.gguf"),
                    },
                ],
            }

            with mock.patch("model_dashboard.pages.inventory.LMSTUDIO_MODELS_ROOT", lmstudio_root):
                html = server._inventory(
                    inventory_result=result,
                    action_token="fixture-token",
                    enable_delete_actions=True,
                )

        self.assertIn("Model", html)
        self.assertIn('action="/actions/delete-model"', html)
        self.assertIn(">Remove</button>", html)

    def test_inventory_lmstudio_bundled_internal_model_is_not_removable(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lmstudio_root = tmp_path / "models"
            bundled_root = tmp_path / ".internal" / "bundled-models"
            bundled_file = (
                bundled_root
                / "nomic-ai"
                / "nomic-embed-text-v1.5-GGUF"
                / "nomic-embed-text-v1.5.Q4_K_M.gguf"
            )
            bundled_file.parent.mkdir(parents=True)
            bundled_file.write_text("weights", encoding="utf-8")
            source_path = (
                "nomic-ai/nomic-embed-text-v1.5-GGUF/"
                "nomic-embed-text-v1.5.Q4_K_M.gguf"
            )

            with mock.patch(
                "model_dashboard.pages.inventory.LMSTUDIO_BUNDLED_MODELS_ROOT",
                bundled_root,
            ):
                models = server._parse_lmstudio_inventory(
                    json.dumps(
                        {
                            "models": [
                                {
                                    "type": "embedding",
                                    "modelKey": "text-embedding-nomic-embed-text-v1.5",
                                    "displayName": "Nomic Embed Text v1.5",
                                    "publisher": "nomic-ai",
                                    "path": source_path,
                                }
                            ]
                        }
                    ),
                    root=lmstudio_root,
                )
                html = server._inventory(
                    inventory_result={
                        "checked_at": "2026-06-05T12:00:00-07:00",
                        "checks": [],
                        "models": models,
                    },
                    action_token="fixture-token",
                    enable_delete_actions=True,
                )

        self.assertEqual(models[0]["local_path"], str(bundled_file))
        self.assertIn("Bundled LM Studio internal model", models[0]["removal_blocked_reason"])
        self.assertIn(str(bundled_file), html)
        self.assertIn("Bundled LM Studio internal model", html)
        self.assertNotIn('action="/actions/delete-model"', html)

    def test_inventory_parses_lmstudio_models_and_loaded_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = server._parse_lmstudio_inventory(
                """
                {
                  "models": [
                    {
                      "modelKey": "qwen3-coder-30b-a3b-instruct-mlx",
                      "displayName": "Qwen3 Coder 30B",
                      "path": "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
                      "quantization": {"name": "4bit", "bits": 4}
                    },
                    {
                      "modelKey": "indexed-only-24b",
                      "displayName": "Indexed Only 24B",
                      "path": "example/Indexed-Only-24B"
                    }
                  ]
                }
                """,
                """
                {"loaded": [{"identifier": "qwen3-coder-30b-a3b-instruct-mlx"}]}
                """,
                root=tmp,
            )

        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["runtime"], "LM Studio")
        self.assertEqual(models[0]["model_id"], "qwen3-coder-30b-a3b-instruct-mlx")
        self.assertEqual(models[0]["status"], "loaded")
        self.assertEqual(
            models[0]["source_path"],
            "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
        )
        self.assertEqual(
            models[0]["local_path"],
            str(Path(tmp) / "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit"),
        )
        self.assertEqual(models[1]["model_id"], "indexed-only-24b")
        self.assertEqual(models[1]["status"], "indexed")
        self.assertNotIn("4bit", {row["model_id"] for row in models})

    def test_inventory_scans_lmstudio_filesystem_only_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            indexed = root / "publisher" / "Indexed-Model"
            filesystem_only = root / "publisher" / "Filesystem-Only-Model"
            ds_store_only = root / "publisher" / "DS-Store-Only"
            metadata_only = root / "publisher" / "Metadata-Only"
            hidden = root / ".hidden" / "Ignored"
            indexed.mkdir(parents=True)
            filesystem_only.mkdir(parents=True)
            ds_store_only.mkdir(parents=True)
            metadata_only.mkdir(parents=True)
            hidden.mkdir(parents=True)
            (indexed / "model.safetensors").write_text("indexed", encoding="utf-8")
            (filesystem_only / "model-00001-of-00004.safetensors").write_text(
                "weights",
                encoding="utf-8",
            )
            (ds_store_only / ".DS_Store").write_text("ignored", encoding="utf-8")
            (metadata_only / "config.json").write_text("{}", encoding="utf-8")

            models = server._scan_lmstudio_filesystem_models(
                root,
                indexed_paths=["publisher/Indexed-Model"],
            )

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["runtime"], "LM Studio")
        self.assertEqual(models[0]["model_id"], "publisher/Filesystem-Only-Model")
        self.assertEqual(models[0]["status"], "filesystem_only")
        self.assertEqual(models[0]["source_path"], "publisher/Filesystem-Only-Model")
        self.assertEqual(models[0]["local_path"], str(filesystem_only))

    def test_inventory_parsers_handle_malformed_or_crash_output(self):
        self.assertEqual(server._parse_lmstudio_inventory("not json"), [])
        self.assertEqual(
            server._parse_ollama_inventory("libc++abi: terminating due to uncaught exception"),
            [],
        )

    def test_inventory_parses_ollama_list_table(self):
        models = server._parse_ollama_inventory(
            "NAME                            ID              SIZE      MODIFIED\n"
            "qwen3:30b                       abc123          18 GB     2 days ago\n"
        )

        self.assertEqual(models[0]["runtime"], "Ollama")
        self.assertEqual(models[0]["model_id"], "qwen3:30b")
        self.assertTrue(models[0]["local_path"].endswith(".ollama/models/manifests/registry.ollama.ai/library/qwen3/30b"))

    def test_lab_dashboard_shows_abliterated_dolphin_lane(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            registry_path = tmp_path / "candidates.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(
                registry_path,
                extra_rows=[
                    {
                        "candidate_id": "20260605-qwen3-8b-abliterated-gguf",
                        "model_name": "Qwen3-8B-Abliterated-GGUF",
                        "model_family": "Qwen3 Abliterated",
                        "provider_or_org": "mlabonne / bartowski",
                        "status": "ready_for_eval",
                        "format_or_runtime": "GGUF through LM Studio or llama.cpp",
                        "source_packet_path": "automations/ai-lab-radar/inputs/abliterated.md",
                        "report_path": "automations/ai-lab-radar/reports/abliterated.md",
                        "benchmark_run_id": "",
                        "why_interesting": (
                            "Compact low-refusal candidate for local behavior testing."
                        ),
                        "risk_notes": (
                            "Experimental refusal behavior must be benchmarked before use."
                        ),
                        "proposed_eval": "Run local benchmark with refusal-boundary review notes.",
                        "security_review_status": "blocked",
                        "download_approval": "blocked",
                        "license_review_status": "needs_review",
                        "provenance_status": "source_metadata_only",
                        "security_notes": "Synthetic blocked specialty candidate.",
                        "isolation_notes": "Do not run.",
                        "security_review_path": "",
                    },
                    {
                        "candidate_id": "20260605-dolphin3-llama31-8b-gguf",
                        "model_name": "Dolphin3.0-Llama3.1-8B-GGUF",
                        "model_family": "Dolphin",
                        "provider_or_org": "Cognitive Computations",
                        "status": "ready_for_eval",
                        "format_or_runtime": "GGUF through LM Studio or llama.cpp",
                        "source_packet_path": "automations/ai-lab-radar/inputs/dolphin.md",
                        "report_path": "automations/ai-lab-radar/reports/dolphin.md",
                        "benchmark_run_id": "",
                        "why_interesting": "Local Dolphin baseline for agentic assistant testing.",
                        "risk_notes": "License and low-refusal behavior need review.",
                        "proposed_eval": "Run local benchmark and compare against Qwen r2.",
                        "security_review_status": "needs_review",
                        "download_approval": "not_approved",
                        "license_review_status": "needs_review",
                        "provenance_status": "source_metadata_only",
                        "security_notes": "Synthetic Dolphin candidate needs security review.",
                        "isolation_notes": "Use local runtime only after approval.",
                        "security_review_path": (
                            "automations/ai-lab-radar/security-reviews/dolphin3.md"
                        ),
                    },
                ],
            )

            with db.connect(db_path) as conn:
                html = server._lab(
                    conn,
                    registry_path=registry_path,
                    eval_results_dir=tmp_path / "eval_results",
                    project_registry_path=tmp_path / "missing-projects.csv",
                )
                specialty_html = server._specialty(conn, registry_path=registry_path)
                dolphin_html = server._specialty(
                    conn,
                    {"lane": ["Dolphin"]},
                    registry_path=registry_path,
                )
                security_html = server._specialty(
                    conn,
                    {"security": ["needs_review"]},
                    registry_path=registry_path,
                )

            self.assertIn("Abliterated / Dolphin Lane", html)
            self.assertIn("Qwen3-8B-Abliterated-GGUF", html)
            self.assertIn("Dolphin3.0-Llama3.1-8B-GGUF", html)
            self.assertIn("Abliterated", html)
            self.assertIn("Dolphin", html)
            self.assertIn("Specialty Models", specialty_html)
            self.assertIn("Qwen3-8B-Abliterated-GGUF", specialty_html)
            self.assertIn("Dolphin3.0-Llama3.1-8B-GGUF", specialty_html)
            self.assertNotIn("Ready Local 7B", specialty_html)
            self.assertIn("Specialty Candidates (1 of 2)", dolphin_html)
            self.assertIn("Dolphin3.0-Llama3.1-8B-GGUF", dolphin_html)
            self.assertNotIn("Qwen3-8B-Abliterated-GGUF", dolphin_html)
            self.assertIn("Security gate", specialty_html)
            self.assertIn("automations/ai-lab-radar/security-reviews/dolphin3.md", specialty_html)
            self.assertIn("Download", specialty_html)
            self.assertIn("blocked", specialty_html)
            self.assertIn("Specialty Candidates (1 of 2)", security_html)
            self.assertIn("Dolphin3.0-Llama3.1-8B-GGUF", security_html)
            self.assertNotIn("Qwen3-8B-Abliterated-GGUF", security_html)

    def test_projects_filters_project_registry_by_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "github_repos.csv"
            write_project_registry(registry_path)

            html = server._projects(
                {"category": ["local inference"]},
                registry_path=registry_path,
            )

            self.assertIn("Project Radar (1 of 2)", html)
            self.assertIn("Local Runtime", html)
            self.assertIn("P5", html)
            self.assertIn("Core local runtime for larger models.", html)
            self.assertIn("100k", html)
            self.assertNotIn("Agent Watch", html)

    def test_projects_sort_by_priority_before_stars(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "github_repos.csv"
            write_project_registry(registry_path)

            html = server._projects(registry_path=registry_path)

            self.assertLess(html.index("Local Runtime"), html.index("Agent Watch"))
            self.assertIn("Priority 5", html)

    def test_lab_dashboard_shows_github_project_radar(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            candidate_registry_path = tmp_path / "candidates.csv"
            project_registry_path = tmp_path / "github_repos.csv"
            db.init_db(db_path, reset=True)
            write_candidate_registry(candidate_registry_path)
            write_project_registry(project_registry_path)

            with db.connect(db_path) as conn:
                html = server._lab(
                    conn,
                    registry_path=candidate_registry_path,
                    eval_results_dir=tmp_path / "eval_results",
                    project_registry_path=project_registry_path,
                )

            self.assertIn("GitHub Project Radar", html)
            self.assertIn("Local Runtime", html)
            self.assertIn("Supports benchmark serving.", html)
            self.assertIn("/projects", html)


if __name__ == "__main__":
    unittest.main()
