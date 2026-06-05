import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


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
    "why_interesting",
    "risk_notes",
    "proposed_eval",
]
PROJECT_FIELDS = [
    "repo_id",
    "repo_name",
    "owner",
    "repo_url",
    "category",
    "status",
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
            "why_interesting": "Already installed for a local retest.",
            "risk_notes": "Needs scored evidence.",
            "proposed_eval": "Run the local benchmark prompt set.",
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
            "why_interesting": "Interesting but not ready.",
            "risk_notes": "Runtime unknown.",
            "proposed_eval": "Confirm local artifact first.",
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

    def test_markdown_report_uses_fixture_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            report = reports.generate_markdown_report(db_path)

            self.assertIn("Models tracked: 4", report)
            self.assertIn("ResearchLite Local 7B", report)
            self.assertIn("TinyCoder Local 1.1B", report)
            self.assertIn("Qwen2.5-Coder 14B Instruct", report)

    def test_overview_filters_by_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            with db.connect(db_path) as conn:
                html = server._overview(conn, {"label": ["RESEARCH_SPECIALIST"]})

            self.assertIn("Ranked Local Models (1 of 4)", html)
            self.assertIn("CONFIRMED", html)
            self.assertIn("ResearchLite Local 7B", html)
            self.assertNotIn("TinyCoder Local 1.1B</a>", html)
            self.assertNotIn("Qwen2.5-Coder 14B Instruct</a>", html)

    def test_overview_filters_by_search_and_install_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            csv_io.import_fixture_set(db_path, FIXTURE_DIR)

            with db.connect(db_path) as conn:
                html = server._overview(conn, {"q": ["coding"], "keep": ["yes"]})

            self.assertIn("Ranked Local Models (2 of 4)", html)
            self.assertIn("TinyCoder Local 1.1B", html)
            self.assertIn("Qwen2.5-Coder 14B Instruct", html)
            self.assertNotIn("ResearchLite Local 7B</a>", html)

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
                    """
                    INSERT INTO eval_scores (
                        id,
                        run_id,
                        {fields},
                        total_score,
                        final_label,
                        score_status
                    )
                    VALUES (5, 77, {values}, 80, 'DAILY_DRIVER', 'confirmed')
                    """.format(fields=score_fields, values=score_placeholders)
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
            (artifact_dir / "dashboard-import").mkdir()

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
                        "why_interesting": "Compact low-refusal candidate for local behavior testing.",
                        "risk_notes": "Experimental refusal behavior must be benchmarked before use.",
                        "proposed_eval": "Run local benchmark with refusal-boundary review notes.",
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

            self.assertIn("Abliterated / Dolphin Lane", html)
            self.assertIn("Qwen3-8B-Abliterated-GGUF", html)
            self.assertIn("Dolphin3.0-Llama3.1-8B-GGUF", html)
            self.assertIn("Abliterated", html)
            self.assertIn("Dolphin", html)

    def test_projects_filters_project_registry_by_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "github_repos.csv"
            write_project_registry(registry_path)

            html = server._projects(
                {"category": ["local inference"]},
                registry_path=registry_path,
            )

            self.assertIn("GitHub Project Radar (1 of 2)", html)
            self.assertIn("Local Runtime", html)
            self.assertIn("100k", html)
            self.assertNotIn("Agent Watch", html)

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
