import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model_dashboard import db


class SchemaTests(unittest.TestCase):
    def test_schema_creation_creates_expected_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "dashboard.sqlite"
            db.init_db(db_path)
            with db.connect(db_path) as conn:
                tables = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                self.assertTrue(set(db.TABLES).issubset(tables))
                self.assertEqual(db.table_count(conn, "models"), 0)

    def test_schema_adds_model_run_perf_columns_idempotently(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "dashboard.sqlite"
            db.init_db(db_path)
            with db.connect(db_path) as conn:
                db.create_schema(conn)
                db.create_schema(conn)
                columns = {
                    row["name"]
                    for row in conn.execute("PRAGMA table_info(model_runs)").fetchall()
                }

            self.assertIn("ttft_seconds", columns)
            self.assertIn("total_latency_seconds", columns)

    def test_schema_migrates_existing_model_runs_table_with_perf_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "dashboard.sqlite"
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE model_runs (
                        id INTEGER PRIMARY KEY,
                        model_id INTEGER NOT NULL,
                        date_tested TEXT NOT NULL,
                        backend TEXT NOT NULL
                    )
                    """
                )
                db.create_schema(conn)
                columns = {
                    row["name"]
                    for row in conn.execute("PRAGMA table_info(model_runs)").fetchall()
                }

            self.assertIn("ttft_seconds", columns)
            self.assertIn("total_latency_seconds", columns)


if __name__ == "__main__":
    unittest.main()
