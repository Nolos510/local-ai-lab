from __future__ import annotations

import io
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlencode

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR.parents[1]
SRC_DIR = REPO_ROOT / "src"
CATALOG_DIR = REPO_ROOT / "data" / "growth_registry"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(SRC_DIR))

from model_dashboard import db, server  # noqa: E402
from model_dashboard.pages import growth as growth_page  # noqa: E402


def fake_plan(*, high_risk=False):
    return {
        "operation": "install",
        "target": "ext-semgrep-mcp",
        "host": "codex",
        "plugin_id": "safe-plugin",
        "marketplace": "official-marketplace",
        "marketplace_source": "https://github.com/openai/official-plugins",
        "marketplace_revision": "a" * 40,
        "reviewed_version": "1.2.3",
        "live_version": "1.2.3",
        "scope": "user",
        "components": ["skills", "mcp_servers"],
        "auth_policy": "No credentials are granted by installation.",
        "data_scope": "Only a selected non-private fixture.",
        "high_risk": high_risk,
        "data_scope_ack_required": high_risk,
        "threat_review_artifact": (
            "reports/growth/safe-plugin-threat-review.md" if high_risk else None
        ),
        "risk_facts": {
            "code_exec": "&lt;script&gt;untrusted&lt;/script&gt;",
            "fs": "Selected repository only.",
        },
        "argv": ["codex", "plugin", "add", "safe-plugin@official-marketplace"],
        "rollback_argv": [
            "codex",
            "plugin",
            "remove",
            "safe-plugin@official-marketplace",
        ],
        "pin_enforcement": "immutable marketplace revision",
        "fingerprint": "f" * 64,
    }


class FakeInstallService:
    def __init__(self, *, high_risk=False, execute_hook=None):
        self.high_risk = high_risk
        self.execute_hook = execute_hook
        self.preflight_calls = []
        self.execute_calls = []

    def preflight(self, **kwargs):
        self.preflight_calls.append(kwargs)
        plan = fake_plan(high_risk=self.high_risk)
        plan["operation"] = kwargs["operation"]
        plan["argv"][2] = "add" if kwargs["operation"] == "install" else "remove"
        return {
            "plan": plan,
            "nonce": "N" * 32,
            "expires_at": 1234.0,
            "dry_run": False,
        }

    def execute(self, **kwargs):
        self.execute_calls.append(kwargs)
        if self.execute_hook:
            return self.execute_hook(**kwargs)
        kwargs["stage"]("installing", 1, 3)
        kwargs["stage"]("verifying", 2, 3)
        kwargs["stage"]("complete", 3, 3)
        return {"outcome": "success"}


class GrowthInstallDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.state = self.repo / ".local-ai-lab" / "growth-state-v1.json"
        self.database = self.repo / "dashboard.sqlite"
        db.init_db(self.database, reset=True)

    def handler(
        self,
        service,
        *,
        enabled=True,
        coordinator=None,
        action_token="growth-action-token",
    ):
        return server.make_handler(
            self.database,
            action_token=action_token,
            enable_inventory_refresh=False,
            enable_growth_installs=enabled,
            growth_catalog_dir=CATALOG_DIR,
            growth_state_path=self.state,
            growth_repo_root=self.repo,
            growth_install_service=service,
            growth_job_coordinator=coordinator,
            local_inventory_registry_path=self.repo / "local-inventory.csv",
        )

    def dispatch(
        self,
        service,
        path,
        form,
        *,
        enabled=True,
        coordinator=None,
        client_host="127.0.0.1",
        host="127.0.0.1:8765",
        origin=None,
        content_length=None,
        configured_token="growth-action-token",
    ):
        handler_type = self.handler(
            service,
            enabled=enabled,
            coordinator=coordinator,
            action_token=configured_token,
        )
        handler = object.__new__(handler_type)
        payload = urlencode(form).encode()
        handler.path = path
        handler.headers = {
            "Content-Length": str(len(payload)) if content_length is None else content_length,
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": host,
        }
        if origin is not None:
            handler.headers["Origin"] = origin
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.client_address = (client_host, 12345)
        statuses = []
        headers = []
        handler.send_response = statuses.append
        handler.send_header = lambda name, value: headers.append((name, value))
        handler.end_headers = lambda: None
        handler.do_POST()
        return statuses, headers, handler.wfile.getvalue().decode()

    @staticmethod
    def preflight_form(**overrides):
        form = {
            "token": "growth-action-token",
            "target": "ext-semgrep-mcp",
            "scope": "user",
            "operation": "install",
        }
        form.update(overrides)
        return form

    def test_installs_default_off_but_progress_authority_is_separate(self):
        service = FakeInstallService()
        statuses, headers, html = self.dispatch(
            service,
            "/actions/growth-install-preflight",
            self.preflight_form(),
            enabled=False,
        )
        self.assertEqual([403], statuses)
        self.assertIn("Growth installs disabled", html)
        self.assertEqual([], service.preflight_calls)
        self.assertIn(("Cache-Control", "no-store"), headers)

    def test_enabled_installs_fail_closed_without_configured_csrf_token(self):
        service = FakeInstallService()
        statuses, _headers, html = self.dispatch(
            service,
            "/actions/growth-install-preflight",
            self.preflight_form(token=""),
            configured_token="",
        )
        self.assertEqual([400], statuses)
        self.assertEqual([], service.preflight_calls)
        self.assertIn("blocked or failed safely", html)

    def test_preflight_shows_exact_bound_facts_and_escapes_all_text(self):
        service = FakeInstallService(high_risk=True)
        statuses, headers, html = self.dispatch(
            service,
            "/actions/growth-install-preflight",
            self.preflight_form(),
        )
        self.assertEqual([200], statuses)
        self.assertIn("https://github.com/openai/official-plugins", html)
        self.assertIn("official-marketplace", html)
        self.assertIn("1.2.3", html)
        self.assertIn("safe-plugin@official-marketplace", html)
        self.assertIn("Type the exact plugin id", html)
        self.assertIn("ack_data_scope", html)
        self.assertNotIn("<script>untrusted</script>", html)
        self.assertIn("&amp;lt;script&amp;gt;", html)
        self.assertIn(("Cache-Control", "no-store"), headers)

    def test_growth_install_posts_require_loopback_origin_csrf_and_capped_body(self):
        cases = [
            ({"token": "wrong"}, {}),
            ({}, {"client_host": "192.0.2.1"}),
            ({}, {"host": "evil.example"}),
            ({}, {"origin": "http://evil.example"}),
            ({}, {"content_length": "-1"}),
            ({}, {"content_length": "not-a-number"}),
            ({}, {"content_length": "5000"}),
        ]
        for form_changes, dispatch_changes in cases:
            with self.subTest(form_changes=form_changes, dispatch_changes=dispatch_changes):
                service = FakeInstallService()
                statuses, _headers, html = self.dispatch(
                    service,
                    "/actions/growth-install-preflight",
                    self.preflight_form(**form_changes),
                    **dispatch_changes,
                )
                self.assertEqual([400], statuses)
                self.assertEqual([], service.preflight_calls)
                self.assertIn("Growth action was blocked or failed safely", html)
                self.assertNotIn("evil.example", html)

    def test_one_background_job_is_serialized_and_status_has_steps_not_percent(self):
        entered = threading.Event()
        release = threading.Event()

        def block(**kwargs):
            kwargs["stage"]("installing", 1, 3)
            entered.set()
            self.assertTrue(release.wait(5))
            kwargs["stage"]("verifying", 2, 3)
            kwargs["stage"]("complete", 3, 3)
            return {"outcome": "success"}

        service = FakeInstallService(execute_hook=block)
        coordinator = server._GrowthJobCoordinator()
        execute_form = {
            "token": "growth-action-token",
            "nonce": "N" * 32,
            "target": "ext-semgrep-mcp",
            "scope": "user",
            "operation": "install",
            "yes": "yes",
        }
        statuses, _headers, html = self.dispatch(
            service,
            "/actions/growth-install-execute",
            execute_form,
            coordinator=coordinator,
        )
        self.assertEqual([202], statuses)
        self.assertTrue(entered.wait(5))
        self.assertIn("Step:", html)
        status_panel = html.split('<section class="panel growth-install-status"', 1)[1].split(
            "</section>", 1
        )[0]
        self.assertNotRegex(status_panel, r"\b\d+%")

        statuses, _headers, html = self.dispatch(
            service,
            "/actions/growth-install-execute",
            execute_form,
            coordinator=coordinator,
        )
        self.assertEqual([400], statuses)
        self.assertIn("blocked or failed safely", html)
        self.assertEqual(1, len(service.execute_calls))
        release.set()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            snapshot = next(iter(coordinator._statuses.values()))
            if snapshot["stage"] == "complete":
                break
            time.sleep(0.01)
        self.assertEqual("complete", snapshot["stage"])
        self.assertEqual("success", snapshot["outcome"])

    def test_raw_background_exception_never_reaches_status_html(self):
        done = threading.Event()

        def fail(**kwargs):
            done.set()
            raise RuntimeError("raw /Users/alice sk-private subprocess output")

        service = FakeInstallService(execute_hook=fail)
        coordinator = server._GrowthJobCoordinator()
        status = coordinator.start(
            service,
            operation="install",
            execute_kwargs={
                "nonce": "N" * 32,
                "target": "ext-semgrep-mcp",
                "scope": "user",
                "operation": "install",
                "yes": True,
                "allowed": True,
            },
        )
        self.assertTrue(done.wait(5))
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = coordinator.snapshot(status["job_id"])
            if status["stage"] == "failed":
                break
            time.sleep(0.01)
        html = growth_page._growth_job_status_page(status)
        self.assertNotIn("alice", html)
        self.assertNotIn("sk-private", html)
        self.assertNotIn("subprocess output", html)
        self.assertEqual("failed", status["outcome"])
        self.assertEqual(0, status["step"])

    def test_thread_start_failure_releases_job_reservation_and_is_sanitized(self):
        service = FakeInstallService()
        coordinator = server._GrowthJobCoordinator()
        with (
            mock.patch.object(
                server.threading.Thread,
                "start",
                side_effect=RuntimeError("raw /Users/alice sk-private thread error"),
            ),
            self.assertRaisesRegex(ValueError, "could not be started safely") as caught,
        ):
            coordinator.start(
                service,
                operation="install",
                execute_kwargs={"unused": True},
            )
        self.assertNotIn("alice", str(caught.exception))
        self.assertNotIn("sk-private", str(caught.exception))
        self.assertIsNone(caught.exception.__cause__)
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(coordinator._active_job_id)
        status = next(iter(coordinator._statuses.values()))
        self.assertEqual("failed", status["stage"])
        self.assertEqual("failed", status["outcome"])

    def test_discovery_inbox_is_render_only_and_double_escaped(self):
        private = self.repo / ".local-ai-lab"
        private.mkdir(mode=0o700)
        inbox = {
            "schema_version": "growth-inbox-v1",
            "items": [
                {
                    "id": "inbox-" + "a" * 20,
                    "source": "github",
                    "kind": "discovery",
                    "catalog_id": None,
                    "title": "&lt;script&gt;title&lt;/script&gt;",
                    "summary": "&lt;img src=x onerror=alert(1)&gt;",
                    "source_url": "https://github.com/official/safe",
                    "version": "v1.0.0",
                    "popularity": 999999,
                    "observed_at": "2026-07-21T19:00:00Z",
                    "review_state": "unreviewed",
                    "approval": "none",
                    "untrusted": True,
                }
            ],
            "reviews": [],
        }
        (private / "growth-inbox-v1.json").write_text(json.dumps(inbox), encoding="utf-8")
        with (
            mock.patch("subprocess.run") as run,
            mock.patch("urllib.request.urlopen") as open_url,
        ):
            html = growth_page._growth(
                {"view": ["inbox"]},
                catalog_dir=CATALOG_DIR,
                state_path=self.state,
                repo_root=self.repo,
                inbox_path=private / "growth-inbox-v1.json",
                enable_growth_installs=True,
            )
        run.assert_not_called()
        open_url.assert_not_called()
        self.assertIn("Discovery inbox", html)
        self.assertIn("Popularity is context only", html)
        self.assertIn("&amp;lt;script&amp;gt;", html)
        self.assertNotIn("<script>title</script>", html)
        self.assertIn("&amp;lt;img src=x onerror=alert(1)&amp;gt;", html)
        self.assertNotIn("<img src=x onerror=alert(1)>", html)


if __name__ == "__main__":
    unittest.main()
