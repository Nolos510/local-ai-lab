import csv
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402
from model_dashboard.pages import actions  # noqa: E402
from model_dashboard.pages.inventory import CANDIDATE_FIELDNAMES  # noqa: E402

FIXED_NOW = datetime(2026, 7, 17, 14, 23, 45)


def fixed_clock():
    return FIXED_NOW


def candidate(candidate_id, model_name, model_id, runner="lmstudio-cli"):
    row = {field: "" for field in CANDIDATE_FIELDNAMES}
    row.update(
        {
            "candidate_id": candidate_id,
            "model_name": model_name,
            "status": "ready_for_eval",
            "local_model_id": model_id,
            "local_runner": runner,
        }
    )
    return row


def write_candidates(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def inventory_model(model_name, model_id):
    return {
        "runtime": "LM Studio",
        "model_id": model_id,
        "display_name": model_name,
        "status": "loaded",
    }


def insert_dashboard_run(database_path, run_id):
    db.init_db(database_path, reset=True)
    with db.connect(database_path) as conn:
        conn.execute(
            "INSERT INTO models (id, model_name, provider) VALUES (1, 'Repeated Model', 'local')"
        )
        conn.execute(
            """
            INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes)
            VALUES (1, 1, '2026-07-17', 'LM Studio CLI', ?)
            """,
            (f"benchmark_run_id={run_id} | dashboard_run_button=yes",),
        )
        conn.commit()


class FreshRunIdHelperTests(unittest.TestCase):
    def test_novel_id_is_unchanged(self):
        self.assertEqual(
            server._mint_dashboard_run_id("novel-run", {"another-run"}, clock=fixed_clock),
            "novel-run",
        )

    def test_reused_id_gets_fixed_clock_suffix_and_next_free_increment(self):
        base = "20260717-repeated-model-dashboard-test"
        existing = {
            base,
            f"{base}-142345",
            f"{base}-142345-2",
        }

        self.assertEqual(
            server._mint_dashboard_run_id(base, existing, clock=fixed_clock),
            f"{base}-142345-3",
        )


class FreshRunPlanningTests(unittest.TestCase):
    def test_single_run_uses_db_and_artifact_ids_without_touching_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "candidates.csv"
            database_path = tmp_path / "dashboard.sqlite"
            eval_results_dir = tmp_path / "eval_results"
            base = "20260717-repeated-model-dashboard-test"
            existing_dir = eval_results_dir / f"{base}-142345"
            existing_dir.mkdir(parents=True)
            marker = existing_dir / "keep.txt"
            marker.write_text("original artifact", encoding="utf-8")
            write_candidates(
                registry_path,
                [candidate("candidate-one", "Repeated Model", "publisher/repeated-one")],
            )
            insert_dashboard_run(database_path, base)

            class FakeThread:
                def __init__(self, *, name, **kwargs):
                    self.name = name

                def start(self):
                    return None

            with mock.patch.object(actions.threading, "Thread", FakeThread):
                result = actions._start_candidate_test(
                    "candidate-one",
                    registry_path,
                    eval_results_dir,
                    5,
                    database_path,
                    clock=fixed_clock,
                )

            self.assertEqual(result["run_id"], f"{base}-142345-2")
            self.assertEqual(marker.read_text(encoding="utf-8"), "original artifact")
            self.assertFalse((eval_results_dir / result["run_id"]).exists())

    def test_preflight_renders_final_minted_id_and_dispatches_that_exact_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "candidates.csv"
            database_path = tmp_path / "dashboard.sqlite"
            eval_results_dir = tmp_path / "eval_results"
            base = "20260717-repeated-model-dashboard-test"
            (eval_results_dir / base).mkdir(parents=True)
            write_candidates(
                registry_path,
                [candidate("candidate-one", "Repeated Model", "publisher/repeated-one")],
            )
            db.init_db(database_path, reset=True)
            inventory = {
                "models": [inventory_model("Repeated Model", "publisher/repeated-one")]
            }

            plan = server._inventory_run_all_plan(
                inventory,
                registry_path,
                tmp_path / "missing-overlay.csv",
                eval_results_dir,
                database_path,
                clock=fixed_clock,
            )
            final_id = f"{base}-142345"
            html = server._run_all_confirm_page(plan, "test-token")
            starter = mock.Mock(return_value={"batch_id": "batch-fixture"})

            server._start_confirmed_candidate_batch(
                {
                    "token": ["test-token"],
                    "confirm_run_all": ["yes"],
                    "approval_scope": [server._run_all_fingerprint(plan)],
                },
                "test-token",
                plan,
                eval_results_dir,
                5,
                database_path,
                starter,
            )

            self.assertEqual(plan["runnable"][0]["run_id"], final_id)
            self.assertIn(final_id, html)
            starter.assert_called_once_with(
                plan["runnable"], eval_results_dir, 5, database_path
            )

    def test_run_all_mints_distinct_ids_for_same_slug_across_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "candidates.csv"
            database_path = tmp_path / "dashboard.sqlite"
            eval_results_dir = tmp_path / "eval_results"
            base = "20260717-shared-name-dashboard-test"
            (eval_results_dir / base).mkdir(parents=True)
            write_candidates(
                registry_path,
                [
                    candidate("candidate-one", "Shared Name", "publisher/shared-one"),
                    candidate("candidate-two", "Shared Name", "publisher/shared-two"),
                ],
            )
            db.init_db(database_path, reset=True)
            inventory = {
                "models": [
                    inventory_model("Shared Name", "publisher/shared-one"),
                    inventory_model("Shared Name", "publisher/shared-two"),
                ]
            }

            plan = server._inventory_run_all_plan(
                inventory,
                registry_path,
                tmp_path / "missing-overlay.csv",
                eval_results_dir,
                database_path,
                clock=fixed_clock,
            )

            self.assertEqual(
                [item["run_id"] for item in plan["runnable"]],
                [f"{base}-142345", f"{base}-142345-2"],
            )


class FreshRunWorkerGuardTests(unittest.TestCase):
    def test_late_artifact_collision_fails_without_execution_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            eval_results_dir = tmp_path / "eval_results"
            run_id = "20260717-race-dashboard-test"
            run_dir = eval_results_dir / run_id
            run_dir.mkdir(parents=True)
            marker = run_dir / "keep.txt"
            marker.write_text("original artifact", encoding="utf-8")

            with mock.patch.object(
                actions,
                "_run_subprocess",
                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
            ) as run:
                result = actions._background_candidate_test(
                    candidate("candidate-one", "Race Model", "publisher/race"),
                    run_id,
                    eval_results_dir,
                    5,
                    tmp_path / "dashboard.sqlite",
                )

            run.assert_not_called()
            self.assertEqual(result["status"], "failed")
            self.assertIn("already exists", result["reason"])
            self.assertEqual(marker.read_text(encoding="utf-8"), "original artifact")
            self.assertEqual([path.name for path in run_dir.iterdir()], ["keep.txt"])


if __name__ == "__main__":
    unittest.main()
