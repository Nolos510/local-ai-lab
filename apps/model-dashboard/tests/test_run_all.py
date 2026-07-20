import csv
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402
from model_dashboard.pages import actions  # noqa: E402
from model_dashboard.pages.inventory import CANDIDATE_FIELDNAMES  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


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

        self.assertNotIn("Run all needing evidence", disabled)
        self.assertNotIn('action="/inventory/run-all"', disabled)
        self.assertIn("Run all needing evidence", enabled)
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

    def test_run_all_plan_skips_models_with_complete_actionable_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry = tmp_path / "candidates.csv"
            db_path = tmp_path / "dashboard.sqlite"
            write_candidates(
                registry,
                [
                    candidate(
                        "candidate-one",
                        "Runnable One",
                        "publisher/runnable-one",
                        "lmstudio-cli",
                    )
                ],
            )
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name)
                    VALUES (1, 'Runnable One')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, tokens_per_sec, ram_usage_gb,
                        quantization, context_window, temperature, top_p, run_notes
                    )
                    VALUES (
                        1, 1, '2026-07-17', 'LM Studio CLI', 42.0, 12.5,
                        '4bit', 4096, 0.2, 0.9,
                        'candidate_id=candidate-one | model_id=publisher/runnable-one'
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO eval_scores (
                        id, run_id, instruction_following, truthfulness_uncertainty,
                        reasoning, coding_debugging, agent_planning,
                        local_ai_lab_usefulness, research_synthesis,
                        business_seo_strategy, long_context, creativity,
                        speed_practicality, total_score, final_label, score_status
                    )
                    VALUES (
                        1, 1, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 77,
                        'DAILY_DRIVER', 'confirmed'
                    )
                    """
                )
            inventory = {
                "checked_at": "2026-07-17T12:00:00-07:00",
                "checks": [],
                "models": [
                    {
                        "runtime": "LM Studio",
                        "model_id": "publisher/runnable-one",
                        "display_name": "Runnable One",
                        "status": "loaded",
                    }
                ],
            }

            plan = server._inventory_run_all_plan(
                inventory,
                registry,
                tmp_path / "missing-overlay.csv",
                tmp_path / "eval_results",
                db_path,
            )

            self.assertEqual(plan["runnable"], [])
            self.assertEqual(len(plan["skipped"]), 1)
            self.assertIn("already has confirmed score", plan["skipped"][0]["reason"])


class RunAllWorkerTests(unittest.TestCase):
    def test_candidate_commands_write_inferred_run_config_metadata(self):
        row = candidate(
            "candidate-one",
            "Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
            "lmstudio-community/qwen3-coder-30b-a3b-instruct-mlx",
            "lmstudio-cli",
        )
        row.update(
            {
                "format_or_runtime": "MLX through LM Studio",
                "runtime_availability": "Local path /Users/example/.lmstudio/models/qwen-mlx-4bit",
            }
        )

        init_command, capture_command = actions._build_candidate_commands(
            row,
            "20260717-qwen3-coder-dashboard-test",
            Path("/fake/eval-results"),
        )

        self.assertIn("--quantization", init_command)
        self.assertEqual(init_command[init_command.index("--quantization") + 1], "4bit")
        self.assertIn("--context-window", init_command)
        self.assertEqual(init_command[init_command.index("--context-window") + 1], "4096")
        self.assertIn("--temperature", init_command)
        self.assertEqual(init_command[init_command.index("--temperature") + 1], "0.2")
        self.assertIn("--top-p", init_command)
        self.assertEqual(init_command[init_command.index("--top-p") + 1], "0.9")
        run_notes = init_command[init_command.index("--run-notes") + 1]
        self.assertIn("quantization_source=inferred:model_name_or_path", run_notes)
        self.assertIn("context_window_source=inferred:benchmark_default", run_notes)
        self.assertIn("temperature_source=inferred:benchmark_default", run_notes)
        self.assertIn("top_p_source=inferred:benchmark_default", run_notes)
        self.assertIn("run-lmstudio-cli", capture_command)
        self.assertIn("--manage-model-lifecycle", capture_command)

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

    def test_background_candidate_test_generates_and_imports_draft_scores_when_enabled(self):
        row = candidate(
            "candidate-one",
            "Runnable One",
            "publisher/runnable-one",
            "lmstudio-cli",
        )
        ok = SimpleNamespace(returncode=0, stdout="", stderr="")
        score_path = Path("/fake/eval-results/run-one/draft-scores.json")

        with (
            mock.patch.object(actions, "_existing_benchmark_run_ids", return_value=set()),
            mock.patch.object(
                actions,
                "_run_candidate_test_for_row",
                return_value={"init": ok, "capture": ok},
            ) as run_candidate,
            mock.patch.object(
                actions,
                "_suggest_draft_scores",
                return_value=(ok, score_path),
            ) as suggest_scores,
            mock.patch.object(actions, "_export_dashboard_import", return_value=ok) as export,
            mock.patch.object(
                actions,
                "_sync_pending_artifacts",
                return_value={"imported": [{"benchmark_run_id": "run-one"}], "skipped": []},
            ) as sync,
        ):
            result = actions._background_candidate_test(
                row,
                "run-one",
                Path("/fake/eval-results"),
                5,
                Path("/fake/dashboard.sqlite"),
                {
                    "enabled": True,
                    "endpoint": "http://127.0.0.1:1234/v1",
                    "judge_model": "local-judge",
                },
            )

        self.assertEqual(result["status"], "passed")
        run_candidate.assert_called_once()
        suggest_scores.assert_called_once_with(
            "run-one",
            Path("/fake/eval-results"),
            5,
            "http://127.0.0.1:1234/v1",
            "local-judge",
        )
        export.assert_called_once_with(
            "run-one",
            Path("/fake/eval-results"),
            5,
            scores_path=score_path,
        )
        sync.assert_called_once()

    def test_background_candidate_test_keeps_capture_passed_when_draft_scoring_fails(self):
        row = candidate(
            "candidate-one",
            "Runnable One",
            "publisher/runnable-one",
            "lmstudio-cli",
        )
        ok = SimpleNamespace(returncode=0, stdout="", stderr="")
        score_failed = SimpleNamespace(returncode=1, stdout="", stderr="connection failed")

        with (
            mock.patch.object(actions, "_existing_benchmark_run_ids", return_value=set()),
            mock.patch.object(
                actions,
                "_run_candidate_test_for_row",
                return_value={"init": ok, "capture": ok},
            ),
            mock.patch.object(
                actions,
                "_suggest_draft_scores",
                return_value=(score_failed, Path("/fake/draft-scores.json")),
            ),
            mock.patch.object(actions, "_export_dashboard_import", return_value=ok),
            mock.patch.object(
                actions,
                "_sync_pending_artifacts",
                return_value={"imported": [{"benchmark_run_id": "run-one"}], "skipped": []},
            ),
        ):
            result = actions._background_candidate_test(
                row,
                "run-one",
                Path("/fake/eval-results"),
                5,
                Path("/fake/dashboard.sqlite"),
                {
                    "enabled": True,
                    "endpoint": "http://127.0.0.1:1234/v1",
                    "judge_model": "local-judge",
                },
            )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["scoring_status"], "pending")
        self.assertIn("draft scoring exited 1", result["reason"])
        self.assertNotIn("connection failed", result["reason"])

    def test_run_all_status_distinguishes_capture_passed_scoring_pending(self):
        status = {
            "state": "complete",
            "plan": [
                runnable_item(
                    "candidate-one",
                    "Runnable One",
                    "publisher/runnable-one",
                    "lmstudio-cli",
                    "run-one",
                )
            ],
            "results": [
                {
                    "run_id": "run-one",
                    "status": "passed",
                    "scoring_status": "pending",
                    "reason": "draft scoring exited 1; raw benchmark evidence preserved",
                }
            ],
        }

        html = actions._run_all_status_page(status)

        self.assertIn("Capture passed", html)
        self.assertIn("Scoring pending", html)
        self.assertIn("1 succeeded", html)
        self.assertNotIn('<span class="pill">failed</span>', html)

    def test_judge_preflight_requires_model_and_exact_local_inventory_match(self):
        with self.assertRaisesRegex(ValueError, "judge model"):
            actions._judge_preflight("http://127.0.0.1:1234/v1", None, 5)

        with (
            mock.patch.object(actions, "_judge_model_ids", return_value={"loaded-judge"}),
            self.assertRaisesRegex(ValueError, "not available"),
        ):
            actions._judge_preflight(
                "http://127.0.0.1:1234/v1",
                "missing-judge",
                5,
            )

        with mock.patch.object(actions, "_judge_model_ids", return_value={"loaded-judge"}):
            result = actions._judge_preflight(
                "http://127.0.0.1:1234/v1",
                "loaded-judge",
                5,
            )

        self.assertEqual(result["model"], "loaded-judge")

    def test_judge_inventory_uses_lm_api_token_without_leaking_it(self):
        expected_token = "fixture-secret-token"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.server.authorization = self.headers.get("Authorization")
                body = json.dumps({"data": [{"id": "loaded-judge"}]}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{httpd.server_port}/v1"
            with mock.patch.dict("os.environ", {"LM_API_TOKEN": expected_token}):
                model_ids = actions._judge_model_ids(endpoint, 5)
        finally:
            httpd.shutdown()
            httpd.server_close()

        self.assertEqual(model_ids, {"loaded-judge"})
        self.assertEqual(httpd.authorization, f"Bearer {expected_token}")

    def test_judge_inventory_401_has_actionable_sanitized_error(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"server-secret-should-not-leak")

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{httpd.server_port}/v1"
            with self.assertRaisesRegex(ValueError, "LM_API_TOKEN") as raised:
                actions._judge_model_ids(endpoint, 5)
        finally:
            httpd.shutdown()
            httpd.server_close()

        self.assertNotIn("server-secret", str(raised.exception))

    def test_unscored_artifacts_require_raw_responses_and_no_score_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready = root / "ready-run"
            ready.mkdir()
            (ready / "raw_responses.jsonl").write_text('{"ok": true}\n', encoding="utf-8")
            empty = root / "empty-run"
            empty.mkdir()
            (empty / "raw_responses.jsonl").write_text("", encoding="utf-8")
            drafted = root / "drafted-run"
            drafted.mkdir()
            (drafted / "raw_responses.jsonl").write_text('{"ok": true}\n', encoding="utf-8")
            (drafted / "draft-scores.json").write_text("{}\n", encoding="utf-8")

            self.assertEqual(actions._unscored_artifact_ids(root), ["ready-run"])

    def test_unscored_artifacts_resume_draft_files_not_imported_into_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            for run_id in ("pending-draft", "imported-draft"):
                run_dir = root / run_id
                run_dir.mkdir()
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"ok": true}\n',
                    encoding="utf-8",
                )
                (run_dir / "draft-scores.json").write_text("{}\n", encoding="utf-8")

            with mock.patch.object(
                actions,
                "_dashboard_runs_by_benchmark_id",
                return_value={"imported-draft": {"score_status": "draft"}},
            ):
                run_ids = actions._unscored_artifact_ids(root, database_path)

            self.assertEqual(run_ids, ["pending-draft"])

    def test_score_artifact_reuses_existing_draft_before_export_and_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "existing-draft"
            run_dir = root / run_id
            run_dir.mkdir()
            draft_path = run_dir / "draft-scores.json"
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"usable local answer"}\n',
                encoding="utf-8",
            )
            draft_path.write_text(
                json.dumps(
                    {
                        "scores": {field: 80 for field in METRIC_FIELDS},
                        "total_score": 80,
                        "final_label": "LOCAL_AI_ASSISTANT",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            ok = SimpleNamespace(returncode=0, stdout="", stderr="")

            with (
                mock.patch.object(actions, "_suggest_draft_scores") as suggest,
                mock.patch.object(
                    actions,
                    "_export_dashboard_import",
                    return_value=ok,
                ) as export,
                mock.patch.object(
                    actions,
                    "_import_artifact",
                    return_value={"benchmark_run_id": run_id, "counts": {}},
                ) as import_artifact,
            ):
                result = actions._score_artifact(
                    run_id,
                    root / "dashboard.sqlite",
                    root,
                    5,
                    "http://127.0.0.1:1234/v1",
                    "local-judge",
                )

            suggest.assert_not_called()
            export.assert_called_once_with(run_id, root, 5, scores_path=draft_path.resolve())
            import_artifact.assert_called_once()
            self.assertEqual(result["draft_scores"], str(draft_path.resolve()))

    def test_score_artifact_archives_all_zero_attempt_before_bounded_rescore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "repair-zero-draft"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"usable local answer"}\n',
                encoding="utf-8",
            )
            draft_path = run_dir / "draft-scores.json"
            draft_path.write_text(
                json.dumps(
                    {
                        "scores": {field: 0 for field in METRIC_FIELDS},
                        "total_score": 0,
                        "final_label": "WATCHLIST",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            ok = SimpleNamespace(returncode=0, stdout="", stderr="")

            def write_repaired_score(*_args, **_kwargs):
                draft_path.write_text(
                    json.dumps(
                        {
                            "scores": {field: 82 for field in METRIC_FIELDS},
                            "total_score": 82,
                            "final_label": "LOCAL_AI_ASSISTANT",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return ok, draft_path

            with (
                mock.patch.object(
                    actions,
                    "_suggest_draft_scores",
                    side_effect=write_repaired_score,
                ) as suggest,
                mock.patch.object(actions, "_export_dashboard_import", return_value=ok),
                mock.patch.object(
                    actions,
                    "_import_artifact",
                    return_value={"benchmark_run_id": run_id, "counts": {}},
                ),
            ):
                result = actions._score_artifact(
                    run_id,
                    root / "dashboard.sqlite",
                    root,
                    5,
                    "http://127.0.0.1:1234/v1",
                    "local-judge",
                )

            self.assertEqual(suggest.call_count, 1)
            archived = run_dir / "score-attempts" / "attempt-01" / "draft-scores.json"
            self.assertTrue(archived.is_file())
            self.assertEqual(
                json.loads(archived.read_text(encoding="utf-8"))["total_score"],
                0,
            )
            self.assertEqual(
                json.loads(draft_path.read_text(encoding="utf-8"))["total_score"],
                82,
            )
            self.assertEqual(result["benchmark_run_id"], run_id)

    def test_background_score_batch_continues_after_one_artifact_fails(self):
        status = actions._new_score_batch_status("score-batch", ["run-one", "run-two"])

        def fake_score(run_id, *args):
            if run_id == "run-one":
                raise ValueError("judge unavailable")
            return {"benchmark_run_id": run_id, "counts": {"eval_scores": 1}}

        with mock.patch.object(actions, "_score_artifact", side_effect=fake_score):
            actions._background_score_batch(
                ["run-one", "run-two"],
                Path("/fake/dashboard.sqlite"),
                Path("/fake/eval-results"),
                5,
                "http://127.0.0.1:1234/v1",
                "loaded-judge",
                status,
            )

        self.assertEqual(status["state"], "complete")
        self.assertEqual([row["status"] for row in status["results"]], ["failed", "passed"])
        self.assertEqual(status["current_run_id"], "")


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
