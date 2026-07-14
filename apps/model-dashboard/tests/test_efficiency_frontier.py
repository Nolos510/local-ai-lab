import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import charts, db, server  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


class EfficiencyMathTests(unittest.TestCase):
    def test_efficiency_divides_throughput_by_peak_ram(self):
        self.assertEqual(2.5, charts.efficiency(50, 20))
        self.assertEqual(0.0, charts.efficiency(0, 20))

    def test_efficiency_is_none_safe_and_division_by_zero_safe(self):
        for throughput, ram in ((None, 20), (50, None), (50, 0), (50, "")):
            with self.subTest(throughput=throughput, ram=ram):
                self.assertIsNone(charts.efficiency(throughput, ram))


class ScatterChartTests(unittest.TestCase):
    def test_scatter_is_deterministic_bounded_and_escapes_labels(self):
        items = [
            ("Model <script>alert(1)</script>", 50, 80, 24),
            ("Second & Model", 25, 70, 12),
        ]

        first = charts.scatter(items, title="Efficiency frontier")
        second = charts.scatter(items, title="Efficiency frontier")

        self.assertEqual(first, second)
        self.assertEqual(2, first.count('class="chart-point"'))
        self.assertIn("Model &lt;script&gt;alert(1)&lt;/script&gt;", first)
        self.assertNotIn("<script>alert(1)</script>", first)
        circles = re.findall(
            r'<circle class="chart-point" cx="([^"]+)" cy="([^"]+)" r="([^"]+)"',
            first,
        )
        self.assertEqual(2, len(circles))
        for cx, cy, radius in circles:
            cx_value = float(cx)
            cy_value = float(cy)
            radius_value = float(radius)
            self.assertGreaterEqual(cx_value - radius_value, charts.SCATTER_PLOT_LEFT)
            self.assertLessEqual(cx_value + radius_value, charts.SCATTER_PLOT_RIGHT)
            self.assertGreaterEqual(cy_value - radius_value, charts.SCATTER_PLOT_TOP)
            self.assertLessEqual(cy_value + radius_value, charts.SCATTER_PLOT_BOTTOM)

    def test_scatter_empty_state_is_honest(self):
        html = charts.scatter([], empty_message="No confirmed frontier data yet")

        self.assertIn("No confirmed frontier data yet", html)
        self.assertNotIn('class="chart-point"', html)


class EfficiencyFrontierPageTests(unittest.TestCase):
    def _insert_score(self, conn, score_id, run_id, total_score, status):
        metric_columns = ", ".join(METRIC_FIELDS)
        metric_placeholders = ", ".join("?" for _ in METRIC_FIELDS)
        conn.execute(
            f"""
            INSERT INTO eval_scores (
                id, run_id, {metric_columns}, total_score, final_label, score_status
            )
            VALUES (?, ?, {metric_placeholders}, ?, ?, ?)
            """,
            (
                score_id,
                run_id,
                *([70] * len(METRIC_FIELDS)),
                total_score,
                "WATCHLIST",
                status,
            ),
        )

    def test_runs_page_uses_latest_confirmed_run_and_reports_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            eval_results = tmp_path / "eval_results"
            db.init_db(db_path, reset=True)

            with db.connect(db_path) as conn:
                conn.executemany(
                    """
                    INSERT INTO models (id, model_name, provider)
                    VALUES (?, ?, 'local')
                    """,
                    (
                        (1, "Frontier <script> Model"),
                        (2, "Draft Model"),
                        (3, "Unscored Model"),
                        (4, "Missing RAM Model"),
                    ),
                )
                conn.executemany(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec, ram_usage_gb
                    )
                    VALUES (?, ?, ?, 'local', ?, ?)
                    """,
                    (
                        (10, 1, "2026-07-10", 30, 15),
                        (11, 1, "2026-07-12", 50, 20),
                        (20, 2, "2026-07-12", 45, 18),
                        (30, 3, "2026-07-12", None, None),
                        (40, 4, "2026-07-12", 40, None),
                    ),
                )
                self._insert_score(conn, 100, 10, 72, "confirmed")
                self._insert_score(conn, 101, 11, 82, "confirmed")
                self._insert_score(conn, 102, 20, 74, "draft")
                self._insert_score(conn, 103, 40, 76, "confirmed")
                conn.commit()

                with mock.patch("subprocess.run") as run:
                    html = server._runs(conn, eval_results_dir=eval_results)

        run.assert_not_called()
        self.assertIn("Efficiency Frontier", html)
        self.assertEqual(1, html.count('class="chart-point"'))
        self.assertIn("2 runs without confirmed scores are excluded", html)
        self.assertIn(
            "1 latest confirmed run missing usable throughput or peak RAM is excluded",
            html,
        )
        self.assertIn("2.50", html)
        self.assertIn(">—</div></td>", html)
        self.assertIn("throughput per GB of peak RAM — higher earns its memory", html)
        self.assertNotIn("Frontier <script> Model", html)
        self.assertNotIn("<script src=", html)

    def test_runs_page_frontier_has_empty_state_without_confirmed_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, provider)
                    VALUES (1, 'Only Draft', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec, ram_usage_gb
                    ) VALUES (1, 1, '2026-07-12', 'local', 40, 20)
                    """
                )
                self._insert_score(conn, 1, 1, 70, "draft")
                conn.commit()

                html = server._runs(conn, eval_results_dir=tmp_path / "eval_results")

        self.assertIn("No latest confirmed runs with throughput and peak RAM yet", html)
        self.assertNotIn('class="chart-point"', html)


if __name__ == "__main__":
    unittest.main()
