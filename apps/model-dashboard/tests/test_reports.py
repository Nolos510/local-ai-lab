import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model_dashboard import csv_io, reports


class ReportTests(unittest.TestCase):
    def test_report_generation_hides_fixture_summary_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            report_path = tmp_path / "report.md"
            fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"

            csv_io.import_fixture_set(db_path, fixture_dir)
            reports.write_report(db_path, report_path)

            text = report_path.read_text(encoding="utf-8")
            self.assertIn("# Local Model Performance Report", text)
            self.assertIn("Models tracked: 0", text)
            self.assertIn("Demo fixture models hidden: 4", text)
            self.assertIn("| Model | Backend | Quant | Score | Status | Label | Decision | Best use case |", text)
            self.assertIn("No real benchmark imports yet.", text)
            self.assertNotIn("Qwen2.5-Coder 14B Instruct", text)

    def test_report_generation_can_include_demo_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            report_path = tmp_path / "report.md"
            fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"

            csv_io.import_fixture_set(db_path, fixture_dir)
            reports.write_report(db_path, report_path, include_demo=True)

            text = report_path.read_text(encoding="utf-8")
            self.assertIn("Models tracked: 4", text)
            self.assertIn("Demo fixture models hidden: 0", text)
            self.assertIn("Qwen2.5-Coder 14B Instruct", text)


if __name__ == "__main__":
    unittest.main()
