import tempfile
import unittest
from pathlib import Path

import sys

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


if __name__ == "__main__":
    unittest.main()
