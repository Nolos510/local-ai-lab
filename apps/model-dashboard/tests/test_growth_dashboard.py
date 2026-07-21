from __future__ import annotations

import io
import json
import shutil
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
REPO_ROOT = APP_DIR.parents[1]
CATALOG_DIR = REPO_ROOT / "data" / "growth_registry"
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402
from model_dashboard import growth as growth_data  # noqa: E402
from model_dashboard.pages import growth as growth_page  # noqa: E402


class GrowthDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo_root = Path(self.temp.name) / "repo"
        self.repo_root.mkdir()
        self.state_path = self.repo_root / ".local-ai-lab" / "growth-state-v1.json"
        self._write_artifact("skills/code-review/SKILL.md")
        self._write_artifact("reports/alice/credential-identifier.md")
        self._write_artifact("reports/growth/learning-proof.md")
        self.state = growth_data.empty_state()
        self.state["inventory"] = [
            self._inventory("code-review", "skill", "repo", "repo_skills", installed=True),
            self._inventory(
                "ext-context7",
                "mcp",
                "codex",
                "codex_mcp_cli",
                configured=True,
            ),
            self._inventory(
                "ln-hf-mcp-course",
                "learning",
                "repo",
                "repo_skills",
                available=True,
            ),
            self._inventory(
                "sk-private-token",
                "plugin",
                "codex",
                "codex_plugin_cli",
                installed=True,
            ),
            self._inventory(
                "alice-private",
                "skill",
                "repo",
                "repo_skills",
                installed=True,
            ),
        ]
        self.state["progress"] = [
            {
                "item_id": "skill-code-review",
                "status": "completed",
                "evidence": "reports/alice/credential-identifier.md",
            },
            {
                "item_id": "ln-hf-mcp-course",
                "status": "queued",
                "evidence": "reports/growth/learning-proof.md",
            },
        ]
        growth_data.write_state_atomic(
            self.state_path,
            self.state,
            repo_root=self.repo_root,
        )

    def _write_artifact(self, relative):
        path = self.repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
        return path

    @staticmethod
    def _inventory(
        item_id,
        kind,
        ecosystem,
        source,
        *,
        available=True,
        configured=False,
        installed=False,
        enabled=False,
        referenced=True,
        evidenced=False,
    ):
        return {
            "id": item_id,
            "kind": kind,
            "ecosystem": ecosystem,
            "source": source,
            "available": available,
            "configured": configured,
            "installed": installed,
            "enabled": enabled,
            "referenced": referenced,
            "evidenced": evidenced,
        }

    def render(self, query):
        return growth_page._growth(
            query,
            catalog_dir=CATALOG_DIR,
            state_path=self.state_path,
            repo_root=self.repo_root,
            action_token="test-action-token",
        )

    def test_each_view_renders_catalog_or_progress_with_sanitized_inventory(self):
        expected = {
            "skills": ("skill-code-review", "repo · repo_skills"),
            "extensions": ("ext-context7", "codex · codex_mcp_cli"),
            "learning": ("ln-hf-mcp-course", "repo · repo_skills"),
            "inbox": ("skill-code-review", "Progress inbox"),
        }
        with (
            mock.patch("subprocess.run") as run,
            mock.patch("urllib.request.urlopen") as open_url,
        ):
            for view, needles in expected.items():
                with self.subTest(view=view):
                    html = self.render({"view": [view]})
                    self.assertIn("Growth / Skills Lab", html)
                    self.assertIn("Compare cataloged skills", html)
                    self.assertNotIn("Compare reviewed skills", html)
                    self.assertIn('class="nav active" href="/growth" aria-current="page"', html)
                    self.assertIn("Saved sanitized inventory", html)
                    self.assertIn(needles[0], html)
                    self.assertIn(needles[1], html)
                    self.assertIn("Detected in saved inventory:", html)
                    self.assertIn("Evidence artifact exists now:", html)
                    self.assertIn("proof_artifact", html)
                    self.assertIn("next_action", html)
                    self.assertNotIn("<script src=", html)
                    self.assertNotRegex(html, r'<link[^>]+https?://')
        run.assert_not_called()
        open_url.assert_not_called()

    def test_role_effort_status_risk_and_evidence_filters_work(self):
        focused = self.render(
            {
                "view": ["skills"],
                "role": ["AIA"],
                "effort": ["1-3"],
                "status": ["Now"],
                "risk": ["review checks"],
                "evidence": ["evidenced"],
            }
        )
        self.assertIn("skill-code-review", focused)
        self.assertNotIn("skill-local-llm-eval", focused)

        risk = self.render(
            {
                "view": ["extensions"],
                "risk": ["Fetches documentation over the network"],
            }
        )
        self.assertIn("ext-context7", risk)
        self.assertNotIn("ext-semgrep-mcp", risk)

        slash_risk = self.render(
            {
                "view": ["extensions"],
                "risk": ["semgrep/mcp"],
            }
        )
        self.assertIn("ext-semgrep-mcp", slash_risk)
        self.assertNotIn("ext-context7", slash_risk)

        detected_not_evidenced = self.render(
            {
                "view": ["extensions"],
                "evidence": ["detected_not_evidenced"],
            }
        )
        self.assertIn("ext-context7", detected_not_evidenced)
        self.assertNotIn("ext-semgrep-mcp", detected_not_evidenced)

        inbox = self.render({"view": ["inbox"], "status": ["queued"]})
        self.assertIn("ln-hf-mcp-course", inbox)
        self.assertNotIn("skill-code-review", inbox)

    def test_risk_facts_and_review_state_render_verbatim_with_safe_prompt_tip(self):
        item = next(
            item
            for item in growth_data.load_catalogs(CATALOG_DIR)
            if item["id"] == "ext-context7"
        )
        html = self.render(
            {
                "view": ["extensions"],
                "risk": ["Fetches documentation over the network"],
            }
        )

        self.assertIn("metadata_reviewed", html)
        for field in growth_data.RISK_FIELDS:
            self.assertIn(f"<code>{field}</code>", html)
            self.assertIn(item["risk_facts"][field], html)
        self.assertIn("review prompt, not a verdict", html)
        self.assertIn('class="metric-tip" tabindex="0"', html)
        self.assertIn("Catalog source", html)
        self.assertNotIn("Reviewed public source", html)
        self.assertNotIn("low risk", html.lower())
        self.assertNotIn("safe to install", html.lower())

    def test_sorting_happens_before_growth_pagination(self):
        items = sorted(
            (
                item
                for item in growth_data.load_catalogs(CATALOG_DIR)
                if item["catalog_kind"] == "extension"
            ),
            key=lambda item: item["name"].casefold(),
            reverse=True,
        )
        expected = items[2:4]
        html = self.render(
            {
                "view": ["extensions"],
                "sort": ["item"],
                "dir": ["desc"],
                "page": ["2"],
                "page_size": ["2"],
            }
        )
        table = html.split('<table class="growth-table"', 1)[1].split("</table>", 1)[0]
        self.assertIn(expected[0]["id"], table)
        self.assertIn(expected[1]["id"], table)
        self.assertLess(table.index(expected[0]["id"]), table.index(expected[1]["id"]))
        self.assertIn('<th aria-sort="descending">', table)
        self.assertIn(f"showing 3-4 of {len(items)}", html)
        self.assertIn("Growth catalog pagination: previous page", html)
        self.assertIn("Growth catalog pagination: next page", html)

        priority_html = self.render(
            {
                "view": ["extensions"],
                "sort": ["priority"],
                "dir": ["asc"],
                "page_size": ["100"],
            }
        )
        priority_table = priority_html.split('<table class="growth-table"', 1)[1].split(
            "</table>", 1
        )[0]
        ordered_ids = (
            "ext-context7",
            "ext-hf-mcp",
            "ext-supabase-mcp",
            "ext-temporal",
            "ext-email",
        )
        positions = [priority_table.index(item_id) for item_id in ordered_ids]
        self.assertEqual(positions, sorted(positions))

    def test_a11y_external_asset_and_private_value_contracts(self):
        html = self.render(
            {
                "view": ["learning"],
                "risk": ["/Users/alice/sk-private-token"],
            }
        )
        switcher = html.split('aria-label="Growth views"', 1)[1].split("</nav>", 1)[0]
        self.assertEqual(1, switcher.count('aria-current="true"'))
        self.assertIn('href="/growth?view=learning" aria-current="true"', switcher)
        self.assertIn('class="skip-link" href="#main-content"', html)
        self.assertIn('<main id="main-content" tabindex="-1">', html)
        self.assertIn('<label for="growth-role">Role</label>', html)
        self.assertIn('<label for="growth-risk">Risk fact contains</label>', html)
        self.assertIn('method="post" action="/actions/growth-progress"', html)
        self.assertNotIn('action="/actions/growth-install"', html)
        self.assertNotIn('action="/actions/growth-remove"', html)
        self.assertNotIn("<script src=", html)
        self.assertNotRegex(html, r'<link[^>]+https?://')
        self.assertNotRegex(html, r'<(?:img|audio|video)[^>]+https?://')
        for private_value in (
            "/Users/alice",
            "alice-private",
            "sk-private-token",
            "credential-identifier",
        ):
            self.assertNotIn(private_value, html)
        aws_query_html = self.render(
            {"view": ["skills"], "risk": ["AKIA123456789012"]}
        )
        self.assertNotIn("AKIA123456789012", aws_query_html)

    def test_catalog_rejects_home_path_embedded_after_punctuation(self):
        catalog_copy = Path(self.temp.name) / "growth-registry"
        shutil.copytree(CATALOG_DIR, catalog_copy)
        skills_path = catalog_copy / "skills.json"
        payload = json.loads(skills_path.read_text(encoding="utf-8"))
        payload["items"][0]["risk_facts"]["fs"] = "path=/Users/alice/private"
        skills_path.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaises(growth_data.GrowthDataError) as raised:
            growth_data.load_catalogs(catalog_copy)
        self.assertNotIn("/Users/alice", str(raised.exception))

    def test_inventory_match_requires_a_compatible_kind(self):
        catalog_items = growth_data.load_catalogs(CATALOG_DIR)
        state = growth_data.empty_state()
        state["inventory"] = [
            self._inventory(
                "ext-context7",
                "skill",
                "repo",
                "repo_skills",
                installed=True,
            )
        ]
        growth_data.validate_state(state)

        views, unmatched_count = growth_data.item_views(
            catalog_items,
            state,
            repo_root=self.repo_root,
        )
        context7 = next(item for item in views if item["id"] == "ext-context7")
        self.assertFalse(context7["_detected"])
        self.assertEqual(1, unmatched_count)

    def test_malformed_private_state_error_never_echoes_raw_values(self):
        malformed = self.repo_root / ".local-ai-lab" / "malformed.json"
        malformed.parent.mkdir(exist_ok=True)
        malformed.write_text(
            '{"secret":"sk-super-private-value","home":"/Users/alice"}',
            encoding="utf-8",
        )
        with self.assertRaises(growth_data.GrowthDataError) as raised:
            growth_data.load_state(malformed)
        message = str(raised.exception)
        self.assertNotIn("sk-super-private-value", message)
        self.assertNotIn("/Users/alice", message)


class GrowthProgressHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo_root = Path(self.temp.name) / "repo"
        self.repo_root.mkdir()
        self.state_path = self.repo_root / ".local-ai-lab" / "growth-state-v1.json"
        evidence = self.repo_root / "reports" / "growth" / "proof.md"
        evidence.parent.mkdir(parents=True)
        evidence.write_text("proof\n", encoding="utf-8")
        self.database_path = self.repo_root / "dashboard.sqlite"
        db.init_db(self.database_path, reset=True)

    def start_server(self):
        handler = server.make_handler(
            self.database_path,
            action_token="growth-test-token",
            enable_inventory_refresh=False,
            growth_catalog_dir=CATALOG_DIR,
            growth_state_path=self.state_path,
            growth_repo_root=self.repo_root,
            local_inventory_registry_path=self.repo_root / "local-inventory.csv",
        )
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        except PermissionError as exc:
            self.skipTest(f"local bind unavailable in this environment: {exc}")
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        return f"http://127.0.0.1:{httpd.server_port}"

    @staticmethod
    def post(url, form):
        request = Request(
            url,
            data=urlencode(form).encode("utf-8"),
            method="POST",
        )
        return urlopen(request, timeout=5)

    def dispatch_progress(
        self,
        form,
        *,
        client_host="127.0.0.1",
        host_header="127.0.0.1:8765",
        origin=None,
    ):
        handler_type = server.make_handler(
            self.database_path,
            action_token="growth-test-token",
            enable_inventory_refresh=False,
            growth_catalog_dir=CATALOG_DIR,
            growth_state_path=self.state_path,
            growth_repo_root=self.repo_root,
            local_inventory_registry_path=self.repo_root / "local-inventory.csv",
        )
        handler = object.__new__(handler_type)
        payload = urlencode(form).encode("utf-8")
        handler.path = "/actions/growth-progress"
        handler.headers = {
            "Content-Length": str(len(payload)),
            "Host": host_header,
        }
        if origin is not None:
            handler.headers["Origin"] = origin
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.client_address = (client_host, 12345)
        statuses = []
        handler.send_response = statuses.append
        handler.send_header = lambda _name, _value: None
        handler.end_headers = lambda: None
        handler.do_POST()
        return statuses, handler.wfile.getvalue().decode("utf-8")

    def test_progress_post_dispatch_requires_token_and_loopback(self):
        form = {
            "token": "growth-test-token",
            "item_id": "skill-code-review",
            "status": "in_progress",
            "evidence": "reports/growth/proof.md",
            "view": "skills",
        }
        statuses, html = self.dispatch_progress(form)
        self.assertEqual([200], statuses)
        self.assertIn("Personal progress updated: skill-code-review", html)
        state = growth_data.load_state(self.state_path)
        self.assertEqual("in_progress", state["progress"][0]["status"])

        before = self.state_path.read_bytes()
        statuses, _html = self.dispatch_progress({**form, "token": "wrong"})
        self.assertEqual([400], statuses)
        self.assertEqual(before, self.state_path.read_bytes())
        statuses, _html = self.dispatch_progress(form, client_host="192.0.2.1")
        self.assertEqual([400], statuses)
        self.assertEqual(before, self.state_path.read_bytes())
        statuses, _html = self.dispatch_progress(form, host_header="evil.example")
        self.assertEqual([400], statuses)
        self.assertEqual(before, self.state_path.read_bytes())
        statuses, _html = self.dispatch_progress(
            form,
            origin="http://evil.example",
        )
        self.assertEqual([400], statuses)
        self.assertEqual(before, self.state_path.read_bytes())

    def test_growth_get_route_dispatches_without_a_server_bind(self):
        handler_type = server.make_handler(
            self.database_path,
            action_token="growth-test-token",
            growth_catalog_dir=CATALOG_DIR,
            growth_state_path=self.state_path,
            growth_repo_root=self.repo_root,
            local_inventory_registry_path=self.repo_root / "local-inventory.csv",
        )
        handler = object.__new__(handler_type)
        with db.connect(self.database_path) as conn:
            html = handler._route("/growth", {"view": ["extensions"]}, conn)
        self.assertIn("Growth / Skills Lab", html)
        self.assertIn("ext-context7", html)
        self.assertIn('href="/growth" aria-current="page"', html)

    def test_growth_get_rejects_non_loopback_host_before_exposing_token(self):
        handler_type = server.make_handler(
            self.database_path,
            action_token="growth-test-token",
            growth_catalog_dir=CATALOG_DIR,
            growth_state_path=self.state_path,
            growth_repo_root=self.repo_root,
            local_inventory_registry_path=self.repo_root / "local-inventory.csv",
        )
        handler = object.__new__(handler_type)
        handler.path = "/growth?view=skills"
        handler.headers = {"Host": "evil.example"}
        handler.wfile = io.BytesIO()
        statuses = []
        handler.send_response = statuses.append
        handler.send_header = lambda _name, _value: None
        handler.end_headers = lambda: None
        handler.do_GET()
        html = handler.wfile.getvalue().decode("utf-8")

        self.assertEqual([400], statuses)
        self.assertIn("requires a loopback Host", html)
        self.assertNotIn("growth-test-token", html)

    def test_progress_update_is_catalog_gated_and_atomic_without_a_server_bind(self):
        catalog_items = growth_data.load_catalogs(CATALOG_DIR)
        replacements = []
        real_replace = growth_data.os.replace

        def spy_replace(source, target, **kwargs):
            replacements.append((source, target, kwargs))
            return real_replace(source, target, **kwargs)

        with mock.patch.object(growth_data.os, "replace", spy_replace):
            growth_data.update_progress(
                self.state_path,
                catalog_items=catalog_items,
                item_id="skill-code-review",
                status="queued",
                evidence="reports/growth/proof.md",
                repo_root=self.repo_root,
            )

        self.assertEqual("growth-state-v1.json", replacements[0][1])
        self.assertRegex(replacements[0][0], r"^\.growth-state-v1-[0-9a-f]+\.tmp$")
        self.assertEqual(
            replacements[0][2]["src_dir_fd"],
            replacements[0][2]["dst_dir_fd"],
        )
        self.assertEqual("queued", growth_data.load_state(self.state_path)["progress"][0]["status"])
        before = self.state_path.read_bytes()
        with self.assertRaises(growth_data.GrowthDataError):
            growth_data.update_progress(
                self.state_path,
                catalog_items=catalog_items,
                item_id="unreviewed-private-item",
                status="completed",
                evidence=None,
                repo_root=self.repo_root,
            )
        self.assertEqual(before, self.state_path.read_bytes())

    def test_progress_post_is_token_gated_atomic_and_catalog_read_only(self):
        base_url = self.start_server()
        catalog_before = {
            path.name: path.read_bytes() for path in CATALOG_DIR.glob("*.json")
        }
        replacements = []
        real_replace = growth_data.os.replace

        def spy_replace(source, target, **kwargs):
            replacements.append((source, target, kwargs))
            return real_replace(source, target, **kwargs)

        with mock.patch.object(growth_data.os, "replace", spy_replace), self.post(
            f"{base_url}/actions/growth-progress",
            {
                "token": "growth-test-token",
                "item_id": "skill-code-review",
                "status": "completed",
                "evidence": "reports/growth/proof.md",
                "view": "skills",
            },
        ) as response:
            html = response.read().decode("utf-8")

        self.assertEqual(200, response.status)
        self.assertIn("Personal progress updated: skill-code-review", html)
        self.assertTrue(replacements)
        self.assertEqual("growth-state-v1.json", replacements[0][1])
        self.assertRegex(replacements[0][0], r"^\.growth-state-v1-[0-9a-f]+\.tmp$")
        self.assertEqual(
            replacements[0][2]["src_dir_fd"],
            replacements[0][2]["dst_dir_fd"],
        )
        state = growth_data.load_state(self.state_path)
        self.assertEqual(
            [
                {
                    "item_id": "skill-code-review",
                    "status": "completed",
                    "evidence": "reports/growth/proof.md",
                }
            ],
            state["progress"],
        )
        self.assertEqual(0o700, self.state_path.parent.stat().st_mode & 0o777)
        self.assertEqual(0o600, self.state_path.stat().st_mode & 0o777)
        self.assertFalse(list(self.state_path.parent.glob("*.tmp")))
        self.assertEqual(
            catalog_before,
            {path.name: path.read_bytes() for path in CATALOG_DIR.glob("*.json")},
        )
        self.assertEqual([self.state_path], list(self.state_path.parent.iterdir()))

        before = self.state_path.read_bytes()
        with self.assertRaises(HTTPError) as raised:
            self.post(
                f"{base_url}/actions/growth-progress",
                {
                    "token": "wrong-token",
                    "item_id": "skill-code-review",
                    "status": "skipped",
                },
            )
        self.assertEqual(400, raised.exception.code)
        self.assertEqual(before, self.state_path.read_bytes())

    def test_state_writer_refuses_any_non_ignored_target(self):
        catalog_target = self.repo_root / "data" / "growth_registry" / "skills.json"
        catalog_target.parent.mkdir(parents=True)
        catalog_target.write_text("catalog sentinel\n", encoding="utf-8")
        with self.assertRaises(growth_data.GrowthDataError):
            growth_data.write_state_atomic(
                catalog_target,
                growth_data.empty_state(),
                repo_root=self.repo_root,
            )
        self.assertEqual("catalog sentinel\n", catalog_target.read_text(encoding="utf-8"))

    def test_state_writer_refuses_a_symlinked_private_directory(self):
        fresh_root = Path(self.temp.name) / "fresh-repo"
        fresh_root.mkdir()
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (fresh_root / ".local-ai-lab").symlink_to(outside, target_is_directory=True)
        target = fresh_root / ".local-ai-lab" / "growth-state-v1.json"

        with self.assertRaises(growth_data.GrowthDataError):
            growth_data.write_state_atomic(
                target,
                growth_data.empty_state(),
                repo_root=fresh_root,
            )
        self.assertFalse((outside / "growth-state-v1.json").exists())


if __name__ == "__main__":
    unittest.main()
