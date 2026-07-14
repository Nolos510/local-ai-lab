import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, fit, server  # noqa: E402


class FitAdvisorMathTests(unittest.TestCase):
    def test_estimate_includes_weight_and_context_overhead(self):
        self.assertAlmostEqual(fit.estimate_weights_gb(30, 4), 16.5)
        self.assertAlmostEqual(fit.estimate_memory_gb(30, 4), 24.5)

    def test_fit_boundaries_use_memory_after_system_reserve(self):
        # 64 GB machine - 16 GB reserve = 48 GB model budget.
        self.assertEqual(fit.classify_fit(23.99, 64), "comfortable")
        self.assertEqual(fit.classify_fit(24.0, 64), "fits")
        self.assertEqual(fit.classify_fit(38.39, 64), "fits")
        self.assertEqual(fit.classify_fit(38.4, 64), "tight")
        self.assertEqual(fit.classify_fit(47.99, 64), "tight")
        self.assertEqual(fit.classify_fit(48.0, 64), "exceeds")

    def test_unknown_and_non_finite_inputs_never_produce_an_estimate(self):
        for params_b, bits in (
            (None, 4),
            (30, None),
            (float("nan"), 4),
            (30, float("inf")),
            (-1, 4),
            (30, 0),
        ):
            with self.subTest(params_b=params_b, bits=bits):
                assessment = fit.assess_fit(params_b, bits, 64)
                self.assertEqual(assessment.status, "unknown")
                self.assertIsNone(assessment.estimated_memory_gb)

        known = fit.assess_fit(30, 4, 64)
        self.assertTrue(math.isfinite(known.estimated_weights_gb))
        self.assertTrue(math.isfinite(known.estimated_memory_gb))
        self.assertTrue(math.isfinite(known.budget_gb))

    def test_unambiguous_parameter_and_quantization_metadata_is_parsed(self):
        self.assertEqual(fit.parse_parameter_count_b("Qwen3-Coder-30B-A3B"), 30.0)
        self.assertEqual(fit.parse_quantization_bits("MLX-4bit"), 4.0)
        self.assertEqual(fit.parse_quantization_bits("Q5_K_M"), 5.0)
        self.assertEqual(fit.parse_quantization_bits("bf16"), 16.0)
        self.assertIsNone(fit.parse_quantization_bits("GGUF quant not selected"))


class FitAdvisorRenderingTests(unittest.TestCase):
    def test_fit_pills_render_on_discover_inventory_and_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "dashboard.sqlite"
            registry_path = root / "candidates.csv"
            hardware_dir = root / "lab-notes"
            hardware_dir.mkdir()
            (hardware_dir / "2026-07-14-hardware.json").write_text(
                json.dumps(
                    {
                        "captured_at": "2026-07-14T12:00:00Z",
                        "machine": {"machine": "arm64", "cpu_count": 32},
                        "macos": {
                            "machine_name": "Fit Test Mac",
                            "chip_brand": "Apple test chip",
                            "memory_bytes": 64 * 1024**3,
                        },
                        "runtimes": {"lms": {"present": True}},
                    }
                ),
                encoding="utf-8",
            )
            fields = (
                "candidate_id",
                "model_name",
                "model_family",
                "status",
                "format_or_runtime",
                "benchmark_run_id",
                "local_runner",
                "local_model_id",
                "runtime_availability",
            )
            with registry_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "candidate_id": "fit-ready-7b",
                        "model_name": "Fit Ready 7B",
                        "model_family": "Fit",
                        "status": "ready_for_eval",
                        "format_or_runtime": "GGUF Q4_K_M",
                        "benchmark_run_id": "fit-ready-run",
                        "local_runner": "lmstudio-cli",
                        "local_model_id": "fit-ready-7b-q4_k_m",
                        "runtime_availability": "already installed",
                    }
                )

            db.init_db(database_path, reset=True)
            with db.connect(database_path) as conn:
                conn.execute(
                    """
                    INSERT INTO models (id, model_name, model_family, provider, params_b)
                    VALUES (1, 'Fit Ready 7B', 'Fit', 'local', 7)
                    """
                )
                conn.execute(
                    """
                    INSERT INTO model_runs (
                        id, model_id, date_tested, backend, quantization,
                        tokens_per_sec, run_notes
                    )
                    VALUES (
                        1, 1, '2026-07-14', 'LM Studio CLI', 'Q4_K_M', 31.2,
                        'benchmark_run_id=fit-ready-run | candidate_id=fit-ready-7b'
                    )
                    """
                )
                conn.commit()

                discover_html = server._radar(
                    conn,
                    registry_path=registry_path,
                    project_registry_path=root / "projects.csv",
                    hardware_profiles_dir=hardware_dir,
                )
                inventory_html = server._inventory(
                    inventory_result={
                        "checked_at": "2026-07-14T12:00:00Z",
                        "checks": [],
                        "models": [
                            {
                                "runtime": "LM Studio",
                                "model_id": "fit-ready-7b-q4_k_m",
                                "display_name": "Fit Ready 7B",
                                "status": "loaded",
                            }
                        ],
                    },
                    registry_path=registry_path,
                    run_history=server._inventory_run_history(conn),
                    hardware_profiles_dir=hardware_dir,
                )
                home_html = server._overview(
                    conn,
                    registry_path=registry_path,
                    local_inventory_path=root / "local-inventory.csv",
                    eval_results_dir=root / "eval-results",
                    hardware_profiles_dir=hardware_dir,
                )

        for surface, html in (
            ("Discover", discover_html),
            ("My Models", inventory_html),
        ):
            with self.subTest(surface=surface):
                self.assertIn('class="pill fit-pill fit-comfortable"', html)
                self.assertIn("Fit: comfortable", html)
                self.assertIn("GB est.", html)
                self.assertIn("Observed 31.2 tok/s", html)
                self.assertIn('class="metric-tip"', html)

        self.assertIn("This Machine", home_html)
        self.assertIn('class="pill fit-pill fit-capacity"', home_html)
        self.assertIn("Fit: up to ~40 GB est. weights", home_html)
        self.assertIn('class="metric-tip"', home_html)

        for html in (discover_html, inventory_html, home_html):
            for chunk in html.split("<script")[1:]:
                self.assertNotIn("src=", chunk.split(">", 1)[0])
            self.assertNotIn("<link", html)


if __name__ == "__main__":
    unittest.main()
