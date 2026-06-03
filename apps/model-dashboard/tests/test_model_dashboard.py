import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import csv_io, db, reports, server  # noqa: E402


FIXTURE_DIR = APP_DIR / "fixtures"


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
                            final_label
                        )
                        VALUES (
                            1, 1, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
                            'NOT_A_LABEL'
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


if __name__ == "__main__":
    unittest.main()
