import csv
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402
from model_dashboard.pagination import (  # noqa: E402
    MAX_PAGE_SIZE,
    _paginate,
    _pagination_controls,
)
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


class PaginationHelperTests(unittest.TestCase):
    def test_slices_and_clamps_out_of_range_pages(self):
        second = _paginate(list(range(7)), {"page": ["2"], "page_size": ["3"]})
        clamped = _paginate(list(range(7)), {"page": ["99"], "page_size": ["3"]})
        capped = _paginate(list(range(101)), {"page_size": ["999"]})

        self.assertEqual((3, 4, 5), second.items)
        self.assertEqual((4, 6, 7), (second.first_item, second.last_item, second.total_items))
        self.assertEqual(3, clamped.number)
        self.assertEqual((6,), clamped.items)
        self.assertEqual(MAX_PAGE_SIZE, capped.page_size)

    def test_controls_preserve_sort_direction_and_active_filters(self):
        query = {
            "group": ["off"],
            "backend": ["Local Runner"],
            "label": ["WATCHLIST"],
            "status": ["confirmed"],
            "sort": ["tokens_per_sec"],
            "dir": ["desc"],
            "page": ["2"],
            "page_size": ["2"],
        }
        page = _paginate(list(range(5)), query)

        html = _pagination_controls("/runs", query, page, label="Runs")

        preserved = (
            "group=off&amp;backend=Local+Runner&amp;label=WATCHLIST&amp;"
            "status=confirmed&amp;sort=tokens_per_sec&amp;dir=desc"
        )
        self.assertIn(f'href="/runs?{preserved}&amp;page=1&amp;page_size=2"', html)
        self.assertIn(f'href="/runs?{preserved}&amp;page=3&amp;page_size=2"', html)
        self.assertIn("showing 3-4 of 5", html)


class DashboardPaginationTests(unittest.TestCase):
    def _runs_fixture(self, root):
        database_path = root / "dashboard.sqlite"
        db.init_db(database_path, reset=True)
        conn = db.connect(database_path)
        names_and_rates = (
            (1, "Rate 50", 50.0),
            (2, "Rate 10", 10.0),
            (3, "Rate 30", 30.0),
            (4, "Rate 20", 20.0),
            (5, "Rate 40", 40.0),
        )
        conn.executemany(
            "INSERT INTO models (id, model_name, provider) VALUES (?, ?, 'local')",
            [(model_id, name) for model_id, name, _ in names_and_rates],
        )
        conn.executemany(
            """
            INSERT INTO model_runs (
                id, model_id, date_tested, backend, tokens_per_sec, run_notes
            )
            VALUES (?, ?, '2026-07-20', 'Local Runner', ?, ?)
            """,
            [
                (model_id, model_id, rate, f"benchmark_run_id=rate-{int(rate)}")
                for model_id, _, rate in names_and_rates
            ],
        )
        metric_columns = ", ".join(METRIC_FIELDS)
        metric_placeholders = ", ".join("?" for _ in METRIC_FIELDS)
        conn.executemany(
            f"""
            INSERT INTO eval_scores (
                id, run_id, {metric_columns}, total_score, final_label, score_status
            )
            VALUES (?, ?, {metric_placeholders}, 70, 'WATCHLIST', 'confirmed')
            """,
            [
                (model_id, model_id, *([70] * len(METRIC_FIELDS)))
                for model_id, _, _ in names_and_rates
            ],
        )
        conn.commit()
        return conn

    def _write_radar_fixture(self, path):
        fieldnames = (
            "candidate_id",
            "model_name",
            "model_family",
            "provider_or_org",
            "status",
            "format_or_runtime",
            "why_interesting",
            "risk_notes",
            "proposed_eval",
        )
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for letter in "GFEDCBA":
                writer.writerow(
                    {
                        "candidate_id": f"candidate-{letter.lower()}",
                        "model_name": f"Candidate {letter}",
                        "model_family": "Fixture",
                        "provider_or_org": "local",
                        "status": "ready_for_eval",
                        "format_or_runtime": "GGUF",
                        "why_interesting": "Local pagination fixture.",
                        "risk_notes": "Fixture only.",
                        "proposed_eval": "Review locally.",
                    }
                )

    def test_flat_runs_sort_before_slicing_and_clamp_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = self._runs_fixture(root)
            try:
                query = {
                    "group": ["off"],
                    "backend": ["Local Runner"],
                    "label": ["WATCHLIST"],
                    "status": ["confirmed"],
                    "sort": ["tokens_per_sec"],
                    "dir": ["asc"],
                    "page": ["2"],
                    "page_size": ["2"],
                }
                html = server._runs(
                    conn,
                    query,
                    registry_path=root / "missing-candidates.csv",
                    eval_results_dir=root / "missing-eval-results",
                )
                clamped_html = server._runs(
                    conn,
                    {**query, "page": ["99"]},
                    registry_path=root / "missing-candidates.csv",
                    eval_results_dir=root / "missing-eval-results",
                )
            finally:
                conn.close()

        table = html.split('<table class="runs-table"', 1)[1].split("</table>", 1)[0]
        self.assertIn("Rate 30", table)
        self.assertIn("Rate 40", table)
        self.assertNotIn("Rate 10", table)
        self.assertLess(table.index("Rate 30"), table.index("Rate 40"))
        self.assertIn("showing 3-4 of 5", html)
        self.assertIn("Rate 50", clamped_html.split("Compare Models", 1)[0])
        self.assertIn("showing 5-5 of 5", clamped_html)

    def test_radar_uses_shared_pagination_and_preserves_query_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            registry_path = root / "candidates.csv"
            db.init_db(database_path, reset=True)
            self._write_radar_fixture(registry_path)
            query = {
                "status": ["ready_for_eval"],
                "sort": ["candidate"],
                "dir": ["asc"],
                "page": ["2"],
                "page_size": ["2"],
            }
            with db.connect(database_path) as conn, mock.patch("subprocess.run") as run:
                html = server._radar(
                    conn,
                    query,
                    registry_path=registry_path,
                    project_registry_path=root / "missing-projects.csv",
                    upstream_state_path=root / "missing-upstream.json",
                )

        run.assert_not_called()
        table = html.split('<table class="radar-table"', 1)[1].split("</table>", 1)[0]
        self.assertIn("Candidate C", table)
        self.assertIn("Candidate D", table)
        self.assertNotIn("Candidate B", table)
        self.assertLess(table.index("Candidate C"), table.index("Candidate D"))
        self.assertIn("showing 3-4 of 7", html)
        self.assertIn(
            'href="/radar?status=ready_for_eval&amp;sort=candidate&amp;dir=asc&amp;page=3&amp;page_size=2"',
            html,
        )
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link", html)

    def test_grouped_runs_render_never_spawns_subprocesses_or_external_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = self._runs_fixture(root)
            try:
                with mock.patch("subprocess.run") as run:
                    html = server._runs(
                        conn,
                        registry_path=root / "missing-candidates.csv",
                        eval_results_dir=root / "missing-eval-results",
                    )
            finally:
                conn.close()

        run.assert_not_called()
        current_rows = re.findall(
            r'<span class="pill current-run">current</span>',
            html,
        )
        self.assertEqual(5, len(current_rows))
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link", html)


if __name__ == "__main__":
    unittest.main()
