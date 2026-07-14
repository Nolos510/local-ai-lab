import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, server  # noqa: E402

FIXTURE_RUNS = APP_DIR / "fixtures" / "artifact_runs"


class ArtifactResponseTests(unittest.TestCase):
    def _render(self, callback):
        with tempfile.TemporaryDirectory() as tmp:
            database_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(database_path, reset=True)
            with db.connect(database_path) as conn:
                return callback(conn, database_path)

    def test_artifact_detail_renders_escaped_collapsible_prompt_rows(self):
        def render(conn, database_path):
            with mock.patch("subprocess.run") as run:
                html = server._artifact_detail(
                    conn,
                    "s1-run-a",
                    registry_path=database_path.parent / "missing-candidates.csv",
                    database_path=database_path,
                    eval_results_dir=FIXTURE_RUNS,
                )
            run.assert_not_called()
            return html

        html = self._render(render)

        self.assertIn("Per-prompt Responses", html)
        self.assertIn("S1-PROMPT-001", html)
        self.assertIn(">12 ms<", html)
        self.assertIn(">7<", html)
        self.assertIn(">9<", html)
        self.assertIn('class="response-details"', html)
        self.assertIn("Expand response", html)
        self.assertIn(
            "&lt;script&gt;alert(&quot;fixture&quot;)&lt;/script&gt;",
            html,
        )
        self.assertNotIn('<script>alert("fixture")</script>', html)
        self.assertIn("Skipped 1 unreadable or incomplete JSONL line.", html)
        self.assertIn("—", html)
        self.assertNotIn(str(FIXTURE_RUNS), html)

    def test_ab_viewer_pairs_shared_prompt_responses_side_by_side(self):
        def render(conn, _database_path):
            with mock.patch("subprocess.run") as run:
                html = server._artifact_compare(
                    conn,
                    {"run_a": ["s1-run-a"], "run_b": ["s1-run-b"]},
                    eval_results_dir=FIXTURE_RUNS,
                )
            run.assert_not_called()
            return html

        html = self._render(render)

        self.assertIn("A/B Response Viewer", html)
        self.assertIn("s1-shared-prompts", html)
        self.assertIn("S1 Model A", html)
        self.assertIn("S1 Model B", html)
        self.assertIn('class="ab-responses-table"', html)
        self.assertEqual(html.count('data-prompt-id="S1-PROMPT-001"'), 1)
        self.assertEqual(html.count('data-prompt-id="S1-PROMPT-002"'), 1)
        self.assertIn("Response from model A.", html)
        self.assertIn("Response from model B for prompt one.", html)
        self.assertIn("s1-run-a: Skipped 1 unreadable or incomplete JSONL line.", html)
        self.assertIn("Latency: 20 ms", html)
        self.assertIn("Input tokens: 8", html)
        self.assertIn("Output tokens: 11", html)

    def test_missing_raw_artifact_has_honest_detail_and_compare_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_root = Path(tmp) / "artifact-runs"
            for run_id in ("run-with-raw", "run-without-raw"):
                run_dir = artifact_root / run_id
                run_dir.mkdir(parents=True)
                (run_dir / "metadata.json").write_text(
                    json.dumps(
                        {
                            "benchmark_run_id": run_id,
                            "prompt_set_id": "empty-state-prompts",
                            "model": {"model_name": run_id},
                        }
                    ),
                    encoding="utf-8",
                )
            (artifact_root / "run-with-raw" / "raw_responses.jsonl").write_text(
                json.dumps(
                    {
                        "prompt_set_id": "empty-state-prompts",
                        "prompt_id": "EMPTY-001",
                        "latency_ms": None,
                        "input_tokens": None,
                        "output_tokens": None,
                        "raw_response": "Only captured response.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            def render(conn, database_path):
                detail_html = server._artifact_detail(
                    conn,
                    "run-without-raw",
                    registry_path=database_path.parent / "missing-candidates.csv",
                    eval_results_dir=artifact_root,
                )
                compare_html = server._artifact_compare(
                    conn,
                    {"run_a": ["run-with-raw"], "run_b": ["run-without-raw"]},
                    eval_results_dir=artifact_root,
                )
                return detail_html, compare_html

            detail_html, compare_html = self._render(render)

        self.assertIn("No raw response artifact is available for this run.", detail_html)
        self.assertIn("No raw response artifact is available for run-without-raw.", compare_html)
        self.assertIn("No response captured for this prompt.", compare_html)
        self.assertIn("—", compare_html)

    def test_artifact_views_use_inline_local_assets_only(self):
        def render(conn, database_path):
            detail_html = server._artifact_detail(
                conn,
                "s1-run-a",
                registry_path=database_path.parent / "missing-candidates.csv",
                eval_results_dir=FIXTURE_RUNS,
            )
            compare_html = server._artifact_compare(
                conn,
                {"run_a": ["s1-run-a"], "run_b": ["s1-run-b"]},
                eval_results_dir=FIXTURE_RUNS,
            )
            return detail_html, compare_html

        for html in self._render(render):
            with self.subTest(title=html.split("<title>", 1)[1].split("</title>", 1)[0]):
                self.assertNotIn("<script src=", html)
                self.assertNotIn("<link rel=", html)
                self.assertNotIn("<img src=", html)

    def test_compare_route_uses_configured_artifact_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            database_path = Path(tmp) / "dashboard.sqlite"
            db.init_db(database_path, reset=True)
            handler_type = server.make_handler(
                database_path,
                eval_results_dir=FIXTURE_RUNS,
                enable_inventory_refresh=False,
            )
            handler = object.__new__(handler_type)
            with db.connect(database_path) as conn:
                html = handler._route(
                    "/artifacts/compare",
                    {"run_a": ["s1-run-a"], "run_b": ["s1-run-b"]},
                    conn,
                )

        self.assertIn("A/B Response Viewer", html)
        self.assertIn("Response from model B for prompt two.", html)


if __name__ == "__main__":
    unittest.main()
