import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db  # noqa: E402
from model_dashboard.pages import inventory  # noqa: E402


class InventoryThroughputTests(unittest.TestCase):
    def _render(self, models, runs, candidates=()):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "dashboard.sqlite"
            registry_path = root / "missing-candidates.csv"
            overlay_path = root / "local-inventory-candidates.csv"
            if candidates:
                with overlay_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=(
                            "candidate_id",
                            "model_name",
                            "local_model_id",
                            "local_runner",
                            "benchmark_run_id",
                        ),
                    )
                    writer.writeheader()
                    writer.writerows(candidates)

            with db.connect(db_path) as conn:
                db.create_schema(conn)
                model_ids = {}
                for run_id, run in enumerate(runs, start=1):
                    model_name = run["model_name"]
                    if model_name not in model_ids:
                        dashboard_model_id = len(model_ids) + 1
                        model_ids[model_name] = dashboard_model_id
                        conn.execute(
                            """
                            INSERT INTO models (id, model_name, provider)
                            VALUES (?, ?, 'local')
                            """,
                            (dashboard_model_id, model_name),
                        )
                    conn.execute(
                        """
                        INSERT INTO model_runs
                            (id, model_id, date_tested, backend, tokens_per_sec, run_notes)
                        VALUES (?, ?, ?, 'local', ?, ?)
                        """,
                        (
                            run_id,
                            model_ids[model_name],
                            run.get("date_tested", f"2026-07-{run_id:02d}"),
                            run.get("tokens_per_sec"),
                            run.get("run_notes", ""),
                        ),
                    )
                conn.commit()
                registry_candidates = inventory._load_radar_candidates(
                    registry_path,
                    overlay_path,
                )
                run_history = inventory._inventory_run_history(
                    conn,
                    registry_candidates,
                )

            return inventory._inventory(
                inventory_result={
                    "checked_at": "2026-07-14T12:00:00-07:00",
                    "checks": [],
                    "models": models,
                },
                registry_path=registry_path,
                local_inventory_path=overlay_path,
                run_history=run_history,
                hardware_profiles_dir=root / "missing-hardware-profiles",
                current_hardware_profile={"memory_gb": "256"},
            )

    @staticmethod
    def _model(model_id, display_name=None):
        return {
            "runtime": "LM Studio",
            "model_id": model_id,
            "display_name": display_name or model_id,
            "status": "loaded",
            "params_b": "7",
            "quantization": "4bit",
        }

    def test_exact_local_model_id_match_shows_observed_throughput(self):
        html = self._render(
            [self._model("runtime/exact-alpha-7b", "Inventory Alpha")],
            [
                {
                    "model_name": "Different Dashboard Label",
                    "tokens_per_sec": 41.25,
                    "run_notes": "model_id=runtime/exact-alpha-7b",
                }
            ],
        )

        self.assertIn("Fit: comfortable", html)
        self.assertIn("GB est.", html)
        self.assertIn("Observed 41.2 tok/s", html)

    def test_overlay_candidate_id_match_shows_observed_throughput(self):
        html = self._render(
            [self._model("runtime/overlay-alpha-7b", "Inventory Overlay Alpha")],
            [
                {
                    "model_name": "Dashboard Overlay Alpha",
                    "tokens_per_sec": 36.75,
                    "run_notes": "candidate_id=overlay-alpha",
                }
            ],
            candidates=[
                {
                    "candidate_id": "overlay-alpha",
                    "model_name": "Overlay Candidate Alpha",
                    "local_model_id": "runtime/overlay-alpha-7b",
                    "local_runner": "lmstudio-cli",
                }
            ],
        )

        self.assertIn("Observed 36.8 tok/s", html)

    def test_normalized_model_name_match_is_case_punctuation_and_space_insensitive(self):
        html = self._render(
            [self._model("unrelated-runtime-id", "ALPHA.Model 7B")],
            [{"model_name": "alpha-model_7b", "tokens_per_sec": 28.5}],
        )

        self.assertIn("Observed 28.5 tok/s", html)

    def test_no_match_renders_no_observed_decoration(self):
        html = self._render(
            [self._model("local-beta-7b", "Local Beta 7B")],
            [{"model_name": "Dashboard Gamma 7B", "tokens_per_sec": 99.9}],
        )

        self.assertNotIn('<span class="observed-performance">', html)

    def test_most_recent_matching_run_controls_observed_throughput_without_designation(self):
        html = self._render(
            [self._model("runtime/latest-alpha-7b", "Latest Alpha")],
            [
                {
                    "model_name": "Latest Alpha Dashboard",
                    "date_tested": "2026-07-10",
                    "tokens_per_sec": 17.0,
                    "run_notes": "model_id=runtime/latest-alpha-7b",
                },
                {
                    "model_name": "Latest Alpha Dashboard",
                    "date_tested": "2026-07-11",
                    "tokens_per_sec": 29.0,
                    "run_notes": "model_id=runtime/latest-alpha-7b",
                },
            ],
        )

        self.assertIn("Observed 29.0 tok/s", html)
        self.assertNotIn("Observed 17.0 tok/s", html)

    def test_registry_designated_run_controls_observed_throughput(self):
        html = self._render(
            [self._model("runtime/current-alpha-7b", "Current Alpha")],
            [
                {
                    "model_name": "Current Alpha Dashboard",
                    "date_tested": "2026-07-10",
                    "tokens_per_sec": 17.0,
                    "run_notes": (
                        "benchmark_run_id=designated-alpha | "
                        "candidate_id=current-alpha | model_id=runtime/current-alpha-7b"
                    ),
                },
                {
                    "model_name": "Current Alpha Dashboard",
                    "date_tested": "2026-07-11",
                    "tokens_per_sec": 29.0,
                    "run_notes": (
                        "benchmark_run_id=newer-alpha | "
                        "candidate_id=current-alpha | model_id=runtime/current-alpha-7b"
                    ),
                },
            ],
            candidates=[
                {
                    "candidate_id": "current-alpha",
                    "model_name": "Current Alpha",
                    "local_model_id": "runtime/current-alpha-7b",
                    "local_runner": "lmstudio-cli",
                    "benchmark_run_id": "designated-alpha",
                }
            ],
        )

        self.assertIn("Observed 17.0 tok/s", html)
        self.assertNotIn("Observed 29.0 tok/s", html)

    def test_latest_matching_run_without_throughput_does_not_reuse_older_observation(self):
        html = self._render(
            [self._model("runtime/null-latest-7b", "Null Latest")],
            [
                {
                    "model_name": "Null Latest Dashboard",
                    "date_tested": "2026-07-10",
                    "tokens_per_sec": 17.0,
                    "run_notes": "model_id=runtime/null-latest-7b",
                },
                {
                    "model_name": "Null Latest Dashboard",
                    "date_tested": "2026-07-11",
                    "tokens_per_sec": None,
                    "run_notes": "model_id=runtime/null-latest-7b",
                },
            ],
        )

        self.assertNotIn('<span class="observed-performance">', html)

    def test_normalized_name_collision_never_cross_attributes_throughput(self):
        html = self._render(
            [self._model("inventory-alpha", "Alpha.Model 7B")],
            [
                {"model_name": "Alpha-Model 7B", "tokens_per_sec": 14.0},
                {"model_name": "Alpha Model_7B", "tokens_per_sec": 91.0},
            ],
        )

        self.assertNotIn('<span class="observed-performance">', html)

    def test_inventory_render_never_spawns_subprocesses(self):
        with mock.patch("subprocess.run") as run:
            html = self._render(
                [self._model("runtime/safe-alpha-7b", "Safe Alpha")],
                [
                    {
                        "model_name": "Safe Alpha Dashboard",
                        "tokens_per_sec": 22.0,
                        "run_notes": "model_id=runtime/safe-alpha-7b",
                    }
                ],
            )

        self.assertIn("Observed 22.0 tok/s", html)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
