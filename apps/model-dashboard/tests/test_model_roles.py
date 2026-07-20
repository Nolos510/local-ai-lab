import json
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import model_roles  # noqa: E402
from model_dashboard.pages import actions, inventory, runs  # noqa: E402


class ModelRoleTests(unittest.TestCase):
    def test_known_embedding_and_reranker_families_are_non_generative(self):
        self.assertEqual(model_roles.infer_model_role("bge-m3:latest"), "embedding")
        self.assertEqual(
            model_roles.infer_model_role("text-embedding-nomic-embed-text-v1.5"),
            "embedding",
        )
        self.assertEqual(model_roles.infer_model_role("bge-reranker-v2-m3"), "reranker")
        self.assertFalse(model_roles.model_supports_generation("embedding"))
        self.assertFalse(model_roles.model_supports_generation("reranker"))

    def test_explicit_runtime_role_wins_and_multimodal_remains_generative(self):
        self.assertEqual(
            model_roles.infer_model_role("custom model", explicit="embedding"),
            "embedding",
        )
        self.assertEqual(model_roles.infer_model_role("Qwen2.5-VL-7B"), "multimodal")
        self.assertTrue(model_roles.model_supports_generation("multimodal"))

    def test_ollama_inventory_classifies_bge_and_excludes_it_from_run_all(self):
        parsed = inventory._parse_ollama_inventory(
            "NAME ID SIZE MODIFIED\nbge-m3:latest abc 1 GB now\nqwen2.5:14b def 9 GB now\n"
        )
        bge = next(row for row in parsed if row["model_id"] == "bge-m3:latest")
        qwen = next(row for row in parsed if row["model_id"] == "qwen2.5:14b")

        self.assertEqual(bge["model_type"], "embedding")
        self.assertEqual(qwen["model_type"], "generator")
        self.assertIn(
            "LLM benchmark not applicable",
            inventory._inventory_run_all_blocked_reason(bge, "registered", {}),
        )

    def test_embedding_artifact_is_excluded_from_scoring_and_resolution_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "bge-run"
            run_dir.mkdir()
            (run_dir / "metadata.json").write_text(
                json.dumps({"model": {"model_name": "bge-m3:latest"}}),
                encoding="utf-8",
            )
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"not a chat response"}\n',
                encoding="utf-8",
            )

            self.assertEqual(actions._unscored_artifact_ids(root), [])
            result = actions._score_artifact(
                "bge-run",
                root / "dashboard.sqlite",
                root,
                5,
                "http://127.0.0.1:1234/v1",
                "judge",
            )
            self.assertEqual(result["status"], "rejected")
            self.assertEqual(
                result["recommended_action"],
                "route_to_role_evaluation",
            )

            counts = runs._score_resolution_counts(
                [
                    {
                        "model_name": "bge-m3:latest",
                        "model_family": "",
                        "provider": "Ollama",
                        "format": "Ollama",
                        "score_status": "draft",
                        "quantization": None,
                        "context_window": 4096,
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "tokens_per_sec": None,
                        "ram_usage_gb": 10.0,
                    }
                ]
            )
            self.assertEqual(counts["non_generation"], 1)
            self.assertEqual(counts["draft"], 0)
            self.assertEqual(counts["missing_run_config"], 0)

    def test_resolution_counts_separate_quarantine_from_valid_draft_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for run_id in ("quarantined-run", "review-pending-run"):
                run_dir = root / run_id
                run_dir.mkdir()
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"raw_response":"usable answer"}\n',
                    encoding="utf-8",
                )
                (run_dir / "draft-scores.json").write_text(
                    json.dumps({"scores": {}}),
                    encoding="utf-8",
                )
            (root / "quarantined-run" / "score-review.json").write_text(
                json.dumps(
                    {
                        "status": "rejected",
                        "human_action": "automatic_invalid_evidence",
                        "recommended_action": "rerun_capture",
                    }
                ),
                encoding="utf-8",
            )

            def row(run_id):
                return {
                    "model_name": "Qwen local",
                    "model_family": "Qwen",
                    "provider": "LM Studio",
                    "format": "MLX",
                    "score_status": None,
                    "quantization": "4bit",
                    "context_window": 4096,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "tokens_per_sec": 20.0,
                    "ram_usage_gb": 24.0,
                    "run_notes": f"benchmark_run_id={run_id}",
                }

            counts = runs._score_resolution_counts(
                [row("quarantined-run"), row("review-pending-run")],
                root,
            )

            self.assertEqual(counts["quarantined"], 1)
            self.assertEqual(counts["draft"], 1)
            self.assertEqual(counts["unscored"], 0)
            state = runs._artifact_score_state(
                {"scores": "no", "draft_scores": "yes", "dashboard_import": "yes"},
                {
                    "status": "rejected",
                    "recommended_action": "rerun_capture",
                },
            )
            self.assertIn("excluded from active rankings", state)
            self.assertIn("rerun capture", state)


if __name__ == "__main__":
    unittest.main()
