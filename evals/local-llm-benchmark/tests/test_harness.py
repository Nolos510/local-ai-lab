import csv
import json
import subprocess
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
