import csv
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
                self.server.requests.append({"path": self.path, "payload": payload})
                if mode == "ollama":
                    content = payload.get("prompt", "")
                    prompt_id = "unknown"
                    for candidate in ("LLMCORE-v0.1-001", "LLMCORE-v0.1-012"):
                        if candidate in content:
                            prompt_id = candidate
                    body = json.dumps(
                        {
                            "model": payload.get("model"),
                            "response": f"mock ollama response for {prompt_id}",
                            "done": True,
                            "done_reason": "stop",
                            "prompt_eval_count": 10,
                            "eval_count": 5,
                            "eval_duration": 500_000_000,
                            "total_duration": 800_000_000,
                        }
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
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
                    response_content = f"mock local response for {prompt_id}"
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
            self.skipTest(f"local bind unavailable in this environment: {exc}")
        server.requests = []
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

            template_lines = (
                (run_dir / "response-template.jsonl").read_text(encoding="utf-8").splitlines()
            )
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
            self.assertEqual(
                raw_records[0]["raw_response"],
                "Raw response line 1\nRaw response line 2",
            )
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

    def test_run_local_captures_all_prompts_and_rejects_non_loopback_endpoint(self):
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
                endpoint = f"http://127.0.0.1:{server.server_port}/v1"
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
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(metadata["run"]["total_latency_seconds"])
            self.assertGreaterEqual(metadata["run"]["total_latency_seconds"], 0)
            self.assertGreater(metadata["run"]["tokens_per_sec"], 0)
            self.assertIsNone(metadata["run"]["ttft_seconds"])

            self.run_harness(
                "export-dashboard",
                "--run-dir",
                str(run_dir),
            )
            with (run_dir / "dashboard-import" / "model_runs.csv").open(
                newline="",
                encoding="utf-8",
            ) as handle:
                run_rows = list(csv.DictReader(handle))
            self.assertIn("ttft_seconds", run_rows[0])
            self.assertIn("total_latency_seconds", run_rows[0])
            self.assertNotEqual(run_rows[0]["total_latency_seconds"], "")

            failed = self.run_harness_raw(
                "run-local",
                "--run-dir",
                str(run_dir),
                "--endpoint",
                "http://192.168.1.10/v1",
                "--force",
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("loopback", failed.stderr)

    def test_run_ollama_captures_all_prompts_and_rejects_non_loopback_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "20260623-fixture-ollama-runner"
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture Ollama Model",
                "--backend",
                "Ollama",
                "--output-root",
                tmp,
            )
            run_dir = Path(tmp) / run_id
            server = self.start_chat_server("ollama")
            try:
                endpoint = f"http://127.0.0.1:{server.server_port}"
                self.run_harness(
                    "run-ollama",
                    "--run-dir",
                    str(run_dir),
                    "--endpoint",
                    endpoint,
                    "--model-id",
                    "fixture-ollama:latest",
                    "--max-tokens",
                    "64",
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
            self.assertEqual(records[0]["stop_reason"], "stop")
            self.assertEqual(records[0]["input_tokens"], 10)
            self.assertEqual(records[0]["output_tokens"], 5)
            self.assertEqual(records[0]["tokens_per_sec"], 10.0)
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(metadata["run"]["total_latency_seconds"])
            self.assertGreaterEqual(metadata["run"]["total_latency_seconds"], 0)
            self.assertGreater(metadata["run"]["tokens_per_sec"], 0)
            self.assertIsNone(metadata["run"]["ttft_seconds"])
            self.assertEqual(server.requests[0]["path"], "/api/generate")
            self.assertEqual(server.requests[0]["payload"]["model"], "fixture-ollama:latest")
            self.assertIs(server.requests[0]["payload"]["stream"], False)
            self.assertEqual(server.requests[0]["payload"]["options"]["num_predict"], 64)

            self.run_harness(
                "export-dashboard",
                "--run-dir",
                str(run_dir),
            )
            with (run_dir / "dashboard-import" / "model_runs.csv").open(
                newline="",
                encoding="utf-8",
            ) as handle:
                run_rows = list(csv.DictReader(handle))
            self.assertNotEqual(run_rows[0]["total_latency_seconds"], "")
            self.assertNotEqual(run_rows[0]["tokens_per_sec"], "")

            failed = self.run_harness_raw(
                "run-ollama",
                "--run-dir",
                str(run_dir),
                "--endpoint",
                "http://192.168.1.10:11434",
                "--model-id",
                "fixture-ollama:latest",
                "--force",
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("loopback", failed.stderr)

    def test_run_mlx_lm_captures_all_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_id = "20260623-mlx-lm-fixture"
            fake_python = tmp_path / "python"
            fake_python.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        "import sys",
                        "assert sys.argv[1:4] == ['-m', 'mlx_lm', 'generate']",
                        "model_id = sys.argv[sys.argv.index('--model') + 1]",
                        "prompt = sys.argv[sys.argv.index('--prompt') + 1]",
                        "max_tokens = sys.argv[sys.argv.index('--max-tokens') + 1]",
                        "assert max_tokens == '64'",
                        "prompt_id = 'unknown'",
                        "for candidate in ('LLMCORE-v0.1-001', 'LLMCORE-v0.1-012'):",
                        "    if candidate in prompt:",
                        "        prompt_id = candidate",
                        "print('mock mlx response for {} using {}'.format(prompt_id, model_id))",
                        "print('\\x1b[32mgreen\\x1b[0m')",
                        "print('Prompt: 10 tokens, 20.0 tokens-per-sec')",
                        "print('Generation: 5 tokens, 12.5 tokens-per-sec')",
                    ]
                ),
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture MLX-LM Model",
                "--backend",
                "MLX-LM",
                "--output-root",
                tmp,
            )
            run_dir = tmp_path / run_id

            self.run_harness(
                "run-mlx-lm",
                "--run-dir",
                str(run_dir),
                "--model-id",
                "mlx-community/Fixture-4bit",
                "--python-path",
                str(fake_python),
                "--max-tokens",
                "64",
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
            self.assertIn("mlx-community/Fixture-4bit", records[0]["raw_response"])
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(metadata["run"]["total_latency_seconds"])
            self.assertGreaterEqual(metadata["run"]["total_latency_seconds"], 0)
            self.assertGreater(metadata["run"]["tokens_per_sec"], 0)
            self.assertIsNone(metadata["run"]["ttft_seconds"])
            log_text = (run_dir / "mlx-lm-capture.log").read_text(encoding="utf-8")
            self.assertIn("\\x1b[32mgreen\\x1b[0m", log_text)
            self.assertNotIn("\x1b[32mgreen", log_text)

    def test_run_llama_cpp_captures_all_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_id = "20260623-llama-cpp-fixture"
            fake_llama = tmp_path / "llama-cli"
            fake_llama.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        "import sys",
                        "model_id = sys.argv[sys.argv.index('-m') + 1]",
                        "prompt = sys.argv[sys.argv.index('-p') + 1]",
                        "max_tokens = sys.argv[sys.argv.index('-n') + 1]",
                        "assert max_tokens == '64'",
                        "assert '--no-display-prompt' in sys.argv",
                        "prompt_id = 'unknown'",
                        "for candidate in ('LLMCORE-v0.1-001', 'LLMCORE-v0.1-012'):",
                        "    if candidate in prompt:",
                        "        prompt_id = candidate",
                        "print('mock llama.cpp response for {} using {}'.format(",
                        "    prompt_id, model_id",
                        "))",
                        "print('\\x1b[34mblue\\x1b[0m')",
                        "prompt_stats = (",
                        "    'llama_perf_context_print: prompt eval time = '",
                        "    '100.00 ms / 10 tokens '",
                        "    '(10.00 ms per token, 100.00 tokens per second)'",
                        ")",
                        "eval_stats = (",
                        "    'llama_perf_context_print:        eval time = '",
                        "    '400.00 ms / 5 runs   '",
                        "    '(80.00 ms per token, 12.50 tokens per second)'",
                        ")",
                        "print(prompt_stats, file=sys.stderr)",
                        "print(eval_stats, file=sys.stderr)",
                    ]
                ),
                encoding="utf-8",
            )
            fake_llama.chmod(0o755)
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "Fixture llama.cpp Model",
                "--backend",
                "llama.cpp",
                "--output-root",
                tmp,
            )
            run_dir = tmp_path / run_id

            self.run_harness(
                "run-llama-cpp",
                "--run-dir",
                str(run_dir),
                "--model-id",
                str(tmp_path / "fixture-model.gguf"),
                "--llama-cli-path",
                str(fake_llama),
                "--max-tokens",
                "64",
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
            self.assertIn("fixture-model.gguf", records[0]["raw_response"])
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(metadata["run"]["total_latency_seconds"])
            self.assertGreaterEqual(metadata["run"]["total_latency_seconds"], 0)
            self.assertGreater(metadata["run"]["tokens_per_sec"], 0)
            self.assertIsNone(metadata["run"]["ttft_seconds"])
            log_text = (run_dir / "llama-cpp-capture.log").read_text(encoding="utf-8")
            self.assertIn("\\x1b[34mblue\\x1b[0m", log_text)
            self.assertNotIn("\x1b[34mblue", log_text)

    def test_init_run_rejects_traversal_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            failed = self.run_harness_raw(
                "init-run",
                "--benchmark-run-id",
                "../outside",
                "--model-name",
                "Traversal Model",
                "--backend",
                "llama.cpp",
                "--output-root",
                tmp,
            )

            self.assertEqual(failed.returncode, 2)
            self.assertIn("Invalid benchmark_run_id", failed.stderr)
            self.assertFalse((Path(tmp).parent / "outside").exists())

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
                        "print('\\x1b[31mred\\x1b[0m')",
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
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(metadata["run"]["total_latency_seconds"])
            self.assertGreaterEqual(metadata["run"]["total_latency_seconds"], 0)
            self.assertGreater(metadata["run"]["tokens_per_sec"], 0)
            log_text = (run_dir / "lms-cli-capture.log").read_text(encoding="utf-8")
            self.assertIn("\\x1b[31mred\\x1b[0m", log_text)
            self.assertNotIn("\x1b[31mred", log_text)

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

    def test_mlx_lm_parser_handles_generate_stats_labels(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("harness", HARNESS)
        harness = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(harness)

        stats = harness._parse_mlx_lm_stats(
            "\n".join(
                [
                    "Prompt: 310 tokens, 82.12 tokens-per-sec",
                    "Generation: 475 tokens, 34.66 tokens-per-sec",
                ]
            )
        )

        self.assertEqual(stats["tokens_per_sec"], 34.66)
        self.assertEqual(stats["input_tokens"], 310)
        self.assertEqual(stats["output_tokens"], 475)

    def test_llama_cpp_parser_handles_perf_context_labels(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("harness", HARNESS)
        harness = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(harness)

        stats = harness._parse_llama_cpp_stats(
            "\n".join(
                [
                    (
                        "llama_perf_context_print: prompt eval time = "
                        "280.00 ms / 310 tokens "
                        "(0.90 ms per token, 1107.14 tokens per second)"
                    ),
                    (
                        "llama_perf_context_print:        eval time = "
                        "13707.15 ms / 475 runs   "
                        "(28.86 ms per token, 34.66 tokens per second)"
                    ),
                ]
            )
        )

        self.assertEqual(stats["tokens_per_sec"], 34.66)
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
                endpoint = f"http://127.0.0.1:{server.server_port}/v1"
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

    def test_dashboard_csv_export_neutralizes_formula_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "20260605-fixture-formula"
            self.run_harness(
                "init-run",
                "--benchmark-run-id",
                run_id,
                "--model-name",
                "=cmd|' /C calc'!A0",
                "--backend",
                "LM Studio",
                "--output-root",
                tmp,
            )
            run_dir = Path(tmp) / run_id

            with (run_dir / "dashboard-import" / "models.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(rows[0]["model_name"], "'=cmd|' /C calc'!A0")


if __name__ == "__main__":
    unittest.main()
