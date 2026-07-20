import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import recommend  # noqa: E402
from model_dashboard.pages import overview, retrieval  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


def write_metrics(path, *, query_count, k, recall_at_k, mrr):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "query_count": query_count,
                "k": k,
                "recall_at_k": recall_at_k,
                "mrr": mrr,
                "per_query": [],
            }
        ),
        encoding="utf-8",
    )


def complete_score_row(model_id, model_name, value):
    row = {
        "id": model_id,
        "model_id": model_id,
        "model_name": model_name,
        "score_status": "confirmed",
        "total_score": value,
        "final_label": "WATCHLIST",
        "tokens_per_sec": 10,
        "ram_usage_gb": 8,
        "decision": "watchlist",
        "provider": "local",
        "source_url": "",
        "model_family": "",
    }
    row.update({field: value for field in METRIC_FIELDS})
    return row


class RetrievalMetricsTests(unittest.TestCase):
    def test_parses_fixture_metrics_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture-metrics.json"
            write_metrics(
                path,
                query_count=12,
                k=7,
                recall_at_k=0.625,
                mrr=0.4375,
            )

            evidence = retrieval.load_retrieval_metrics(path)

        self.assertEqual(evidence["status"], "scored")
        self.assertEqual(evidence["query_count"], 12)
        self.assertEqual(evidence["k"], 7)
        self.assertEqual(evidence["recall_at_k"], 0.625)
        self.assertEqual(evidence["mrr"], 0.4375)

    def test_renders_multiple_configurations_for_direct_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "repo-docs-v0.2"
            write_metrics(
                corpus / "bge-m3-dense-identity-metrics.json",
                query_count=29,
                k=5,
                recall_at_k=0.62,
                mrr=0.51,
            )
            write_metrics(
                corpus / "bge-m3-hybrid-cross-encoder-metrics.json",
                query_count=29,
                k=5,
                recall_at_k=0.79,
                mrr=0.73,
            )

            with mock.patch("subprocess.run") as run:
                html = retrieval._retrieval(root)

            run.assert_not_called()

        self.assertIn("repo-docs-v0.2", html)
        self.assertIn("bge-m3:latest", html)
        self.assertIn("dense", html)
        self.assertIn("hybrid", html)
        self.assertIn("identity", html)
        self.assertIn("cross-encoder", html)
        self.assertIn("0.620", html)
        self.assertIn("0.510", html)
        self.assertIn("0.790", html)
        self.assertIn("0.730", html)
        self.assertLess(
            html.index("bge-m3-dense-identity-metrics.json"),
            html.index("bge-m3-hybrid-cross-encoder-metrics.json"),
        )

    def test_not_scored_yet_shows_exact_production_command_without_running_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "repo-docs-v0.2").mkdir()

            with mock.patch("subprocess.run") as run:
                html = retrieval._retrieval(root)

            run.assert_not_called()
            self.assertEqual(list(root.rglob("*-metrics.json")), [])

        self.assertEqual(html.count("not scored yet"), 4)
        self.assertIn("LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_2_bge_m3_dense_identity", html)
        self.assertIn("--retrieval-mode dense", html)
        self.assertIn("bge-m3-dense-identity-results.jsonl", html)
        self.assertIn("bge-m3-dense-identity-metrics.json", html)
        self.assertIn("LOCAL_AI_LAB_RERANKER_PROVIDER=cross_encoder", html)
        self.assertIn("$LOCAL_CROSS_ENCODER_PATH", html)

    def test_missing_and_malformed_metrics_are_handled_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "repo-docs-v0.2"
            corpus.mkdir()
            malformed = corpus / "bge-m3-dense-identity-metrics.json"
            malformed.write_text("{not valid json", encoding="utf-8")

            missing = retrieval.load_retrieval_metrics(
                corpus / "bge-m3-hybrid-identity-metrics.json"
            )
            invalid = retrieval.load_retrieval_metrics(malformed)
            html = retrieval._retrieval(root)

        self.assertEqual(missing["status"], "not_scored")
        self.assertEqual(invalid["status"], "unavailable")
        self.assertIn("metrics unavailable", html)
        self.assertIn("not scored yet", html)
        self.assertIn("Run the exact local command below to replace this invalid file.", html)

    def test_retrieval_models_stay_out_of_llm_top_results_and_task_recommender(self):
        rows = [
            complete_score_row(1, "bge-m3:latest", 100),
            complete_score_row(2, "bge-reranker-v2-m3", 99),
            complete_score_row(3, "Qwen Local", 70),
        ]

        summary = recommend.task_recommendations(rows)
        top_rows = overview._top_result_rows(rows)

        self.assertEqual(summary.scored_model_count, 1)
        self.assertEqual(
            {leader.model_name for task in summary.tasks for leader in task.leaders},
            {"Qwen Local"},
        )
        rendered_rows = "".join("".join(row) for row in top_rows)
        self.assertIn("Qwen Local", rendered_rows)
        self.assertNotIn("bge-m3", rendered_rows)
        self.assertNotIn("bge-reranker", rendered_rows)

    def test_retrieval_page_uses_only_inline_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "repo-docs-v0.2").mkdir()
            html = retrieval._retrieval(root)

        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link rel=", html)
        self.assertIn('class="metric-tip"', html)


if __name__ == "__main__":
    unittest.main()
