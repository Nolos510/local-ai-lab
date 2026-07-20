import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard.components import _runtime_health_panel  # noqa: E402
from model_dashboard.runtime_health import runtime_health_snapshot  # noqa: E402


class RuntimeHealthTests(unittest.TestCase):
    def start_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.server.requests.append(
                    {"path": self.path, "authorization": self.headers.get("Authorization")}
                )
                if self.path == "/v1/models":
                    body = json.dumps(
                        {
                            "data": [
                                {"id": "primary-local"},
                                {"id": "reviewer-local"},
                            ]
                        }
                    ).encode()
                    status = 200
                elif self.path == "/readyz":
                    body = b"ready"
                    status = 200
                else:
                    body = b"not found"
                    status = 404
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.requests = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server

    def test_snapshot_checks_local_models_once_qdrant_and_native_commands(self):
        server = self.start_server()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1"
        qdrant = f"http://127.0.0.1:{server.server_port}"
        try:
            with mock.patch.dict(os.environ, {"LM_API_TOKEN": "private-token"}):
                result = runtime_health_snapshot(
                    enable_score_actions=True,
                    judge_endpoint=endpoint,
                    judge_model="primary-local",
                    reviewer_endpoint=endpoint,
                    reviewer_model="reviewer-local",
                    qdrant_url=qdrant,
                    command_finder=lambda name: "/safe/bin/lms" if name == "lms" else None,
                )
        finally:
            server.shutdown()
            server.server_close()

        by_name = {row["name"]: row for row in result["rows"]}
        self.assertEqual(result["overall"], "ready")
        self.assertEqual(by_name["Primary judge"]["status"], "ready")
        self.assertEqual(by_name["Independent reviewer"]["status"], "ready")
        self.assertEqual(by_name["Qdrant"]["status"], "ready")
        self.assertEqual(by_name["LM Studio CLI"]["status"], "ready")
        self.assertEqual(by_name["Ollama CLI"]["status"], "optional")
        self.assertEqual(
            sum(request["path"] == "/v1/models" for request in server.requests),
            1,
        )
        self.assertEqual(
            next(
                request["authorization"]
                for request in server.requests
                if request["path"] == "/v1/models"
            ),
            "Bearer private-token",
        )
        self.assertNotIn("private-token", repr(result))
        self.assertNotIn("/safe/bin", repr(result))

    def test_snapshot_rejects_credentialed_or_non_loopback_urls_without_leaking(self):
        result = runtime_health_snapshot(
            enable_score_actions=True,
            judge_endpoint="http://user:secret@127.0.0.1:1234/v1?token=abc",
            judge_model="primary-local",
            reviewer_endpoint="https://example.com/v1/private",
            reviewer_model="reviewer-local",
            qdrant_url="http://user:secret@127.0.0.1:6333/private?token=abc",
            command_finder=lambda _name: None,
        )

        self.assertEqual(result["overall"], "action_needed")
        rendered = repr(result)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("token=abc", rendered)
        self.assertNotIn("example.com", rendered)

    def test_disabled_score_actions_do_not_probe_model_endpoint(self):
        server = self.start_server()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1"
        try:
            result = runtime_health_snapshot(
                enable_score_actions=False,
                judge_endpoint=endpoint,
                judge_model="primary-local",
                reviewer_endpoint=endpoint,
                reviewer_model="reviewer-local",
                qdrant_url=f"http://127.0.0.1:{server.server_port}",
                command_finder=lambda _name: None,
            )
        finally:
            server.shutdown()
            server.server_close()

        model_rows = result["rows"][:2]
        self.assertEqual([row["status"] for row in model_rows], ["disabled", "disabled"])
        self.assertFalse(any(request["path"] == "/v1/models" for request in server.requests))

    def test_health_panel_renders_state_and_remediation(self):
        html = _runtime_health_panel(
            {
                "action_needed": 1,
                "rows": [
                    {
                        "name": "Primary judge",
                        "status": "action_needed",
                        "detail": "Configured model is missing.",
                        "action": "Load the model.",
                    }
                ],
            }
        )

        self.assertIn("Local Readiness", html)
        self.assertIn("1 required local check needs attention", html)
        self.assertIn("Configured model is missing", html)
        self.assertIn("uv run local-ai-lab doctor", html)


if __name__ == "__main__":
    unittest.main()
