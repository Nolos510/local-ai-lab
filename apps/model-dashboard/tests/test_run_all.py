import csv
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402
from model_dashboard.pages import actions  # noqa: E402
from model_dashboard.pages.inventory import CANDIDATE_FIELDNAMES  # noqa: E402


def write_candidates(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def candidate(candidate_id, model_name, model_id, runner):
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


def runnable_item(candidate_id, model_name, model_id, runner, run_id):
    row = candidate(candidate_id, model_name, model_id, runner)
    return {
        "candidate": row,
        "candidate_id": candidate_id,
        "model_name": model_name,
        "model_id": model_id,
        "runner": runner,
        "run_id": run_id,
    }


class RunAllRenderTests(unittest.TestCase):
    def test_inventory_run_all_control_is_visible_only_when_runs_enabled(self):
        disabled = server._inventory(enable_run_tests=False)
        enabled = server._inventory(enable_run_tests=True)

        self.assertNotIn("Run all runnable", disabled)
        self.assertNotIn('action="/inventory/run-all"', disabled)
        self.assertIn("Run all runnable", enabled)
        self.assertIn('method="get" action="/inventory/run-all"', enabled)

    def test_confirm_page_enumerates_exact_batch_and_skipped_reasons_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry = tmp_path / "candidates.csv"
            write_candidates(
                registry,
                [
                    candidate(
                        "candidate-one",
                        "Runnable One",
                        "publisher/runnable-one",
                        "lmstudio-cli",
                    ),
                    candidate(
                        "candidate-two",
                        "Skipped Two",
                        "skipped-two:latest",
                        "",
                    ),
                ],
            )
            inventory = {
                "checked_at": "2026-07-14T12:00:00-07:00",
                "checks": [],
                "models": [
                    {
                        "runtime": "LM Studio",
                        "model_id": "publisher/runnable-one",
                        "display_name": "Runnable One",
                        "status": "loaded",
                    },
                    {
                        "runtime": "Ollama",
                        "model_id": "skipped-two:latest",
                        "display_name": "Skipped Two",
                        "status": "installed",
                    },
                ],
            }

            with mock.patch("subprocess.run") as run:
                plan = server._inventory_run_all_plan(
                    inventory,
                    registry,
                    tmp_path / "missing-overlay.csv",
                    tmp_path / "eval_results",
                )
                html = server._run_all_confirm_page(plan, "fixture-token")

            run.assert_not_called()
            self.assertEqual(len(plan["runnable"]), 1)
            self.assertEqual(len(plan["skipped"]), 1)
            self.assertIn("Run All Preflight", html)
            self.assertIn("candidate-one", html)
            self.assertIn("publisher/runnable-one", html)
            self.assertIn("lmstudio-cli", html)
            self.assertIn(plan["runnable"][0]["run_id"], html)
            self.assertIn("Skipped Two", html)
            self.assertIn("missing local runner", html)
            self.assertIn('action="/actions/run-all"', html)
            self.assertIn('name="token" value="fixture-token"', html)
            self.assertIn('name="confirm_run_all" value="yes"', html)
            self.assertIn('name="approval_scope"', html)


class RunAllWorkerTests(unittest.TestCase):
    def test_confirmed_dispatch_requires_token_and_confirmation_before_start(self):
        plan = {
            "runnable": [
                runnable_item(
                    "candidate-one",
                    "Runnable One",
                    "publisher/runnable-one",
                    "lmstudio-cli",
                    "20260714-runnable-one-dashboard-test",
                )
            ],
            "skipped": [],
        }
        approval_scope = server._run_all_fingerprint(plan)
        starter = mock.Mock()
        common_args = (
            "test-token",
            plan,
            Path("/fake/eval-results"),
            5,
            Path("/fake/dashboard.sqlite"),
            starter,
        )

        with self.assertRaisesRegex(ValueError, "Invalid action token"):
            server._start_confirmed_candidate_batch(
                {
                    "token": ["wrong"],
                    "confirm_run_all": ["yes"],
                    "approval_scope": [approval_scope],
                },
                *common_args,
            )
        starter.assert_not_called()

        with self.assertRaisesRegex(ValueError, "confirmation is required"):
            server._start_confirmed_candidate_batch(
                {"token": ["test-token"], "approval_scope": [approval_scope]},
                *common_args,
            )
        starter.assert_not_called()

    def test_confirmed_dispatch_starts_only_the_exact_preflight_plan(self):
        plan = {
            "runnable": [
                runnable_item(
                    "candidate-one",
                    "Runnable One",
                    "publisher/runnable-one",
                    "lmstudio-cli",
                    "20260714-runnable-one-dashboard-test",
                )
            ],
            "skipped": [],
        }
        started = {"batch_id": "batch-fixture"}
        starter = mock.Mock(return_value=started)
        form = {
            "token": ["test-token"],
            "confirm_run_all": ["yes"],
            "approval_scope": [server._run_all_fingerprint(plan)],
        }

        result = server._start_confirmed_candidate_batch(
            form,
            "test-token",
            plan,
            Path("/fake/eval-results"),
            5,
            Path("/fake/dashboard.sqlite"),
            starter,
        )

        self.assertEqual(result, started)
        starter.assert_called_once_with(
            plan["runnable"],
            Path("/fake/eval-results"),
            5,
            Path("/fake/dashboard.sqlite"),
        )

    def test_batch_dispatch_is_sequential_and_partial_failure_is_summarized(self):
        plan = [
            runnable_item(
                "candidate-one",
                "Runnable One",
                "publisher/runnable-one",
                "lmstudio-cli",
                "20260714-runnable-one-dashboard-test",
            ),
            runnable_item(
                "candidate-two",
                "Runnable Two",
                "runnable-two:latest",
                "ollama",
                "20260714-runnable-two-dashboard-test",
            ),
        ]
        status = actions._new_run_all_status("batch-fixture", plan)
        dispatched = []

        def fake_background(row, run_id, eval_results_dir, timeout, database_path):
            dispatched.append((row["candidate_id"], run_id))
            return {
                "candidate_id": row["candidate_id"],
                "model_name": row["model_name"],
                "model_id": row["local_model_id"],
                "runner": row["local_runner"],
                "run_id": run_id,
                "status": "failed" if row["candidate_id"] == "candidate-one" else "passed",
                "reason": "capture exited 9" if row["candidate_id"] == "candidate-one" else "",
            }

        with mock.patch.object(
            actions,
            "_background_candidate_test",
            side_effect=fake_background,
        ):
            actions._background_candidate_batch(
                plan,
                Path("/fake/eval-results"),
                5,
                Path("/fake/dashboard.sqlite"),
                status,
            )

        self.assertEqual(
            dispatched,
            [
                ("candidate-one", "20260714-runnable-one-dashboard-test"),
                ("candidate-two", "20260714-runnable-two-dashboard-test"),
            ],
        )
        self.assertEqual(status["state"], "complete")
        self.assertEqual([row["status"] for row in status["results"]], ["failed", "passed"])
        html = actions._run_all_status_page(status)
        self.assertIn("1 succeeded", html)
        self.assertIn("1 failed", html)
        self.assertIn("capture exited 9", html)
        self.assertIn("Runnable Two", html)


class RunAllHttpTests(unittest.TestCase):
    def start_server(self, db_path, **handler_kwargs):
        handler = server.make_handler(db_path, **handler_kwargs)
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        except PermissionError as exc:
            self.skipTest(f"local bind unavailable in this environment: {exc}")
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        return f"http://127.0.0.1:{httpd.server_port}"

    def post(self, url, form):
        request = Request(url, data=urlencode(form).encode("utf-8"), method="POST")
        return urlopen(request, timeout=5)

    def test_run_all_requires_token_and_explicit_confirmation_before_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            plan = {
                "runnable": [
                    runnable_item(
                        "candidate-one",
                        "Runnable One",
                        "publisher/runnable-one",
                        "lmstudio-cli",
                        "20260714-runnable-one-dashboard-test",
                    )
                ],
                "skipped": [],
            }
            approval_scope = server._run_all_fingerprint(plan)

            with (
                mock.patch.object(server, "_inventory_run_all_plan", return_value=plan),
                mock.patch.object(server, "_start_candidate_batch") as start,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_run_tests=True,
                    eval_results_dir=tmp_path / "eval_results",
                )

                with urlopen(f"{base_url}/inventory/run-all", timeout=5) as response:
                    preflight = response.read().decode("utf-8")

                self.assertIn("Run All Preflight", preflight)
                self.assertIn("publisher/runnable-one", preflight)
                start.assert_not_called()

                with self.assertRaises(HTTPError) as raised:
                    self.post(
                        f"{base_url}/actions/run-all",
                        {
                            "token": "wrong",
                            "confirm_run_all": "yes",
                            "approval_scope": approval_scope,
                        },
                    )
                self.assertEqual(raised.exception.code, 400)
                start.assert_not_called()

                with self.assertRaises(HTTPError) as raised:
                    self.post(
                        f"{base_url}/actions/run-all",
                        {"token": "test-token", "approval_scope": approval_scope},
                    )
                self.assertEqual(raised.exception.code, 400)
                start.assert_not_called()

    def test_confirmed_run_all_starts_the_exact_preflight_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            plan = {
                "runnable": [
                    runnable_item(
                        "candidate-one",
                        "Runnable One",
                        "publisher/runnable-one",
                        "lmstudio-cli",
                        "20260714-runnable-one-dashboard-test",
                    ),
                    runnable_item(
                        "candidate-two",
                        "Runnable Two",
                        "runnable-two:latest",
                        "ollama",
                        "20260714-runnable-two-dashboard-test",
                    ),
                ],
                "skipped": [],
            }
            started = {
                "batch_id": "batch-fixture",
                "status": actions._new_run_all_status("batch-fixture", plan["runnable"]),
                "thread_name": "dashboard-run-all-batch-fixture",
            }

            with (
                mock.patch.object(
                    server, "_inventory_run_all_plan", return_value=plan
                ) as planner,
                mock.patch.object(server, "_start_candidate_batch", return_value=started) as start,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_run_tests=True,
                    eval_results_dir=tmp_path / "eval_results",
                )
                with urlopen(f"{base_url}/inventory/run-all", timeout=5) as response:
                    preflight = response.read().decode("utf-8")
                with self.post(
                    f"{base_url}/actions/run-all",
                    {
                        "token": "test-token",
                        "confirm_run_all": "yes",
                        "approval_scope": server._run_all_fingerprint(plan),
                    },
                ) as response:
                    body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn(plan["runnable"][0]["run_id"], preflight)
            self.assertIn(plan["runnable"][1]["run_id"], preflight)
            self.assertIn("Run All Started", body)
            self.assertIn("2 models", body)
            self.assertIn("/inventory/run-all/status?batch_id=batch-fixture", body)
            planner.assert_called_once()
            start.assert_called_once()
            self.assertEqual(start.call_args.args[0], plan["runnable"])


if __name__ == "__main__":
    unittest.main()
