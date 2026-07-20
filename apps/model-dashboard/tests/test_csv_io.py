import csv
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_artifact_import_remaps_ids_when_fixture_rows_collide(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
            csv_io.import_fixture_set(db_path, fixture_dir)
            artifact_dir = tmp_path / "artifact"
            benchmark_run_id = "20260605-qwen3-coder-30b-a3b-lmstudio-cli-r1"

            write_table(
                artifact_dir / "models.csv",
                "models",
                [
                    {
                        "id": 1,
                        "model_name": "Qwen3-Coder-30B-A3B-Instruct-MLX-4bit",
                        "model_family": "Qwen",
                        "provider": "lmstudio-community local artifact",
                        "params_b": 30,
                        "source_url": "https://huggingface.co/lmstudio-community/qwen3",
                    }
                ],
            )
            write_table(
                artifact_dir / "model_runs.csv",
                "model_runs",
                [
                    {
                        "id": 3,
                        "model_id": 1,
                        "date_tested": "2026-06-05",
                        "backend": "LM Studio CLI",
                        "format": "MLX",
                        "quantization": "4bit",
                        "tokens_per_sec": 66.46,
                        "run_notes": f"benchmark_run_id={benchmark_run_id} | dashboard=yes",
                    }
                ],
            )
            write_table(
                artifact_dir / "eval_scores.csv",
                "eval_scores",
                [
                    {
                        "id": 2,
                        "run_id": 3,
                        "instruction_following": 76,
                        "truthfulness_uncertainty": 72,
                        "reasoning": 86,
                        "coding_debugging": 64,
                        "agent_planning": 70,
                        "local_ai_lab_usefulness": 55,
                        "research_synthesis": 77,
                        "business_seo_strategy": 82,
                        "long_context": 80,
                        "creativity": 73,
                        "speed_practicality": 76,
                        "total_score": 72.5,
                        "final_label": "WATCHLIST",
                        "score_status": "confirmed",
                    }
                ],
            )
            write_table(
                artifact_dir / "decisions.csv",
                "decisions",
                [
                    {
                        "id": 3,
                        "model_id": 1,
                        "decision": "watchlist",
                        "keep_installed": 1,
                        "created_at": "2026-06-06T02:18:06+00:00",
                    }
                ],
            )

            counts = csv_io.import_all(
                db_path,
                {
                    "models": artifact_dir / "models.csv",
                    "model_runs": artifact_dir / "model_runs.csv",
                    "eval_scores": artifact_dir / "eval_scores.csv",
                    "decisions": artifact_dir / "decisions.csv",
                },
            )

            self.assertEqual(counts, {
                "models": 1,
                "model_runs": 1,
                "eval_scores": 1,
                "decisions": 1,
            })
            with db.connect(db_path) as conn:
                self.assertEqual(db.table_count(conn, "models"), 5)
                self.assertEqual(db.table_count(conn, "model_runs"), 5)
                self.assertEqual(db.table_count(conn, "eval_scores"), 5)
                self.assertEqual(db.table_count(conn, "decisions"), 5)
                imported = conn.execute(
                    """
                    SELECT m.id AS model_id, r.id AS run_id, s.id AS score_id, d.id AS decision_id
                    FROM models m
                    JOIN model_runs r ON r.model_id = m.id
                    JOIN eval_scores s ON s.run_id = r.id
                    JOIN decisions d ON d.model_id = m.id
                    WHERE r.run_notes LIKE ?
                    """,
                    (f"%benchmark_run_id={benchmark_run_id}%",),
                ).fetchone()
                self.assertIsNotNone(imported)
                self.assertGreater(imported["model_id"], 4)
                self.assertGreater(imported["run_id"], 4)
                self.assertGreater(imported["score_id"], 4)
                self.assertGreater(imported["decision_id"], 4)

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

    def test_model_run_perf_columns_import_and_legacy_csv_remains_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            csv_dir = tmp_path / "input"
            write_table(
                csv_dir / "models.csv",
                "models",
                [{"id": 1, "model_name": "Perf Model"}],
            )
            write_table(
                csv_dir / "model_runs.csv",
                "model_runs",
                [
                    {
                        "id": 1,
                        "model_id": 1,
                        "date_tested": "2026-06-17",
                        "backend": "LM Studio CLI",
                        "tokens_per_sec": "12.5",
                        "ttft_seconds": "",
                        "total_latency_seconds": "9.25",
                    }
                ],
            )
            write_table(csv_dir / "eval_scores.csv", "eval_scores", [])
            csv_io.import_all(
                db_path,
                {
                    "models": csv_dir / "models.csv",
                    "model_runs": csv_dir / "model_runs.csv",
                    "eval_scores": csv_dir / "eval_scores.csv",
                },
            )
            with db.connect(db_path) as conn:
                row = conn.execute(
                    "SELECT tokens_per_sec, ttft_seconds, total_latency_seconds FROM model_runs"
                ).fetchone()
            self.assertEqual(row["tokens_per_sec"], 12.5)
            self.assertIsNone(row["ttft_seconds"])
            self.assertEqual(row["total_latency_seconds"], 9.25)

            legacy_dir = tmp_path / "legacy"
            write_table(
                legacy_dir / "models.csv",
                "models",
                [{"id": 2, "model_name": "Legacy Perf Model"}],
            )
            legacy_fields = [
                field
                for field in csv_io.TABLE_FIELDS["model_runs"]
                if field not in {"ttft_seconds", "total_latency_seconds"}
            ]
            with (legacy_dir / "model_runs.csv").open(
                "w",
                newline="",
                encoding="utf-8",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=legacy_fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "id": 2,
                        "model_id": 2,
                        "date_tested": "2026-06-17",
                        "backend": "LM Studio CLI",
                    }
                )
            csv_io.import_all(
                db_path,
                {
                    "models": legacy_dir / "models.csv",
                    "model_runs": legacy_dir / "model_runs.csv",
                },
            )
            with db.connect(db_path) as conn:
                legacy_row = conn.execute(
                    "SELECT ttft_seconds, total_latency_seconds FROM model_runs WHERE id = 2"
                ).fetchone()
            self.assertIsNone(legacy_row["ttft_seconds"])
            self.assertIsNone(legacy_row["total_latency_seconds"])

    def test_model_run_import_backfills_missing_run_config_with_inferred_sources(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            csv_dir = tmp_path / "input"
            write_table(
                csv_dir / "models.csv",
                "models",
                [
                    {
                        "id": 1,
                        "model_name": "Fixture Local Model Q5_K_M",
                        "source_url": "lmstudio-community/fixture-q5",
                    }
                ],
            )
            write_table(
                csv_dir / "model_runs.csv",
                "model_runs",
                [
                    {
                        "id": 1,
                        "model_id": 1,
                        "date_tested": "2026-06-17",
                        "backend": "LM Studio CLI",
                        "run_notes": "benchmark_run_id=fixture-run",
                    }
                ],
            )
            write_table(csv_dir / "eval_scores.csv", "eval_scores", [])
            csv_io.import_all(
                db_path,
                {
                    "models": csv_dir / "models.csv",
                    "model_runs": csv_dir / "model_runs.csv",
                    "eval_scores": csv_dir / "eval_scores.csv",
                },
            )

            with db.connect(db_path) as conn:
                row = conn.execute(
                    """
                    SELECT quantization, context_window, temperature, top_p, run_notes
                    FROM model_runs
                    WHERE id = 1
                    """
                ).fetchone()

            self.assertEqual(row["quantization"], "Q5_K_M")
            self.assertEqual(row["context_window"], 4096)
            self.assertEqual(row["temperature"], 0.2)
            self.assertEqual(row["top_p"], 0.9)
            self.assertIn("quantization_source=inferred:model_name_or_path", row["run_notes"])
            self.assertIn("context_window_source=inferred:benchmark_default", row["run_notes"])
            self.assertIn("temperature_source=inferred:benchmark_default", row["run_notes"])
            self.assertIn("top_p_source=inferred:benchmark_default", row["run_notes"])

    def test_export_neutralizes_spreadsheet_formula_prefixes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "dashboard.sqlite"
            csv_dir = tmp_path / "input"
            export_dir = tmp_path / "export"
            write_table(
                csv_dir / "models.csv",
                "models",
                [
                    {
                        "id": 1,
                        "model_name": "=cmd|' /C calc'!A0",
                        "model_family": "Formula",
                    }
                ],
            )
            write_table(
                csv_dir / "model_runs.csv",
                "model_runs",
                [{"id": 1, "model_id": 1, "date_tested": "2026-06-05", "backend": "LM Studio"}],
            )
            write_table(csv_dir / "eval_scores.csv", "eval_scores", [])
            write_table(csv_dir / "decisions.csv", "decisions", [])
            csv_io.import_all(
                db_path,
                {
                    "models": csv_dir / "models.csv",
                    "model_runs": csv_dir / "model_runs.csv",
                    "eval_scores": csv_dir / "eval_scores.csv",
                    "decisions": csv_dir / "decisions.csv",
                },
            )

            exported = csv_io.export_all(db_path, export_dir)

            with exported["models"].open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["model_name"], "'=cmd|' /C calc'!A0")


if __name__ == "__main__":
    unittest.main()
