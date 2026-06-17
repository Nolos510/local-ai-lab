import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402


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

    def test_model_action_is_refused_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            base_url = self.start_server(db_path, action_token="test-token")

            with self.assertRaises(HTTPError) as raised:
                self.post(
                    f"{base_url}/actions/remove-ollama-model",
                    {"token": "test-token", "model_id": "qwen3:8b"},
                )

            self.assertEqual(raised.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
