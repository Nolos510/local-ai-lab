import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model_dashboard import scoring


class ScoringTests(unittest.TestCase):
    def test_total_score_is_metric_average(self):
        values = {field: 80 for field in scoring.METRIC_FIELDS}
        self.assertEqual(scoring.calculate_total_score(values), 80.0)

    def test_suggests_coding_specialist_from_strong_coding_metric(self):
        values = {field: 70 for field in scoring.METRIC_FIELDS}
        values["coding_debugging"] = 95
        self.assertEqual(scoring.suggest_final_label(values), "CODING_SPECIALIST")

    def test_rejects_unknown_label(self):
        with self.assertRaises(ValueError):
            scoring.validate_final_label("HYPE_ONLY")


if __name__ == "__main__":
    unittest.main()
