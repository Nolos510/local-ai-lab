import csv
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import csv_io, db, server  # noqa: E402
from model_dashboard.pages import actions  # noqa: E402


def write_table(path, table_name, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_io.TABLE_FIELDS[table_name])
        writer.writeheader()
        writer.writerows(rows)


class DashboardHttpHandlerTests(unittest.TestCase):
    def start_server(self, db_path, **handler_kwargs):
        if "local_inventory_registry_path" not in handler_kwargs:
            overlay_dir = tempfile.TemporaryDirectory()
            self.addCleanup(overlay_dir.cleanup)
            handler_kwargs["local_inventory_registry_path"] = (
                Path(overlay_dir.name) / "local_inventory_candidates.csv"
            )
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
        body = urlencode(form).encode("utf-8")
        request = Request(url, data=body, method="POST")
        return urlopen(request, timeout=5)

    def test_valid_get_route_returns_dashboard_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            with urlopen(f"{base_url}/lab", timeout=5) as response:
                body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
            self.assertIn("Local Model Performance Dashboard", body)
            self.assertIn("Home", body)
            self.assertIn("Export report", body)

    def test_home_route_uses_configured_local_metadata_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            candidate_registry = tmp_path / "candidates.csv"
            local_inventory = tmp_path / "local_inventory_candidates.csv"
            eval_results = tmp_path / "eval_results"
            candidate_registry.write_text(
                "candidate_id,model_name,status,local_runner,local_model_id\n"
                "ready-one,Ready One,ready_for_eval,lmstudio-cli,ready-one\n",
                encoding="utf-8",
            )
            local_inventory.write_text(
                "candidate_id,model_name,status,local_runner,local_model_id\n"
                "local-one,Local One,ready_for_eval,lmstudio-cli,local-one\n",
                encoding="utf-8",
            )
            (eval_results / "artifact-one").mkdir(parents=True)
            (eval_results / "artifact-two").mkdir()
            db.init_db(db_path, reset=True)
            base_url = self.start_server(
                db_path,
                action_token="test-token",
                candidate_registry_path=candidate_registry,
                local_inventory_registry_path=local_inventory,
                eval_results_dir=eval_results,
            )

            with urlopen(f"{base_url}/", timeout=5) as response:
                body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("<span>Discover</span>", body)
            self.assertIn("<strong>2</strong>", body)
            self.assertIn("<em>candidates to evaluate</em>", body)
            self.assertIn("<span>Install</span>", body)
            self.assertIn("<em>detected local models</em>", body)
            self.assertIn("<span>Benchmark</span>", body)
            self.assertIn("<em>artifact directories</em>", body)
            self.assertIn("Benchmark your first local model", body)

    def test_discover_route_uses_configured_radar_and_project_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            candidate_registry = tmp_path / "candidates.csv"
            project_registry = tmp_path / "github_repos.csv"
            candidate_registry.write_text(
                "candidate_id,model_name,model_family,provider_or_org,status,format_or_runtime,"
                "source_packet_path,report_path,benchmark_run_id,why_interesting,risk_notes,"
                "proposed_eval,security_review_status,download_approval,license_review_status,"
                "provenance_status,security_notes,isolation_notes,security_review_path\n"
                "custom-ready,Custom Ready,Custom,local,ready_for_eval,llama.cpp,"
                "inputs/custom.md,reports/custom.md,,Why,Risk,Eval,local_inventory_reviewed,"
                "not_needed_local,needs_review,local_inventory,Notes,Loopback only,\n",
                encoding="utf-8",
            )
            project_registry.write_text(
                "repo_id,repo_name,owner,repo_url,category,status,priority_score,"
                "priority_rationale,stars_observed,license,source_packet_path,report_path,"
                "why_interesting,business_tie_in,local_fit,risk_notes,recommended_next_step\n"
                "custom-project,Custom Project,example,https://github.com/example/custom,"
                "local inference,ready_for_review,5,Local fit,1k,MIT,inputs/projects.md,"
                "reports/projects.md,Useful locally,Portfolio tie-in,Self-hosted path,"
                "Review telemetry,Read source\n",
                encoding="utf-8",
            )
            db.init_db(db_path, reset=True)
            base_url = self.start_server(
                db_path,
                action_token="test-token",
                candidate_registry_path=candidate_registry,
                project_registry_path=project_registry,
            )

            with urlopen(f"{base_url}/radar", timeout=5) as response:
                body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Discover records are local review metadata only", body)
            self.assertIn("Custom Ready", body)
            self.assertIn("Custom Project", body)
            self.assertIn("Project Radar", body)
            self.assertNotIn("Ready Local 7B", body)

    def test_demoted_get_routes_remain_reachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            for path in (
                "/lab",
                "/capability",
                "/specialty",
                "/projects",
                "/storage",
                "/compare",
                "/reports",
            ):
                with self.subTest(path=path):
                    with urlopen(f"{base_url}{path}", timeout=5) as response:
                        body = response.read().decode("utf-8")

                    self.assertEqual(response.status, 200)
                    self.assertNotIn("Page not found", body)

    def test_unknown_post_route_returns_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            with self.assertRaises(HTTPError) as raised:
                self.post(f"{base_url}/actions/not-real", {"token": "test-token"})

            self.assertEqual(raised.exception.code, 404)

    def test_post_with_bad_token_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            with self.assertRaises(HTTPError) as raised:
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "wrong"})

            self.assertEqual(raised.exception.code, 400)

    def test_oversized_post_body_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            with self.assertRaises(HTTPError) as raised:
                self.post(
                    f"{base_url}/actions/refresh-inventory",
                    {"token": "test-token", "payload": "x" * 4097},
                )

            self.assertEqual(raised.exception.code, 400)

    def test_inventory_refresh_is_refused_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(
                db_path,
                action_token="test-token",
                enable_inventory_refresh=False,
            )

            with self.assertRaises(HTTPError) as raised:
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"})

            self.assertEqual(raised.exception.code, 403)

    def test_inventory_refresh_auto_registers_detected_lmstudio_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            result = {
                "checked_at": "2026-06-05T12:00:00-07:00",
                "checks": [],
                "models": [
                    {
                        "runtime": "LM Studio",
                        "model_id": "mistral-dolphin-mix-cine-open-ne-nsfw",
                        "display_name": "Mistral Dolphin Mix Cine Open Ne NSFW",
                        "status": "loaded",
                        "source_path": "mraderacher/Mistral-Dolphin-GGUF/model.gguf",
                        "local_path": (
                            "/Users/example/.lmstudio/models/mraderacher/"
                            "Mistral-Dolphin-GGUF"
                        ),
                        "model_type": "llm",
                    },
                    {
                        "runtime": "Ollama",
                        "model_id": "qwen3:30b",
                        "display_name": "qwen3:30b",
                        "status": "installed",
                        "local_path": "/Users/example/.ollama/models/manifests/qwen3/30b",
                        "model_type": "llm",
                        "format_or_runtime": "Ollama",
                    }
                ],
            }
            overlay_path = tmp_path / "local_inventory_candidates.csv"

            with mock.patch.object(server, "_refresh_inventory", return_value=result):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_run_tests=True,
                    candidate_registry_path=tmp_path / "missing.csv",
                    local_inventory_registry_path=overlay_path,
                )
                with self.post(
                    f"{base_url}/actions/refresh-inventory",
                    {"token": "test-token"},
                ) as response:
                    body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertTrue(overlay_path.exists())
            self.assertIn("Auto-registered exact local IDs: 2", body)
            self.assertIn("Mistral Dolphin Mix Cine Open Ne NSFW", body)
            self.assertIn("Run Test", body)
            self.assertIn("mistral-dolphin-mix-cine-open-ne-nsfw", body)
            self.assertIn("qwen3:30b", body)

    def test_delete_model_action_is_refused_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            with (
                mock.patch("model_dashboard.removal.subprocess.run") as run,
                self.assertRaises(HTTPError) as raised,
            ):
                self.post(
                    f"{base_url}/actions/delete-model",
                    {"token": "test-token", "remove_key": "anything"},
                )

            self.assertEqual(raised.exception.code, 403)
            run.assert_not_called()

    def test_run_test_action_starts_background_and_returns_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            started = {
                "candidate": {
                    "candidate_id": "candidate-ready",
                    "model_name": "Ready Local 7B",
                    "local_runner": "lmstudio-cli",
                    "local_model_id": "ready-local-7b",
                },
                "run_id": "20260621-ready-local-dashboard-test",
                "run_dir": str(tmp_path / "eval_results" / "20260621-ready-local-dashboard-test"),
                "thread_name": "dashboard-run-test",
            }

            with mock.patch.object(server, "_start_candidate_test", return_value=started) as start:
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_run_tests=True,
                )
                with self.post(
                    f"{base_url}/actions/run-test",
                    {"token": "test-token", "candidate_id": "candidate-ready"},
                ) as response:
                    body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Run Test Started", body)
            self.assertIn("Ready Local 7B", body)
            self.assertIn("20260621-ready-local-dashboard-test", body)
            start.assert_called_once()
            self.assertEqual(start.call_args.args[0], "candidate-ready")
            self.assertEqual(start.call_args.args[4], db_path)

    def test_background_run_imports_dashboard_csvs_after_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            fixture_dir = APP_DIR / "fixtures"
            csv_io.import_fixture_set(db_path, fixture_dir)
            eval_results = tmp_path / "eval_results"
            run_id = "20260621-ready-local-dashboard-test"
            import_dir = eval_results / run_id / "dashboard-import"

            write_table(
                import_dir / "models.csv",
                "models",
                [{"id": 1, "model_name": "Ready Local 7B", "provider": "local"}],
            )
            write_table(
                import_dir / "model_runs.csv",
                "model_runs",
                [
                    {
                        "id": 1,
                        "model_id": 1,
                        "date_tested": "2026-06-21",
                        "backend": "LM Studio CLI",
                        "tokens_per_sec": 22.5,
                        "run_notes": f"benchmark_run_id={run_id} | dashboard_run_button=yes",
                    }
                ],
            )
            write_table(import_dir / "eval_scores.csv", "eval_scores", [])
            write_table(import_dir / "decisions.csv", "decisions", [])

            with (
                mock.patch.object(actions, "_run_candidate_test_for_row") as run_capture,
                mock.patch.object(
                    actions,
                    "_run_subprocess",
                    return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                ) as export,
            ):
                actions._background_candidate_test(
                    {"candidate_id": "candidate-ready", "model_name": "Ready Local 7B"},
                    run_id,
                    eval_results,
                    5,
                    db_path,
                )

            run_capture.assert_called_once()
            export.assert_called_once()
            with db.connect(db_path) as conn:
                imported = conn.execute(
                    """
                    SELECT m.model_name, r.tokens_per_sec
                    FROM model_runs r
                    JOIN models m ON m.id = r.model_id
                    WHERE r.run_notes LIKE ?
                    """,
                    (f"%benchmark_run_id={run_id}%",),
                ).fetchone()

            self.assertIsNotNone(imported)
            self.assertEqual(imported["model_name"], "Ready Local 7B")
            self.assertEqual(imported["tokens_per_sec"], 22.5)

    def test_inventory_refresh_runs_pending_artifact_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            eval_results = tmp_path / "eval_results"
            run_id = "20260714-refresh-sync"
            import_dir = eval_results / run_id / "dashboard-import"
            write_table(
                import_dir / "models.csv",
                "models",
                [{"id": 1, "model_name": "Refresh Sync Model", "provider": "local"}],
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
                        "run_notes": f"benchmark_run_id={run_id}",
                    }
                ],
            )
            write_table(import_dir / "eval_scores.csv", "eval_scores", [])
            write_table(import_dir / "decisions.csv", "decisions", [])
            db.init_db(db_path, reset=True)
            inventory = {"checked_at": "2026-07-14T10:00:00Z", "checks": [], "models": []}

            with mock.patch.object(server, "_refresh_inventory", return_value=inventory):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_import_actions=True,
                    eval_results_dir=eval_results,
                )
                with self.post(
                    f"{base_url}/actions/refresh-inventory",
                    {"token": "test-token"},
                ) as response:
                    response.read()

            self.assertEqual(response.status, 200)
            with db.connect(db_path) as conn:
                self.assertEqual(server._pending_artifact_run_ids(conn, eval_results), [])
                self.assertEqual(db.table_count(conn, "model_runs"), 1)

    def test_import_all_action_requires_token_and_renders_post_sync_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "dashboard.sqlite"
            eval_results = tmp_path / "eval_results"
            run_id = "20260714-manual-sync"
            import_dir = eval_results / run_id / "dashboard-import"
            write_table(
                import_dir / "models.csv",
                "models",
                [{"id": 1, "model_name": "Manual Sync Model", "provider": "local"}],
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
                        "run_notes": f"benchmark_run_id={run_id}",
                    }
                ],
            )
            write_table(import_dir / "eval_scores.csv", "eval_scores", [])
            write_table(import_dir / "decisions.csv", "decisions", [])
            db.init_db(db_path, reset=True)
            base_url = self.start_server(
                db_path,
                action_token="test-token",
                enable_import_actions=True,
                eval_results_dir=eval_results,
            )

            with self.assertRaises(HTTPError) as raised:
                self.post(f"{base_url}/actions/import-all", {"token": "wrong"})
            self.assertEqual(raised.exception.code, 400)

            with self.post(
                f"{base_url}/actions/import-all",
                {"token": "test-token"},
            ) as response:
                body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Manual artifact sync imported 1 set", body)
            self.assertIn("imported model", body)
            self.assertNotIn('action="/actions/import-all"', body)

    def test_delete_model_lmstudio_requires_confirm_then_uses_trash(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lmstudio_root = tmp_path / "lmstudio"
            model_dir = lmstudio_root / "publisher" / "Model"
            model_dir.mkdir(parents=True)
            (model_dir / "model.safetensors").write_text("weights", encoding="utf-8")
            model = {
                "runtime": "LM Studio",
                "model_id": "publisher/Model",
                "display_name": "Model",
                "status": "filesystem_only",
                "source_path": "publisher/Model",
                "local_path": str(model_dir),
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }
            refresh_calls = []

            def fake_refresh(_timeout=5):
                refresh_calls.append(True)
                return result

            def fake_run(command, **_kwargs):
                return SimpleNamespace(returncode=0, stdout="trashed", stderr="", args=command)

            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with (
                mock.patch.object(server, "LMSTUDIO_MODELS_ROOT", lmstudio_root),
                mock.patch.object(server, "_refresh_inventory", fake_refresh),
                mock.patch("model_dashboard.removal.platform.system", return_value="Darwin"),
                mock.patch("model_dashboard.removal.subprocess.run", side_effect=fake_run) as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)

                with self.post(
                    f"{base_url}/actions/delete-model",
                    {"token": "test-token", "remove_key": remove_key},
                ) as response:
                    confirm_body = response.read().decode("utf-8")

                self.assertEqual(response.status, 200)
                self.assertIn("Confirm Model Removal", confirm_body)
                self.assertIn(str(model_dir), confirm_body)
                run.assert_not_called()

                with self.post(
                    f"{base_url}/actions/delete-model",
                    {
                        "token": "test-token",
                        "remove_key": remove_key,
                        "confirm_delete": "yes",
                    },
                ) as response:
                    result_body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Model Removal succeeded", result_body)
            self.assertGreaterEqual(len(refresh_calls), 2)
            command = run.call_args.args[0]
            self.assertEqual(command[0], "osascript")
            self.assertEqual(command[1], "-l")
            self.assertEqual(command[2], "JavaScript")
            self.assertIn("trashItemAtURLResultingItemURLError", command[4])
            self.assertNotIn("rm", command)

    def test_delete_model_lmstudio_file_path_trashes_parent_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lmstudio_root = tmp_path / "lmstudio"
            model_dir = lmstudio_root / "publisher" / "Model"
            model_dir.mkdir(parents=True)
            weight_file = model_dir / "model.gguf"
            weight_file.write_text("weights", encoding="utf-8")
            model = {
                "runtime": "LM Studio",
                "model_id": "publisher/Model",
                "display_name": "Model",
                "status": "indexed",
                "source_path": str(weight_file),
                "local_path": str(weight_file),
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }

            def fake_run(command, **_kwargs):
                return SimpleNamespace(returncode=0, stdout="trashed", stderr="", args=command)

            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with (
                mock.patch.object(server, "LMSTUDIO_MODELS_ROOT", lmstudio_root),
                mock.patch.object(server, "_refresh_inventory", lambda _timeout=5: result),
                mock.patch("model_dashboard.removal.platform.system", return_value="Darwin"),
                mock.patch("model_dashboard.removal.subprocess.run", side_effect=fake_run) as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)

                with self.post(
                    f"{base_url}/actions/delete-model",
                    {"token": "test-token", "remove_key": remove_key},
                ) as response:
                    confirm_body = response.read().decode("utf-8")

                self.assertIn(str(model_dir), confirm_body)
                self.assertNotIn(str(weight_file), confirm_body)
                run.assert_not_called()

                with self.post(
                    f"{base_url}/actions/delete-model",
                    {
                        "token": "test-token",
                        "remove_key": remove_key,
                        "confirm_delete": "yes",
                    },
                ) as response:
                    result_body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Model Removal succeeded", result_body)
            command = run.call_args.args[0]
            self.assertEqual(command[0], "osascript")
            self.assertEqual(command[1], "-l")
            self.assertEqual(command[2], "JavaScript")
            self.assertIn(str(model_dir), command[4])
            self.assertNotIn(str(weight_file), command[4])
            self.assertIn("trashItemAtURLResultingItemURLError", command[4])

    def test_delete_model_lmstudio_missing_path_is_refused_before_osascript(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lmstudio_root = tmp_path / "lmstudio"
            model_dir = lmstudio_root / "publisher" / "Model"
            model = {
                "runtime": "LM Studio",
                "model_id": "publisher/Model",
                "display_name": "Model",
                "status": "filesystem_only",
                "source_path": "publisher/Model",
                "local_path": str(model_dir),
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)

            with (
                mock.patch.object(server, "LMSTUDIO_MODELS_ROOT", lmstudio_root),
                mock.patch.object(server, "_refresh_inventory", lambda _timeout=5: result),
                mock.patch("model_dashboard.removal.subprocess.run") as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)
                with self.assertRaises(HTTPError) as raised:
                    self.post(
                        f"{base_url}/actions/delete-model",
                        {
                            "token": "test-token",
                            "remove_key": remove_key,
                            "confirm_delete": "yes",
                        },
                    )

            self.assertEqual(raised.exception.code, 400)
            run.assert_not_called()

    def test_delete_model_ollama_uses_ollama_rm(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ollama_root = tmp_path / "ollama"
            model = {
                "runtime": "Ollama",
                "model_id": "qwen3:30b",
                "display_name": "qwen3:30b",
                "status": "installed",
                "source_path": "",
                "local_path": "",
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }

            def fake_run(command, **_kwargs):
                return SimpleNamespace(returncode=0, stdout="deleted", stderr="", args=command)

            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with (
                mock.patch.object(server, "OLLAMA_MODELS_ROOT", ollama_root),
                mock.patch.object(server, "_refresh_inventory", lambda _timeout=5: result),
                mock.patch("model_dashboard.removal.shutil.which", return_value="/bin/ollama"),
                mock.patch("model_dashboard.removal.subprocess.run", side_effect=fake_run) as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)
                with self.post(
                    f"{base_url}/actions/delete-model",
                    {
                        "token": "test-token",
                        "remove_key": remove_key,
                        "confirm_delete": "yes",
                    },
                ) as response:
                    body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Model Removal succeeded", body)
            self.assertEqual(run.call_args.args[0], ("/bin/ollama", "rm", "qwen3:30b"))

    def test_delete_model_mlx_requires_confirm_then_trashes_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hf_root = tmp_path / "hub"
            snapshot = hf_root / "models--mlx-community--Qwen" / "snapshots" / "abc123"
            snapshot.mkdir(parents=True)
            (snapshot / "config.json").write_text("{}", encoding="utf-8")
            (snapshot / "model.safetensors").write_text("weights", encoding="utf-8")
            model = {
                "runtime": "MLX-LM",
                "model_id": str(snapshot),
                "display_name": "mlx-community/Qwen",
                "status": "cached",
                "source_path": "mlx-community/Qwen",
                "local_path": str(snapshot),
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }

            def fake_run(command, **_kwargs):
                return SimpleNamespace(returncode=0, stdout="trashed", stderr="", args=command)

            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with (
                mock.patch.object(server, "HF_HUB_CACHE_ROOT", hf_root),
                mock.patch.object(server, "_refresh_inventory", lambda _timeout=5: result),
                mock.patch("model_dashboard.removal.platform.system", return_value="Darwin"),
                mock.patch("model_dashboard.removal.subprocess.run", side_effect=fake_run) as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)

                with self.post(
                    f"{base_url}/actions/delete-model",
                    {"token": "test-token", "remove_key": remove_key},
                ) as response:
                    confirm_body = response.read().decode("utf-8")

                self.assertIn("Confirm Model Removal", confirm_body)
                self.assertIn(str(snapshot), confirm_body)
                self.assertIn(str(hf_root), confirm_body)
                run.assert_not_called()

                with self.post(
                    f"{base_url}/actions/delete-model",
                    {
                        "token": "test-token",
                        "remove_key": remove_key,
                        "confirm_delete": "yes",
                    },
                ) as response:
                    body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("Model Removal succeeded", body)
            command = run.call_args.args[0]
            self.assertEqual(command[:3], ("osascript", "-l", "JavaScript"))
            self.assertIn(str(snapshot), command[4])
            self.assertIn("trashItemAtURLResultingItemURLError", command[4])
            self.assertNotIn("rm", command)

    def test_delete_model_mlx_refuses_snapshot_outside_hf_cache_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hf_root = tmp_path / "hub"
            outside = tmp_path / "outside" / "models--mlx-community--Qwen" / "snapshots" / "abc123"
            outside.mkdir(parents=True)
            (outside / "config.json").write_text("{}", encoding="utf-8")
            (outside / "model.safetensors").write_text("weights", encoding="utf-8")
            model = {
                "runtime": "MLX-LM",
                "model_id": str(outside),
                "display_name": "mlx-community/Qwen",
                "status": "cached",
                "source_path": "mlx-community/Qwen",
                "local_path": str(outside),
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)

            with (
                mock.patch.object(server, "HF_HUB_CACHE_ROOT", hf_root),
                mock.patch.object(server, "_refresh_inventory", lambda _timeout=5: result),
                mock.patch("model_dashboard.removal.subprocess.run") as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)
                with self.assertRaises(HTTPError) as raised:
                    self.post(
                        f"{base_url}/actions/delete-model",
                        {
                            "token": "test-token",
                            "remove_key": remove_key,
                            "confirm_delete": "yes",
                        },
                    )

            self.assertEqual(raised.exception.code, 400)
            run.assert_not_called()

    def test_delete_model_refuses_out_of_root_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lmstudio_root = tmp_path / "lmstudio"
            outside = tmp_path / "outside" / "Model"
            outside.mkdir(parents=True)
            (outside / "model.safetensors").write_text("weights", encoding="utf-8")
            model = {
                "runtime": "LM Studio",
                "model_id": "publisher/Model",
                "display_name": "Model",
                "status": "filesystem_only",
                "source_path": "publisher/Model",
                "local_path": str(outside),
            }
            result = {
                "checked_at": "2026-06-18T10:00:00-07:00",
                "checks": [],
                "models": [model],
            }
            db_path = tmp_path / "dashboard.sqlite"
            db.init_db(db_path, reset=True)

            with (
                mock.patch.object(server, "LMSTUDIO_MODELS_ROOT", lmstudio_root),
                mock.patch.object(server, "_refresh_inventory", lambda _timeout=5: result),
                mock.patch("model_dashboard.removal.subprocess.run") as run,
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_delete_actions=True,
                )
                self.post(f"{base_url}/actions/refresh-inventory", {"token": "test-token"}).read()
                remove_key = server._inventory_model_key(model)
                with self.assertRaises(HTTPError) as raised:
                    self.post(
                        f"{base_url}/actions/delete-model",
                        {
                            "token": "test-token",
                            "remove_key": remove_key,
                            "confirm_delete": "yes",
                        },
                    )

            self.assertEqual(raised.exception.code, 400)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
