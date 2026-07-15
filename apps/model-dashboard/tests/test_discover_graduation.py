from __future__ import annotations

import csv
import json
import sqlite3
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

from model_dashboard import db, discover, server  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402

CANDIDATE_FIELDS = (
    "candidate_id",
    "model_name",
    "model_family",
    "status",
    "format_or_runtime",
    "benchmark_run_id",
    "model_page_url",
    "github_url",
    "why_interesting",
    "risk_notes",
    "proposed_eval",
)


def write_candidates(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def candidate(candidate_id: str, name: str, run_id: str) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "model_name": name,
        "model_family": "Fixture",
        "status": "ready_for_eval",
        "format_or_runtime": "GGUF",
        "benchmark_run_id": run_id,
        "model_page_url": f"https://huggingface.co/example/{candidate_id}",
        "github_url": "",
        "why_interesting": "Graduation fixture.",
        "risk_notes": "Fixture only.",
        "proposed_eval": "Run locally.",
    }


def insert_run(
    conn: sqlite3.Connection,
    *,
    model_id: int,
    run_row_id: int,
    benchmark_run_id: str,
    score_status: str | None = None,
    decision: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO models (id, model_name, model_family, provider) VALUES (?, ?, ?, ?)",
        (model_id, f"Model {model_id}", "Fixture", "local"),
    )
    conn.execute(
        """
        INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes)
        VALUES (?, ?, '2026-07-14', 'fixture', ?)
        """,
        (run_row_id, model_id, f"benchmark_run_id={benchmark_run_id} | fixture=yes"),
    )
    if score_status:
        metric_names = ", ".join(METRIC_FIELDS)
        metric_values = ", ".join("80" for _ in METRIC_FIELDS)
        conn.execute(
            f"""
            INSERT INTO eval_scores (
                id, run_id, {metric_names}, total_score, final_label, score_status
            ) VALUES (?, ?, {metric_values}, 80, 'WATCHLIST', ?)
            """,
            (1000 + run_row_id, run_row_id, score_status),
        )
    if decision:
        conn.execute(
            """
            INSERT INTO decisions (id, model_id, decision, keep_installed)
            VALUES (?, ?, ?, 0)
            """,
            (2000 + run_row_id, model_id, decision),
        )
    conn.commit()


def pending_state(candidate_id: str) -> dict[str, object]:
    return {
        "version": 1,
        "candidates": {
            candidate_id: {
                "source_type": "huggingface",
                "source_url": f"https://huggingface.co/example/{candidate_id}",
                "previous_revision": "old-sha",
                "previous_modified_at": "2026-07-01T00:00:00Z",
                "revision": "new-sha",
                "modified_at": "2026-07-13T00:00:00Z",
                "update_pending": True,
            }
        },
    }


class DiscoverGraduationTests(unittest.TestCase):
    def test_confirmed_or_decided_candidates_graduate_but_other_runs_do_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "dashboard.sqlite"
            registry = root / "candidates.csv"
            write_candidates(
                registry,
                [
                    candidate("confirmed", "Confirmed Candidate", "run-confirmed"),
                    candidate("decided", "Decided Candidate", "run-decided"),
                    candidate("draft", "Draft Candidate", "run-draft"),
                    candidate("merely-run", "Merely Run Candidate", "run-merely"),
                    candidate("not-imported", "Not Imported Candidate", "run-missing"),
                ],
            )
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                insert_run(
                    conn,
                    model_id=1,
                    run_row_id=11,
                    benchmark_run_id="run-confirmed",
                    score_status="confirmed",
                )
                insert_run(
                    conn,
                    model_id=2,
                    run_row_id=12,
                    benchmark_run_id="run-decided",
                    decision="keep",
                )
                insert_run(
                    conn,
                    model_id=3,
                    run_row_id=13,
                    benchmark_run_id="run-draft",
                    score_status="draft",
                )
                insert_run(
                    conn,
                    model_id=4,
                    run_row_id=14,
                    benchmark_run_id="run-merely",
                )

                default_html = server._radar(conn, registry_path=registry)
                evaluated_html = server._radar(
                    conn,
                    {"view": ["evaluated"]},
                    registry_path=registry,
                )

            self.assertNotIn("Confirmed Candidate", default_html)
            self.assertNotIn("Decided Candidate", default_html)
            self.assertIn("Draft Candidate", default_html)
            self.assertIn("Merely Run Candidate", default_html)
            self.assertIn("Not Imported Candidate", default_html)
            self.assertIn('href="/radar?view=evaluated"', default_html)
            self.assertIn("Evaluated <strong>2</strong>", default_html)
            self.assertIn("Confirmed Candidate", evaluated_html)
            self.assertIn("Decided Candidate", evaluated_html)
            self.assertNotIn("Draft Candidate", evaluated_html)

    def test_overlay_rows_graduate_and_home_discover_count_is_ungraduated_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "dashboard.sqlite"
            registry = root / "candidates.csv"
            overlay = root / "local_inventory_candidates.csv"
            eval_results = root / "eval_results"
            hardware = root / "hardware"
            eval_results.mkdir()
            hardware.mkdir()
            write_candidates(
                registry,
                [candidate("still-open", "Still Open", "run-open")],
            )
            write_candidates(
                overlay,
                [candidate("overlay-done", "Overlay Evaluated", "run-overlay")],
            )
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                insert_run(
                    conn,
                    model_id=7,
                    run_row_id=17,
                    benchmark_run_id="run-overlay",
                    score_status="confirmed",
                )
                default_html = server._radar(
                    conn,
                    registry_path=registry,
                    local_inventory_path=overlay,
                )
                evaluated_html = server._radar(
                    conn,
                    {"view": ["evaluated"]},
                    registry_path=registry,
                    local_inventory_path=overlay,
                )
                home_html = server._overview(
                    conn,
                    registry_path=registry,
                    local_inventory_path=overlay,
                    eval_results_dir=eval_results,
                    hardware_profiles_dir=hardware,
                )

            self.assertIn("Still Open", default_html)
            self.assertNotIn("Overlay Evaluated", default_html)
            self.assertIn("Overlay Evaluated", evaluated_html)
            workflow = home_html.split('class="workflow-strip"', 1)[1]
            discover_step = workflow.split('href="/radar"', 1)[1].split("</a>", 1)[0]
            self.assertIn("<strong>1</strong>", discover_step)
            self.assertIn("candidates to evaluate", discover_step)

    def test_pending_upstream_update_resurfaces_with_badge_and_dismiss_regraduates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "dashboard.sqlite"
            registry = root / "candidates.csv"
            state_path = root / "radar_upstream_state.json"
            write_candidates(
                registry,
                [candidate("resurface", "Resurfaced Candidate", "run-resurface")],
            )
            state_path.write_text(json.dumps(pending_state("resurface")), encoding="utf-8")
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                insert_run(
                    conn,
                    model_id=9,
                    run_row_id=19,
                    benchmark_run_id="run-resurface",
                    score_status="confirmed",
                )
                with mock.patch(
                    "urllib.request.urlopen",
                    side_effect=AssertionError("dashboard render must stay offline"),
                ):
                    html = server._radar(
                        conn,
                        registry_path=registry,
                        upstream_state_path=state_path,
                        action_token="secret-token",
                    )

                self.assertIn("Resurfaced Candidate", html)
                self.assertIn("updated upstream since evaluation", html)
                self.assertIn("old-sha", html)
                self.assertIn("new-sha", html)
                self.assertIn('action="/actions/dismiss-upstream-update"', html)
                self.assertIn('value="secret-token"', html)

                discover.dismiss_upstream_update(state_path, "resurface")
                dismissed_html = server._radar(
                    conn,
                    registry_path=registry,
                    upstream_state_path=state_path,
                )
                evaluated_html = server._radar(
                    conn,
                    {"view": ["evaluated"]},
                    registry_path=registry,
                    upstream_state_path=state_path,
                )

            self.assertNotIn("Resurfaced Candidate", dismissed_html)
            self.assertIn("Resurfaced Candidate", evaluated_html)

    def test_dismiss_post_is_token_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "dashboard.sqlite"
            registry = root / "candidates.csv"
            overlay = root / "overlay.csv"
            state_path = root / "radar_upstream_state.json"
            write_candidates(
                registry,
                [candidate("post-dismiss", "POST Dismiss Candidate", "run-post")],
            )
            state_path.write_text(json.dumps(pending_state("post-dismiss")), encoding="utf-8")
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                insert_run(
                    conn,
                    model_id=10,
                    run_row_id=20,
                    benchmark_run_id="run-post",
                    score_status="confirmed",
                )

            handler = server.make_handler(
                db_path,
                action_token="right-token",
                candidate_registry_path=registry,
                local_inventory_registry_path=overlay,
                upstream_state_path=state_path,
            )
            try:
                httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            except PermissionError as exc:
                self.skipTest(f"local bind unavailable in this environment: {exc}")
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(httpd.shutdown)
            self.addCleanup(httpd.server_close)
            url = f"http://127.0.0.1:{httpd.server_port}/actions/dismiss-upstream-update"

            def post(token: str):
                body = urlencode(
                    {"token": token, "candidate_id": "post-dismiss"}
                ).encode("utf-8")
                return urlopen(Request(url, data=body, method="POST"), timeout=5)

            with self.assertRaises(HTTPError) as raised:
                post("wrong-token")
            self.assertEqual(400, raised.exception.code)
            self.assertTrue(
                json.loads(state_path.read_text(encoding="utf-8"))["candidates"][
                    "post-dismiss"
                ]["update_pending"]
            )

            with post("right-token") as response:
                body = response.read().decode("utf-8")
            self.assertEqual(200, response.status)
            self.assertNotIn("POST Dismiss Candidate", body)
            self.assertFalse(
                json.loads(state_path.read_text(encoding="utf-8"))["candidates"][
                    "post-dismiss"
                ]["update_pending"]
            )


if __name__ == "__main__":
    unittest.main()
