import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, recommend, server  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


def score_row(model_id, model_name, *, status="confirmed", **scores):
    row = {
        "model_id": model_id,
        "model_name": model_name,
        "score_status": status,
    }
    row.update(scores)
    return row


def complete_score_row(model_id, model_name, value, *, status="confirmed", **scores):
    values = {field: value for field in METRIC_FIELDS}
    values.update(scores)
    return score_row(model_id, model_name, status=status, **values)


class TaskRecommenderTests(unittest.TestCase):
    def test_zero_confirmed_models_has_no_recommendations(self):
        summary = recommend.task_recommendations(
            [complete_score_row(1, "Draft Only", 99, status="draft")]
        )

        self.assertEqual(summary.scored_model_count, 0)
        self.assertEqual(summary.tasks, ())

    def test_one_confirmed_model_leads_every_scored_task(self):
        summary = recommend.task_recommendations(
            [complete_score_row(1, "Only Model", 70)]
        )

        self.assertEqual(summary.scored_model_count, 1)
        self.assertEqual(
            [task.task for task in summary.tasks],
            [
                "Coding",
                "Reasoning & agents",
                "Research & writing",
                "Long context",
                "Fast & practical",
            ],
        )
        for task in summary.tasks:
            self.assertEqual(task.score, 70.0)
            self.assertEqual([leader.model_name for leader in task.leaders], ["Only Model"])

    def test_n_models_use_task_dimensions_and_ignore_drafts(self):
        summary = recommend.task_recommendations(
            [
                complete_score_row(
                    1,
                    "Code Model",
                    40,
                    instruction_following=90,
                    coding_debugging=100,
                ),
                complete_score_row(
                    2,
                    "Reasoning Model",
                    50,
                    reasoning=96,
                    agent_planning=94,
                ),
                complete_score_row(
                    3,
                    "Draft Superstar",
                    100,
                    status="draft",
                ),
            ]
        )

        self.assertEqual(summary.scored_model_count, 2)
        leaders_by_task = {
            task.task: (task.score, [leader.model_name for leader in task.leaders])
            for task in summary.tasks
        }
        self.assertEqual(leaders_by_task["Coding"], (95.0, ["Code Model"]))
        self.assertEqual(
            leaders_by_task["Reasoning & agents"],
            (95.0, ["Reasoning Model"]),
        )
        self.assertNotIn(
            "Draft Superstar",
            [leader for _, leaders in leaders_by_task.values() for leader in leaders],
        )

    def test_ties_keep_all_co_leaders_in_deterministic_order(self):
        summary = recommend.task_recommendations(
            [
                complete_score_row(2, "Zulu", 80),
                complete_score_row(1, "Alpha", 80),
                complete_score_row(3, "Lower", 60),
            ]
        )

        self.assertEqual(summary.scored_model_count, 3)
        for task in summary.tasks:
            self.assertEqual(task.score, 80.0)
            self.assertEqual(
                [(leader.model_id, leader.model_name) for leader in task.leaders],
                [(1, "Alpha"), (2, "Zulu")],
            )

    def test_tasks_without_complete_confirmed_dimensions_are_hidden(self):
        summary = recommend.task_recommendations(
            [
                score_row(
                    1,
                    "Coding Only",
                    instruction_following=80,
                    coding_debugging=90,
                )
            ]
        )

        self.assertEqual(summary.scored_model_count, 1)
        self.assertEqual([task.task for task in summary.tasks], ["Coding"])


class TaskRecommenderRenderingTests(unittest.TestCase):
    def test_home_and_benchmark_render_confirmed_leaders_without_subprocesses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            db.init_db(database_path, reset=True)

            with db.connect(database_path) as conn:
                conn.executemany(
                    "INSERT INTO models (id, model_name, provider) VALUES (?, ?, ?)",
                    (
                        (1, "Confirmed Leader", "local"),
                        (2, "Draft Pretender", "local"),
                    ),
                )
                conn.executemany(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        (1, 1, "2026-07-14", "local"),
                        (2, 2, "2026-07-14", "local"),
                    ),
                )
                columns = ", ".join(METRIC_FIELDS)
                placeholders = ", ".join("?" for _ in METRIC_FIELDS)
                conn.executemany(
                    f"""
                    INSERT INTO eval_scores (
                        id, run_id, {columns}, total_score, final_label, score_status
                    )
                    VALUES (?, ?, {placeholders}, ?, ?, ?)
                    """,
                    (
                        (1, 1, *([70] * len(METRIC_FIELDS)), 70, "WATCHLIST", "confirmed"),
                        (2, 2, *([100] * len(METRIC_FIELDS)), 100, "DAILY_DRIVER", "draft"),
                    ),
                )
                conn.commit()

                with mock.patch("subprocess.run") as run:
                    home_html = server._overview(
                        conn,
                        registry_path=root / "candidates.csv",
                        local_inventory_path=root / "inventory.csv",
                        eval_results_dir=root / "eval-results",
                        hardware_profiles_dir=root / "hardware",
                    )
                    benchmark_html = server._runs(
                        conn,
                        database_path=database_path,
                        eval_results_dir=root / "eval-results",
                    )

                run.assert_not_called()

        for html in (home_html, benchmark_html):
            self.assertIn("Best for...", html)
            self.assertIn("only 1 model scored - benchmark more to compare", html)
            self.assertIn('href="/models/1"', html)
            self.assertIn("Confirmed Leader", html)
            self.assertIn('class="metric-tip"', html)

            leaders_region = html.split('class="task-leaders', 1)[1].split("</section>", 1)[0]
            self.assertNotIn("Draft Pretender", leaders_region)

        self.assertLess(
            benchmark_html.index('class="task-leaders'),
            benchmark_html.index("<h2>Model Runs"),
        )

    def test_panels_are_hidden_when_no_confirmed_task_scores_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            db.init_db(database_path, reset=True)

            with db.connect(database_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, provider)
                    VALUES (1, 'Draft Only', 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (id, model_id, date_tested, backend)
                    VALUES (1, 1, '2026-07-14', 'local')
                    """
                )
                columns = ", ".join(METRIC_FIELDS)
                placeholders = ", ".join("?" for _ in METRIC_FIELDS)
                conn.execute(
                    f"""
                    INSERT INTO eval_scores (
                        id, run_id, {columns}, total_score, final_label, score_status
                    )
                    VALUES (?, ?, {placeholders}, ?, ?, ?)
                    """,
                    (1, 1, *([90] * len(METRIC_FIELDS)), 90, "DAILY_DRIVER", "draft"),
                )
                conn.commit()

                with mock.patch("subprocess.run") as run:
                    home_html = server._overview(
                        conn,
                        registry_path=root / "candidates.csv",
                        local_inventory_path=root / "inventory.csv",
                        eval_results_dir=root / "eval-results",
                        hardware_profiles_dir=root / "hardware",
                    )
                    benchmark_html = server._runs(
                        conn,
                        database_path=database_path,
                        eval_results_dir=root / "eval-results",
                    )

                run.assert_not_called()

        self.assertNotIn('class="task-leaders', home_html)
        self.assertNotIn('class="task-leaders', benchmark_html)


if __name__ == "__main__":
    unittest.main()
