import csv
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model_dashboard import csv_io, db


def write_table(path, table_name, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_io.TABLE_FIELDS[table_name])
        writer.writeheader()
        writer.writerows(rows)


class CsvImportTests(unittest.TestCase):
    def test_fixture_import_loads_linked_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "dashboard.sqlite"
            fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
            counts = csv_io.import_fixture_set(db_path, fixture_dir)

            self.assertEqual(counts["models"], 4)
            self.assertEqual(counts["model_runs"], 4)
            self.assertEqual(counts["eval_scores"], 4)
            self.assertEqual(counts["decisions"], 4)

            with db.connect(db_path) as conn:
                linked = conn.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM eval_scores s
                    JOIN model_runs r ON r.id = s.run_id
                    JOIN models m ON m.id = r.model_id
                    """
                ).fetchone()["count"]
                self.assertEqual(linked, 4)

    def test_second_import_preserves_existing_child_rows_for_same_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            first_dir = tmp_path / "first"
            second_dir = tmp_path / "second"

            write_table(
                first_dir / "models.csv",
                "models",
                [
                    {
                        "id": 1,
                        "model_name": "Qwen Test",
                        "model_family": "Qwen",
                        "provider": "Local",
                    }
                ],
            )
            write_table(
                first_dir / "model_runs.csv",
                "model_runs",
                [{"id": 1, "model_id": 1, "date_tested": "2026-06-03", "backend": "LM Studio"}],
            )
            write_table(first_dir / "eval_scores.csv", "eval_scores", [])
            write_table(
                first_dir / "decisions.csv",
                "decisions",
                [
                    {
                        "id": 1,
                        "model_id": 1,
                        "decision": "retest",
                        "keep_installed": 1,
                        "created_at": "2026-06-03T20:00:00+00:00",
                    }
                ],
            )
            write_table(
                second_dir / "models.csv",
                "models",
                [
                    {
                        "id": 1,
                        "model_name": "Qwen Test",
                        "model_family": "Qwen",
                        "provider": "lmstudio-community",
                    }
                ],
            )
            write_table(
                second_dir / "model_runs.csv",
                "model_runs",
                [{"id": 2, "model_id": 1, "date_tested": "2026-06-03", "backend": "LM Studio"}],
            )
            write_table(
                second_dir / "eval_scores.csv",
                "eval_scores",
                [
                    {
                        "id": 1,
                        "run_id": 2,
                        "instruction_following": 72,
                        "truthfulness_uncertainty": 70,
                        "reasoning": 66,
                        "coding_debugging": 88,
                        "agent_planning": 72,
                        "local_ai_lab_usefulness": 60,
                        "research_synthesis": 62,
                        "business_seo_strategy": 80,
                        "long_context": 82,
                        "creativity": 74,
                        "speed_practicality": 84,
                        "total_score": 73.64,
                        "final_label": "CODING_SPECIALIST",
                    }
                ],
            )
            write_table(
                second_dir / "decisions.csv",
                "decisions",
                [
                    {
                        "id": 2,
                        "model_id": 1,
                        "decision": "keep",
                        "keep_installed": 1,
                        "created_at": "2026-06-03T20:30:00+00:00",
                    }
                ],
            )

            for csv_dir in (first_dir, second_dir):
                csv_io.import_all(
                    db_path,
                    {
                        "models": csv_dir / "models.csv",
                        "model_runs": csv_dir / "model_runs.csv",
                        "eval_scores": csv_dir / "eval_scores.csv",
                        "decisions": csv_dir / "decisions.csv",
                    },
                )

            with db.connect(db_path) as conn:
                self.assertEqual(db.table_count(conn, "models"), 1)
                self.assertEqual(db.table_count(conn, "model_runs"), 2)
                self.assertEqual(db.table_count(conn, "eval_scores"), 1)
                self.assertEqual(db.table_count(conn, "decisions"), 2)

    def test_legacy_eval_scores_without_score_status_import_as_confirmed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            csv_dir = tmp_path / "legacy"
            write_table(
                csv_dir / "models.csv",
                "models",
                [{"id": 1, "model_name": "Legacy Score Model"}],
            )
            write_table(
                csv_dir / "model_runs.csv",
                "model_runs",
                [{"id": 1, "model_id": 1, "date_tested": "2026-06-05", "backend": "LM Studio"}],
            )
            legacy_fields = [
                field for field in csv_io.TABLE_FIELDS["eval_scores"] if field != "score_status"
            ]
            with (csv_dir / "eval_scores.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=legacy_fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "id": 1,
                        "run_id": 1,
                        "instruction_following": 70,
                        "truthfulness_uncertainty": 70,
                        "reasoning": 70,
                        "coding_debugging": 70,
                        "agent_planning": 70,
                        "local_ai_lab_usefulness": 70,
                        "research_synthesis": 70,
                        "business_seo_strategy": 70,
                        "long_context": 70,
                        "creativity": 70,
                        "speed_practicality": 70,
                        "total_score": "",
                        "final_label": "",
                    }
                )

            csv_io.import_all(
                db_path,
                {
                    "models": csv_dir / "models.csv",
                    "model_runs": csv_dir / "model_runs.csv",
                    "eval_scores": csv_dir / "eval_scores.csv",
                },
            )

            with db.connect(db_path) as conn:
                row = conn.execute("SELECT score_status FROM eval_scores").fetchone()
            self.assertEqual(row["score_status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
