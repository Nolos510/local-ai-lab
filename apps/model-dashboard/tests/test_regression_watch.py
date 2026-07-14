import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import charts, db, server  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


class SparklineTests(unittest.TestCase):
    def test_sparkline_is_deterministic_escapes_labels_and_labels_values(self):
        items = [
            ("2026-07-10", 20),
            ("2026-07-11 <retest>", 25.5),
            ("2026-07-12", 22),
        ]

        first = charts.sparkline(items, title="Tokens / sec", value_format="{:.1f}")
        second = charts.sparkline(items, title="Tokens / sec", value_format="{:.1f}")

        self.assertEqual(first, second)
        self.assertEqual(3, first.count('class="chart-spark-point"'))
        self.assertIn("2026-07-11 &lt;retest&gt;", first)
        self.assertNotIn("2026-07-11 <retest>", first)
        self.assertIn(">20.0</text>", first)
        self.assertIn(">25.5</text>", first)
        self.assertIn(">22.0</text>", first)
        self.assertNotIn("NaN", first)
        self.assertNotIn("inf", first)


class RegressionWatchPageTests(unittest.TestCase):
    def _insert_score(self, conn, score_id, run_id, total_score, status):
        metric_columns = ", ".join(METRIC_FIELDS)
        metric_values = ", ".join("70" for _ in METRIC_FIELDS)
        conn.execute(
            f"""
            INSERT INTO eval_scores (
                id, run_id, {metric_columns}, total_score, final_label, score_status
            ) VALUES (?, ?, {metric_values}, ?, 'WATCHLIST', ?)
            """,
            (score_id, run_id, total_score, status),
        )

    def test_multiple_runs_render_four_chronological_metric_sparklines(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, provider)
                    VALUES (1, 'Regression Model', 'local')
                    """
                )
                conn.executemany(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec,
                        total_latency_seconds, ram_usage_gb
                    ) VALUES (?, 1, ?, 'local', ?, ?, ?)
                    """,
                    (
                        (30, "2026-07-14", 30, 90, 38),
                        (10, "2026-07-10", 20, 120, 40),
                        (20, "2026-07-12", 25, 100, 39),
                    ),
                )
                self._insert_score(conn, 100, 10, 70, "confirmed")
                self._insert_score(conn, 200, 20, 99, "draft")
                self._insert_score(conn, 300, 30, 80, "confirmed")
                conn.commit()

                with mock.patch("subprocess.run") as run:
                    html = server._model_detail(conn, 1)

        run.assert_not_called()
        self.assertEqual(4, html.count('class="chart chart-sparkline"'))
        self.assertEqual(11, html.count('class="chart-spark-point"'))
        score_chart = html.split('aria-label="Confirmed total score"', 1)[1].split(
            "</svg>", 1
        )[0]
        self.assertEqual(2, score_chart.count('class="chart-spark-point"'))
        self.assertIn(">—</text>", score_chart)
        self.assertLess(score_chart.index("2026-07-10"), score_chart.index("2026-07-12"))
        self.assertLess(score_chart.index("2026-07-12"), score_chart.index("2026-07-14"))

    def test_single_run_model_shows_honest_no_comparison_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, provider)
                    VALUES (1, 'Single Run Model', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec,
                        total_latency_seconds, ram_usage_gb
                    ) VALUES (1, 1, '2026-07-14', 'local', 20, 120, 40)
                    """
                )
                conn.commit()

                with mock.patch("subprocess.run") as run:
                    html = server._model_detail(conn, 1)

        run.assert_not_called()
        self.assertIn("Performance over time", html)
        self.assertIn("one run — nothing to compare yet", html)
        self.assertNotIn('class="chart-spark-point"', html)
        self.assertNotIn("<script src=", html)


if __name__ == "__main__":
    unittest.main()
