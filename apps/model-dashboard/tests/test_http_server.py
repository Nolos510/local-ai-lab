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
            self.assertIn("Lab Dashboard", body)

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

            with (
                mock.patch.object(server, "_refresh_inventory", return_value=result),
                mock.patch.object(server, "CANDIDATE_REGISTRY_PATH", tmp_path / "missing.csv"),
                mock.patch.object(server, "LOCAL_INVENTORY_REGISTRY_PATH", overlay_path),
            ):
                base_url = self.start_server(
                    db_path,
                    action_token="test-token",
                    enable_run_tests=True,
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
            manifest_path = (
                ollama_root / "manifests" / "registry.ollama.ai" / "library" / "qwen3" / "30b"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text("manifest", encoding="utf-8")
            model = {
                "runtime": "Ollama",
                "model_id": "qwen3:30b",
                "display_name": "qwen3:30b",
                "status": "installed",
                "source_path": "",
                "local_path": str(manifest_path),
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
