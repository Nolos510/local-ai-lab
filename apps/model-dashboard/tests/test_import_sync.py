import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import csv_io, db, server  # noqa: E402


def write_table(path, table_name, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_io.TABLE_FIELDS[table_name])
        writer.writeheader()
        writer.writerows(rows)


def write_import_set(eval_results, run_id):
    import_dir = eval_results / run_id / "dashboard-import"
    write_table(
        import_dir / "models.csv",
        "models",
        [{"id": 1, "model_name": "U1 Import Model", "provider": "local"}],
    )
    write_table(
        import_dir / "model_runs.csv",
        "model_runs",
        [
            {
                "id": 1,
                "model_id": 1,
                "date_tested": "2026-07-14",
                "backend": "LM Studio CLI",
                "run_notes": f"benchmark_run_id={run_id} | u1_fixture=yes",
            }
        ],
    )
    write_table(import_dir / "eval_scores.csv", "eval_scores", [])
    write_table(import_dir / "decisions.csv", "decisions", [])


def load_dashboard_entrypoint():
    spec = importlib.util.spec_from_file_location(
        "dashboard_entrypoint_for_u1_tests", APP_DIR / "run_dashboard.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportSyncTests(unittest.TestCase):
    def test_startup_sync_imports_pending_set_once_across_two_boots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            eval_results = root / "eval_results"
            run_id = "20260714-u1-startup"
            write_import_set(eval_results, run_id)

            first = server._startup_import_sync(database_path, eval_results, enabled=True)
            second = server._startup_import_sync(database_path, eval_results, enabled=True)

            with db.connect(database_path) as conn:
                self.assertEqual(db.table_count(conn, "models"), 1)
                self.assertEqual(db.table_count(conn, "model_runs"), 1)
                self.assertEqual(server._pending_artifact_run_ids(conn, eval_results), [])

        self.assertEqual([row["benchmark_run_id"] for row in first["imported"]], [run_id])
        self.assertEqual(first["skipped"], [])
        self.assertEqual(second["imported"], [])
        self.assertEqual(second["skipped"], [])

    def test_corrupt_set_is_skipped_with_escaped_visible_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            eval_results = root / "eval_results"
            run_id = "20260714-u1-corrupt"
            write_import_set(eval_results, run_id)
            (eval_results / run_id / "dashboard-import" / "model_runs.csv").write_text(
                "id\nnot-an-integer\n", encoding="utf-8"
            )

            result = server._startup_import_sync(database_path, eval_results, enabled=True)
            notice = server._import_sync_notice(result)

            with db.connect(database_path) as conn:
                self.assertEqual(db.table_count(conn, "models"), 0)
                self.assertEqual(db.table_count(conn, "model_runs"), 0)

        self.assertEqual(result["imported"], [])
        self.assertEqual(result["skipped"][0]["benchmark_run_id"], run_id)
        self.assertEqual(result["skipped"][0]["reason"], "invalid dashboard CSV set")
        self.assertIn("Skipped 1 corrupt or incomplete artifact set", notice)
        self.assertIn(run_id, notice)
        self.assertNotIn(str(root), notice)

    def test_loopback_defaults_on_non_loopback_off_and_disable_flag_wins(self):
        entrypoint = load_dashboard_entrypoint()
        parser = entrypoint.build_parser()

        self.assertTrue(server._resolve_import_actions("127.0.0.1", None))
        self.assertTrue(server._resolve_import_actions("localhost", None))
        self.assertTrue(server._resolve_import_actions("::1", None))
        self.assertFalse(server._resolve_import_actions("0.0.0.0", None))
        self.assertFalse(server._resolve_import_actions("127.0.0.1", False))
        self.assertFalse(server._resolve_import_actions("0.0.0.0", True))
        self.assertIsNone(parser.parse_args(["serve"]).enable_import_actions)
        self.assertFalse(
            parser.parse_args(["serve", "--disable-import-actions"]).enable_import_actions
        )

    def test_import_all_controls_on_home_and_benchmark_include_action_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            eval_results = root / "eval_results"
            write_import_set(eval_results, "20260714-u1-button")
            db.init_db(database_path, reset=True)

            with db.connect(database_path) as conn:
                with mock.patch("subprocess.run") as run:
                    home_html = server._overview(
                        conn,
                        registry_path=root / "candidates.csv",
                        local_inventory_path=root / "inventory.csv",
                        eval_results_dir=eval_results,
                        hardware_profiles_dir=root / "hardware",
                        enable_import_actions=True,
                        action_token="u1-token",
                    )
                    benchmark_html = server._runs(
                        conn,
                        database_path=database_path,
                        eval_results_dir=eval_results,
                        enable_import_actions=True,
                        action_token="u1-token",
                    )
                run.assert_not_called()

        for html in (home_html, benchmark_html):
            self.assertIn('method="post" action="/actions/import-all"', html)
            self.assertIn('name="token" value="u1-token"', html)
            self.assertIn("Import all pending", html)

    def test_disabled_import_all_control_has_no_post_form_or_token(self):
        html = server._artifact_import_all_control(
            2,
            enable_import_actions=False,
            action_token="must-not-leak",
        )

        self.assertIn("disabled", html)
        self.assertNotIn('action="/actions/import-all"', html)
        self.assertNotIn("must-not-leak", html)

    def test_post_sync_home_and_benchmark_render_imported_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            eval_results = root / "eval_results"
            run_id = "20260714-u1-post-sync"
            write_import_set(eval_results, run_id)
            result = server._startup_import_sync(database_path, eval_results, enabled=True)

            with db.connect(database_path) as conn:
                home_html = server._overview(
                    conn,
                    registry_path=root / "candidates.csv",
                    local_inventory_path=root / "inventory.csv",
                    eval_results_dir=eval_results,
                    hardware_profiles_dir=root / "hardware",
                    enable_import_actions=True,
                    action_token="u1-token",
                    import_sync_result=result,
                )
                benchmark_html = server._runs(
                    conn,
                    database_path=database_path,
                    eval_results_dir=eval_results,
                    enable_import_actions=True,
                    action_token="u1-token",
                    import_sync_result=result,
                )

        self.assertNotIn("Import benchmark artifacts", home_html)
        self.assertNotIn('action="/actions/import-all"', home_html)
        self.assertIn("Automatic artifact sync imported 1 set", home_html)
        self.assertIn("imported model", benchmark_html)
        self.assertNotIn('action="/actions/import-all"', benchmark_html)

    def test_serve_calls_patchable_startup_sync_before_server_loop(self):
        calls = []

        class FakeServer:
            def __init__(self, address, handler):
                calls.append((address, handler))

            def serve_forever(self):
                return None

            def server_close(self):
                return None

        with tempfile.TemporaryDirectory() as tmp:
            database_path = Path(tmp) / "dashboard.sqlite"
            sync_result = {"imported": [], "skipped": []}
            with (
                mock.patch.object(server, "_startup_import_sync", return_value=sync_result) as sync,
                mock.patch.object(server, "ThreadingHTTPServer", FakeServer),
            ):
                server.serve(database_path, host="127.0.0.1", port=0)

        sync.assert_called_once()
        self.assertEqual(sync.call_args.args[0], database_path)
        self.assertTrue(sync.call_args.kwargs["enabled"])
        self.assertEqual(calls[0][0], ("127.0.0.1", 0))


if __name__ == "__main__":
    unittest.main()
