import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


HARNESS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = HARNESS_DIR.parents[1]
HARNESS = HARNESS_DIR / "harness.py"
APP_DIR = REPO_ROOT / "apps" / "model-dashboard"
sys.path.insert(0, str(APP_DIR))

from model_dashboard import csv_io, db  # noqa: E402


class LocalBenchmarkHarnessTests(unittest.TestCase):
    def run_harness(self, *args):
        result = subprocess.run(
            [sys.executable, str(HARNESS), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def run_harness_raw(self, *args):
        return subprocess.run(
            [sys.executable, str(HARNESS), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def start_chat_server(self, mode):
        class ChatHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                request_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                payload = json.loads(request_body.decode("utf-8"))
                messages = payload.get("messages", [])
                content = messages[-1].get("content", "") if messages else ""
                if mode == "judge":
                    scores = {field: 77 for field in self.server.metric_fields}
                    response_content = json.dumps(
                        {
                            "scores": scores,
                            "total_score": 77,
                            "final_label": "WATCHLIST",
                            "rationale": "Draft local judge fixture.",
                            "metric_rationales": {
                                field: "Fixture rationale" for field in self.server.metric_fields
                            },
                        }
                    )
                else:
                    prompt_id = "unknown"
                    for candidate in ("LLMCORE-v0.1-001", "LLMCORE-v0.1-012"):
                        if candidate in content:
                            prompt_id = candidate
                    response_content = "mock local response for {}".format(prompt_id)
                body = json.dumps(
                    {
                        "choices": [
                            {
                                "message": {"content": response_content},
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), ChatHandler)
        except PermissionError as exc:
            self.skipTest("local bind unavailable in this environment: {}".format(exc))
        server.metric_fields = [
            "instruction_following",
            "truthfulness_uncertainty",
            "reasoning",
            "coding_debugging",
            "agent_planning",
            "local_ai_lab_usefulness",
            "research_synthesis",
            "business_seo_strategy",
            "long_context",
            "creativity",
            "speed_practicality",
        ]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server

    def test_init_run_creates_local_artifact_skeleton(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "20260603-fixture-model-llamacpp-q4"
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture Model",
                "--backend",
                "llama.cpp",
                "--output-root",
                tmp,
                "--temperature",
                "0.2",
                "--top-p",
                "0.9",
            )

            run_dir = Path(tmp) / run_id
            self.assertTrue((run_dir / "metadata.json").exists())
            self.assertTrue((run_dir / "raw_responses.jsonl").exists())
            self.assertTrue((run_dir / "response-template.jsonl").exists())

            template_lines = (run_dir / "response-template.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(len(template_lines), 12)

            for table_name in ("models", "model_runs", "eval_scores", "decisions"):
                self.assertTrue((run_dir / "dashboard-import" / f"{table_name}.csv").exists())

            with (run_dir / "dashboard-import" / "eval_scores.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows, [])

    def test_record_responses_and_export_dashboard_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "20260603-fixture-model-llamacpp-q4"
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture Model",
                "--backend",
                "llama.cpp",
                "--output-root",
                tmp,
            )
            run_dir = Path(tmp) / run_id
            responses_path = Path(tmp) / "manual-responses.jsonl"
            responses_path.write_text(
                json.dumps(
                    {
                        "prompt_id": "LLMCORE-v0.1-001",
                        "started_at": "2026-06-03T10:00:00-07:00",
                        "completed_at": "2026-06-03T10:00:04-07:00",
                        "latency_ms": 4000,
                        "raw_response": "Raw response line 1\nRaw response line 2",
                        "evaluator_notes": "Manual fixture note.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            self.run_harness(
                "record-responses",
                "--run-dir",
                str(run_dir),
                "--responses-jsonl",
                str(responses_path),
                "--force",
            )

            raw_records = [
                json.loads(line)
                for line in (run_dir / "raw_responses.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(raw_records), 1)
            self.assertEqual(raw_records[0]["benchmark_run_id"], run_id)
            self.assertEqual(raw_records[0]["raw_response"], "Raw response line 1\nRaw response line 2")
            self.assertRegex(raw_records[0]["prompt_text_sha256"], r"^[0-9a-f]{64}$")

            scores_path = Path(tmp) / "scores.json"
            scores = {
                "scores": {
                    "instruction_following": 80,
                    "truthfulness_uncertainty": 80,
                    "reasoning": 80,
                    "coding_debugging": 80,
                    "agent_planning": 80,
                    "local_ai_lab_usefulness": 80,
                    "research_synthesis": 80,
                    "business_seo_strategy": 80,
                    "long_context": 80,
                    "creativity": 80,
                    "speed_practicality": 80,
                },
                "final_label": "WATCHLIST",
            }
            scores_path.write_text(json.dumps(scores), encoding="utf-8")

            decision_path = Path(tmp) / "decision.json"
            decision_path.write_text(
                json.dumps(
                    {
                        "decision": "watchlist",
                        "best_use_case": "Local fixture checks",
                        "weakness": "Manual fixture only",
                        "retest_condition": "Run full prompt set",
                    }
                ),
                encoding="utf-8",
            )

            self.run_harness(
                "export-dashboard",
                "--run-dir",
                str(run_dir),
                "--scores-json",
                str(scores_path),
                "--decision-json",
                str(decision_path),
            )

            with (run_dir / "dashboard-import" / "eval_scores.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                score_rows = list(csv.DictReader(handle))
            self.assertEqual(len(score_rows), 1)
            self.assertEqual(score_rows[0]["final_label"], "WATCHLIST")
            self.assertEqual(score_rows[0]["instruction_following"], "80.0")

            with (run_dir / "dashboard-import" / "decisions.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                decision_rows = list(csv.DictReader(handle))
            self.assertEqual(decision_rows[0]["decision"], "watchlist")

            dashboard_db = Path(tmp) / "dashboard.sqlite"
            counts = csv_io.import_all(
                dashboard_db,
                {
                    "models": run_dir / "dashboard-import" / "models.csv",
                    "model_runs": run_dir / "dashboard-import" / "model_runs.csv",
                    "eval_scores": run_dir / "dashboard-import" / "eval_scores.csv",
                    "decisions": run_dir / "dashboard-import" / "decisions.csv",
                },
            )
            self.assertEqual(
                counts,
                {"models": 1, "model_runs": 1, "eval_scores": 1, "decisions": 1},
            )
            with db.connect(dashboard_db) as conn:
                summaries = db.list_model_summaries(conn)
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0]["model_name"], "Fixture Model")
            self.assertEqual(summaries[0]["final_label"], "WATCHLIST")

    def test_run_local_captures_all_prompts_and_rejects_public_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "20260605-fixture-local-runner"
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture Runner Model",
                "--backend",
                "LM Studio",
                "--output-root",
                tmp,
            )
            run_dir = Path(tmp) / run_id
            server = self.start_chat_server("runner")
            try:
                endpoint = "http://127.0.0.1:{}/v1".format(server.server_port)
                self.run_harness(
                    "run-local",
                    "--run-dir",
                    str(run_dir),
                    "--endpoint",
                    endpoint,
                    "--model",
                    "fixture-local-model",
                    "--force",
                )
            finally:
                server.shutdown()
                server.server_close()

            records = [
                json.loads(line)
                for line in (run_dir / "raw_responses.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(records), 12)
            self.assertTrue(all(record["raw_response"] for record in records))
            self.assertTrue(all(record["error"] is None for record in records))

            failed = self.run_harness_raw(
                "run-local",
                "--run-dir",
                str(run_dir),
                "--endpoint",
                "https://8.8.8.8/v1",
                "--force",
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("public IP", failed.stderr)

    def test_run_lmstudio_cli_captures_all_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_id = "20260605-lmstudio-cli-fixture"
            fake_lms = tmp_path / "lms"
            fake_lms.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        "import sys",
                        "model_id = sys.argv[2]",
                        "assert '--yes' in sys.argv",
                        "assert '--dont-fetch-catalog' in sys.argv",
                        "prompt = sys.argv[sys.argv.index('-p') + 1]",
                        "prompt_id = 'unknown'",
                        "for candidate in ('LLMCORE-v0.1-001', 'LLMCORE-v0.1-012'):",
                        "    if candidate in prompt:",
                        "        prompt_id = candidate",
                        "print('mock lms response for {} using {}'.format(prompt_id, model_id))",
                        "print('prompt tokens: 10')",
                        "print('completion tokens: 5')",
                        "print('12.5 tok/s')",
                    ]
                ),
                encoding="utf-8",
            )
            fake_lms.chmod(0o755)
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture LM Studio Model",
                "--backend",
                "LM Studio CLI",
                "--output-root",
                tmp,
            )
            run_dir = tmp_path / run_id

            self.run_harness(
                "run-lmstudio-cli",
                "--run-dir",
                str(run_dir),
                "--model-id",
                "fixture-model-id",
                "--lms-path",
                str(fake_lms),
                "--force",
            )

            records = [
                json.loads(line)
                for line in (run_dir / "raw_responses.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(records), 12)
            self.assertEqual(records[0]["stop_reason"], "cli_exit_0")
            self.assertEqual(records[0]["input_tokens"], 10)
            self.assertEqual(records[0]["output_tokens"], 5)
            self.assertEqual(records[0]["tokens_per_sec"], 12.5)
            self.assertIn("fixture-model-id", records[0]["raw_response"])
            self.assertTrue((run_dir / "lms-cli-capture.log").exists())

    def test_lmstudio_cli_parser_handles_lms_stats_labels(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("harness", HARNESS)
        harness = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(harness)

        stats = harness._parse_lms_stats(
            "\n".join(
                [
                    "Prediction Stats:",
                    "  Tokens/Second: 72.34",
                    "  Prompt Tokens: 310",
                    "  Predicted Tokens: 475",
                ]
            )
        )

        self.assertEqual(stats["tokens_per_sec"], 72.34)
        self.assertEqual(stats["input_tokens"], 310)
        self.assertEqual(stats["output_tokens"], 475)

    def test_suggest_scores_writes_draft_and_exports_draft_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "20260605-fixture-draft-scoring"
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture Draft Model",
                "--backend",
                "LM Studio",
                "--output-root",
                tmp,
            )
            run_dir = Path(tmp) / run_id
            responses_path = Path(tmp) / "manual-responses.jsonl"
            responses_path.write_text(
                json.dumps(
                    {
                        "prompt_id": "LLMCORE-v0.1-001",
                        "raw_response": "A compact but useful fixture answer.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.run_harness(
                "record-responses",
                "--run-dir",
                str(run_dir),
                "--responses-jsonl",
                str(responses_path),
                "--force",
            )

            server = self.start_chat_server("judge")
            draft_path = run_dir / "draft-scores.json"
            try:
                endpoint = "http://127.0.0.1:{}/v1".format(server.server_port)
                self.run_harness(
                    "suggest-scores",
                    "--run-dir",
                    str(run_dir),
                    "--endpoint",
                    endpoint,
                    "--judge-model",
                    "fixture-judge",
                    "--out",
                    str(draft_path),
                )
            finally:
                server.shutdown()
                server.server_close()

            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            self.assertEqual(draft["score_status"], "draft")
            self.assertEqual(draft["scores"]["reasoning"], 77.0)

            self.run_harness(
                "export-dashboard",
                "--run-dir",
                str(run_dir),
                "--scores-json",
                str(draft_path),
            )

            with (run_dir / "dashboard-import" / "eval_scores.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["score_status"], "draft")


if __name__ == "__main__":
    unittest.main()
