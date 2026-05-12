import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model_dashboard import csv_io, db


class CsvImportTests(unittest.TestCase):
    def test_fixture_import_loads_linked_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "dashboard.sqlite"
            fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
            counts = csv_io.import_fixture_set(db_path, fixture_dir)

            self.assertEqual(counts["models"], 4)
            self.assertEqual(counts["model_runs"], 4)
            self.assertEqual(counts["eval_scores"], 4)
            self.assertEqual(counts["decisions"], 4)

            with db.connect(db_path) as conn:
                linked = conn.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM eval_scores s
                    JOIN model_runs r ON r.id = s.run_id
                    JOIN models m ON m.id = r.model_id
                    """
                ).fetchone()["count"]
                self.assertEqual(linked, 4)


if __name__ == "__main__":
    unittest.main()
