import csv
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import components, db, server  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402

CURRENT_RUN_TIP = (
    "latest / registry-designated run for this model; older runs are kept for "
    "history and regression diffs"
)


class AuthoritativeRunSelectionTests(unittest.TestCase):
    def test_registry_designation_beats_more_recent_run(self):
        runs = [
            {
                "id": 11,
                "model_id": 1,
                "date_tested": "2026-07-15",
                "run_notes": "benchmark_run_id=newer-run | candidate_id=alpha",
            },
            {
                "id": 10,
                "model_id": 1,
                "date_tested": "2026-07-10",
                "run_notes": "benchmark_run_id=designated-run | candidate_id=alpha",
            },
        ]

        groups = components._authoritative_run_groups(
            runs,
            [{"candidate_id": "alpha", "benchmark_run_id": "designated-run"}],
        )

        self.assertEqual(10, groups[1]["authoritative_run_id"])
        self.assertEqual([11], [row["id"] for row in groups[1]["other_runs"]])

    def test_registry_designation_is_scoped_to_its_model(self):
        runs = [
            {
                "id": 10,
                "model_id": 1,
                "date_tested": "2026-07-10",
                "run_notes": "benchmark_run_id=shared-id | candidate_id=alpha",
            },
            {
                "id": 11,
                "model_id": 1,
                "date_tested": "2026-07-15",
                "run_notes": "benchmark_run_id=alpha-new | candidate_id=alpha",
            },
            {
                "id": 20,
                "model_id": 2,
                "date_tested": "2026-07-10",
                "run_notes": "benchmark_run_id=shared-id | candidate_id=beta",
            },
        ]

        groups = components._authoritative_run_groups(
            runs,
            [{"candidate_id": "beta", "benchmark_run_id": "shared-id"}],
        )

        self.assertEqual(11, groups[1]["authoritative_run_id"])
        self.assertEqual(20, groups[2]["authoritative_run_id"])

    def test_recency_uses_highest_id_to_break_date_tie(self):
        runs = [
            {"id": 20, "model_id": 1, "date_tested": "2026-07-15", "run_notes": ""},
            {"id": 22, "model_id": 1, "date_tested": "2026-07-15", "run_notes": ""},
            {"id": 21, "model_id": 1, "date_tested": "2026-07-14", "run_notes": ""},
        ]

        groups = components._authoritative_run_groups(runs, [])

        self.assertEqual(22, groups[1]["authoritative_run_id"])
        self.assertEqual([20, 21], [row["id"] for row in groups[1]["other_runs"]])

    def test_model_without_runs_has_no_authoritative_group(self):
        groups = components._authoritative_run_groups([], [{"benchmark_run_id": "missing"}])

        self.assertIsNone(groups.get(1))


class AuthoritativeRunPageTests(unittest.TestCase):
    def _write_registry(self, path, benchmark_run_id="designated-run"):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=("candidate_id", "model_name", "benchmark_run_id"),
            )
            writer.writeheader()
            writer.writerow(
                {
                    "candidate_id": "alpha-candidate",
                    "model_name": "Alpha Model",
                    "benchmark_run_id": benchmark_run_id,
                }
            )

    def _insert_score(
        self,
        conn,
        score_id,
        run_id,
        total_score,
        *,
        status="confirmed",
        label="WATCHLIST",
    ):
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
                label,
                status,
            ),
        )

    def _fixture(self, root):
        db_path = root / "dashboard.sqlite"
        registry_path = root / "candidates.csv"
        self._write_registry(registry_path)
        db.init_db(db_path, reset=True)
        conn = db.connect(db_path)
        conn.executemany(
            """
            INSERT INTO models (id, model_name, provider)
            VALUES (?, ?, 'local')
            """,
            ((1, "Alpha Model"), (2, "Beta Model")),
        )
        conn.executemany(
            """
            INSERT INTO model_runs (
                id, model_id, date_tested, backend, tokens_per_sec, ram_usage_gb, run_notes
            )
            VALUES (?, ?, ?, 'Local Runner', ?, 20, ?)
            """,
            (
                (10, 1, "2026-07-10", 12.0, "benchmark_run_id=designated-run"),
                (11, 1, "2026-07-15", 99.0, "benchmark_run_id=newer-run"),
                (12, 1, "2026-07-09", 8.0, "benchmark_run_id=oldest-run"),
                (20, 2, "2026-07-12", 2.0, "benchmark_run_id=beta-run"),
            ),
        )
        self._insert_score(conn, 100, 10, 70.0)
        self._insert_score(conn, 101, 11, 90.0)
        self._insert_score(conn, 102, 20, 60.0)
        conn.commit()
        return conn, registry_path

    def test_grouped_benchmark_marks_only_designated_run_and_keeps_history_reachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn, registry_path = self._fixture(root)
            try:
                with mock.patch("subprocess.run") as run:
                    html = server._runs(
                        conn,
                        registry_path=registry_path,
                        eval_results_dir=root / "eval-results",
                    )
            finally:
                conn.close()

        run.assert_not_called()
        table_rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
        current_rows = [row for row in table_rows if 'class="pill current-run"' in row]
        self.assertEqual(2, len(current_rows))
        alpha_current = next(row for row in current_rows if "Alpha Model" in row)
        self.assertIn("designated-run", alpha_current)
        self.assertNotIn("newer-run", alpha_current)
        self.assertIn('<details class="run-history">', html)
        self.assertIn("2 earlier runs", html)
        self.assertIn("newer-run", html)
        self.assertIn("oldest-run", html)
        self.assertEqual(2, html.count('class="pill current-run"'))
        self.assertIn(CURRENT_RUN_TIP, html)
        self.assertIn('href="/runs?group=off"', html)
        self.assertNotIn("<script src=", html)

    def test_ungrouped_view_keeps_u4_numeric_sort_and_sort_query_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn, registry_path = self._fixture(root)
            try:
                html = server._runs(
                    conn,
                    {
                        "group": ["off"],
                        "sort": ["tokens_per_sec"],
                        "dir": ["asc"],
                    },
                    registry_path=registry_path,
                    eval_results_dir=root / "eval-results",
                )
            finally:
                conn.close()

        table = html.split('<table class="runs-table"', 1)[1].split("</table>", 1)[0]
        self.assertLess(table.index("Beta Model"), table.index("oldest-run"))
        self.assertLess(table.index("oldest-run"), table.index("designated-run"))
        self.assertLess(table.index("designated-run"), table.index("newer-run"))
        self.assertIn(
            'href="/runs?group=off&amp;sort=tokens_per_sec&amp;dir=desc"',
            table,
        )
        self.assertIn('aria-sort="ascending"', table)

    def test_home_top_results_uses_registry_designated_score_and_throughput(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn, registry_path = self._fixture(root)
            try:
                html = server._overview(
                    conn,
                    registry_path=registry_path,
                    local_inventory_path=root / "missing-overlay.csv",
                    eval_results_dir=root / "eval-results",
                    hardware_profiles_dir=root / "hardware",
                    upstream_state_path=root / "upstream.json",
                    current_hardware_profile={"memory_gb": "256"},
                )
            finally:
                conn.close()

        table = html.split('<table class="overview-table"', 1)[1].split("</table>", 1)[0]
        alpha_row = next(
            row
            for row in re.findall(r"<tr>(.*?)</tr>", table, flags=re.DOTALL)
            if "Alpha Model" in row
        )
        self.assertIn("70.00", alpha_row)
        self.assertIn("12.0", alpha_row)
        self.assertNotIn("90.00", alpha_row)
        self.assertNotIn("99.0", alpha_row)

    def test_db_summaries_prefer_confirmed_score_but_keep_latest_run_performance(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO models (id, model_name, provider) VALUES (1, 'Alpha', 'local')"
                )
                conn.executemany(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, quantization,
                        tokens_per_sec, ram_usage_gb
                    )
                    VALUES (?, 1, ?, ?, ?, ?, ?)
                    """,
                    (
                        (9, "2026-07-12", "Intermediate Runner", "Q5", 50.0, 35.0),
                        (10, "2026-07-10", "Older Runner", "Q4", 20.0, 30.0),
                        (11, "2026-07-15", "Current Runner", "Q8", 75.4, 40.0),
                    ),
                )
                self._insert_score(conn, 99, 9, 72.5, status="confirmed")
                self._insert_score(
                    conn,
                    100,
                    10,
                    73.64,
                    status="confirmed",
                    label="CODING_SPECIALIST",
                )
                self._insert_score(
                    conn,
                    101,
                    11,
                    85.66,
                    status="draft",
                    label="DAILY_DRIVER",
                )
                summary = dict(db.list_model_summaries(conn)[0])

        self.assertEqual(73.64, summary["total_score"])
        self.assertEqual("confirmed", summary["score_status"])
        self.assertEqual("CODING_SPECIALIST", summary["final_label"])
        self.assertEqual(75.4, summary["tokens_per_sec"])
        self.assertEqual(40.0, summary["ram_usage_gb"])
        self.assertEqual("Current Runner", summary["backend"])
        self.assertEqual("Q8", summary["quantization"])

    def test_top_results_keep_confirmed_above_drafts_and_label_draft_only_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.executemany(
                    "INSERT INTO models (id, model_name, provider) VALUES (?, ?, 'local')",
                    (
                        (1, "Older Confirmed"),
                        (2, "Draft Only"),
                        (3, "Higher Confirmed"),
                    ),
                )
                conn.executemany(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec, ram_usage_gb,
                        run_notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (10, 1, "2026-07-10", "Older Runner", 20.0, 30.0, ""),
                        (
                            11,
                            1,
                            "2026-07-15",
                            "Current Runner",
                            75.4,
                            40.0,
                            "benchmark_run_id=current-confirmed-model",
                        ),
                        (20, 2, "2026-07-15", "Draft Runner", 90.0, 50.0, ""),
                        (30, 3, "2026-07-15", "Confirmed Runner", 60.0, 35.0, ""),
                    ),
                )
                self._insert_score(
                    conn,
                    100,
                    10,
                    73.64,
                    status="confirmed",
                    label="CODING_SPECIALIST",
                )
                self._insert_score(
                    conn,
                    101,
                    11,
                    85.66,
                    status="draft",
                    label="DAILY_DRIVER",
                )
                self._insert_score(
                    conn,
                    102,
                    20,
                    99.0,
                    status="draft",
                    label="DAILY_DRIVER",
                )
                self._insert_score(
                    conn,
                    103,
                    30,
                    80.0,
                    status="confirmed",
                    label="DAILY_DRIVER",
                )
                conn.commit()

                html = server._overview(
                    conn,
                    registry_path=root / "missing-candidates.csv",
                    local_inventory_path=root / "missing-inventory.csv",
                    eval_results_dir=root / "eval-results",
                    hardware_profiles_dir=root / "hardware",
                )

        table = html.split('<table class="overview-table"', 1)[1].split("</table>", 1)[0]
        rows = [
            row
            for row in re.findall(r"<tr>(.*?)</tr>", table, flags=re.DOTALL)
            if "href=\"/models/" in row
        ]
        model_names = ("Higher Confirmed", "Older Confirmed", "Draft Only")
        self.assertEqual(
            list(model_names),
            [next(name for name in model_names if name in row) for row in rows],
        )
        older_confirmed_row = next(row for row in rows if "Older Confirmed" in row)
        draft_only_row = next(row for row in rows if "Draft Only" in row)
        self.assertIn("73.64", older_confirmed_row)
        self.assertIn("75.4", older_confirmed_row)
        self.assertIn(">CONFIRMED</span>", older_confirmed_row)
        self.assertNotIn("85.66", older_confirmed_row)
        self.assertIn("99.00", draft_only_row)
        self.assertIn(">DRAFT</span>", draft_only_row)


if __name__ == "__main__":
    unittest.main()
