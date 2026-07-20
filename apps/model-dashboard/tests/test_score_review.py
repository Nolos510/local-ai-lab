import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import db, score_review  # noqa: E402
from model_dashboard.pages import actions  # noqa: E402
from model_dashboard.pages import artifact as artifact_page  # noqa: E402
from model_dashboard.pages import review as review_page  # noqa: E402
from model_dashboard.scoring import METRIC_FIELDS  # noqa: E402


def score_record(value=80, label="LOCAL_AI_ASSISTANT", model="judge-a"):
    return {
        "id": 1,
        "run_id": 1,
        "score_status": "draft",
        "scores": {field: float(value) for field in METRIC_FIELDS},
        "total_score": float(value),
        "final_label": label,
        "judge": {"model": model},
    }


class ScoreReviewTests(unittest.TestCase):
    def test_review_next_action_maps_integrity_and_disagreement_states(self):
        self.assertEqual(
            review_page._review_next_action({"status": "draft"}),
            "Await independent reviewer",
        )
        self.assertEqual(
            review_page._review_next_action({"flags": ["capture_errors_present"]}),
            "Rerun capture before scoring",
        )
        self.assertEqual(
            review_page._review_next_action({"flags": ["primary_all_scores_zero"]}),
            "Rescore or retire shared-zero evidence",
        )
        self.assertEqual(
            review_page._review_next_action({"flags": ["label"]}),
            "Adjudicate the final label",
        )
        self.assertEqual(
            review_page._review_next_action({"flags": ["metric_delta"]}),
            "Inspect metric deltas",
        )

    def test_independent_scores_within_threshold_become_machine_reviewed(self):
        primary = score_record(80, model="judge-a")
        reviewer = score_record(84, model="judge-b")

        result = score_review.compare_independent_scores(primary, reviewer)

        self.assertEqual(result["status"], "machine_reviewed")
        self.assertEqual(result["primary_judge"], "judge-a")
        self.assertEqual(result["reviewer_judge"], "judge-b")
        self.assertEqual(result["mean_metric_delta"], 4.0)
        self.assertTrue(result["label_agreement"])

    def test_large_or_label_disagreement_routes_to_human_review(self):
        primary = score_record(80, "LOCAL_AI_ASSISTANT", "judge-a")
        reviewer = score_record(55, "WATCHLIST", "judge-b")

        result = score_review.compare_independent_scores(primary, reviewer)

        self.assertEqual(result["status"], "disagreement")
        self.assertFalse(result["label_agreement"])
        self.assertEqual(result["max_metric_delta"], 25.0)
        self.assertIn("label", result["flags"])
        self.assertIn("metric_delta", result["flags"])

    def test_incomplete_reviewer_label_is_preserved_as_disagreement(self):
        primary = score_record(80, "LOCAL_AI_ASSISTANT", "judge-a")
        reviewer = score_record(82, model="judge-b")
        reviewer["final_label"] = None
        reviewer["suggestion_warnings"] = [
            "final_label_missing",
            "rationale_missing",
        ]

        result = score_review.compare_independent_scores(primary, reviewer)

        self.assertEqual(result["status"], "disagreement")
        self.assertIsNone(result["reviewer_label"])
        self.assertIn("reviewer_label_missing", result["flags"])
        self.assertIn("reviewer_output_incomplete", result["flags"])
        self.assertEqual(
            result["reviewer_output_warnings"],
            ["final_label_missing", "rationale_missing"],
        )

    def test_all_zero_score_agreement_is_not_machine_reviewed(self):
        primary = score_record(0, "WATCHLIST", "judge-a")
        reviewer = score_record(0, "WATCHLIST", "judge-b")

        result = score_review.compare_independent_scores(primary, reviewer)

        self.assertEqual(result["status"], "disagreement")
        self.assertIn("primary_all_scores_zero", result["flags"])
        self.assertIn("reviewer_all_scores_zero", result["flags"])

    def test_primary_suggestion_warnings_require_human_review(self):
        primary = score_record(80, model="judge-a")
        primary["suggestion_warnings"] = ["metric_rationales_incomplete"]
        reviewer = score_record(82, model="judge-b")

        result = score_review.compare_independent_scores(primary, reviewer)

        self.assertEqual(result["status"], "disagreement")
        self.assertIn("primary_output_incomplete", result["flags"])
        self.assertEqual(
            result["primary_output_warnings"],
            ["metric_rationales_incomplete"],
        )

    def test_capture_error_forces_disagreement_and_blocks_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "capture-error"
            run_dir.mkdir()
            primary = score_record(80, model="judge-a")
            reviewer = score_record(82, model="judge-b")
            (run_dir / "draft-scores.json").write_text(
                json.dumps(primary),
                encoding="utf-8",
            )
            (run_dir / "review-scores.json").write_text(
                json.dumps(reviewer),
                encoding="utf-8",
            )
            (run_dir / "raw_responses.jsonl").write_text(
                json.dumps(
                    {
                        "raw_response": "local runtime error",
                        "error": "provider unavailable",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                score_review.compare_independent_scores(primary, reviewer),
            )

            state = score_review.review_state(run_dir)

            self.assertEqual(state["status"], "disagreement")
            self.assertIn("capture_errors_present", state["flags"])
            self.assertEqual(state["capture_evidence"]["error_count"], 1)
            self.assertEqual(
                score_review.confirmable_agreement_ids(Path(tmp)),
                [],
            )

    def test_automatic_disposition_routes_objective_failures_without_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_error = root / "capture-error"
            capture_error.mkdir()
            (capture_error / "raw_responses.jsonl").write_text(
                '{"raw_response":"runtime failure","error":"provider unavailable"}\n',
                encoding="utf-8",
            )
            (capture_error / "draft-scores.json").write_text(
                json.dumps(score_record(80)),
                encoding="utf-8",
            )
            all_zero = root / "all-zero"
            all_zero.mkdir()
            (all_zero / "raw_responses.jsonl").write_text(
                '{"raw_response":"usable answer"}\n',
                encoding="utf-8",
            )
            (all_zero / "draft-scores.json").write_text(
                json.dumps(score_record(0, "WATCHLIST")),
                encoding="utf-8",
            )
            embedding = root / "embedding"
            embedding.mkdir()
            (embedding / "metadata.json").write_text(
                json.dumps({"model": {"model_name": "bge-m3:latest"}}),
                encoding="utf-8",
            )
            (embedding / "raw_responses.jsonl").write_text(
                '{"raw_response":"vector output"}\n',
                encoding="utf-8",
            )
            (embedding / "draft-scores.json").write_text(
                json.dumps(score_record(80)),
                encoding="utf-8",
            )
            valid = root / "valid"
            valid.mkdir()
            (valid / "raw_responses.jsonl").write_text(
                '{"raw_response":"usable answer"}\n',
                encoding="utf-8",
            )
            (valid / "draft-scores.json").write_text(
                json.dumps(score_record(80)),
                encoding="utf-8",
            )

            self.assertEqual(
                score_review.automatic_disposition(capture_error)["recommended_action"],
                "rerun_capture",
            )
            self.assertEqual(
                score_review.automatic_disposition(all_zero)["recommended_action"],
                "rescore",
            )
            self.assertEqual(
                score_review.automatic_disposition(embedding)["recommended_action"],
                "route_to_role_evaluation",
            )
            self.assertIsNone(score_review.automatic_disposition(valid))
            self.assertEqual(score_review.reviewable_artifact_ids(root), ["valid"])

    def test_automatic_quarantine_removes_draft_score_but_preserves_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "all-zero-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"usable answer"}\n',
                encoding="utf-8",
            )
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record(0, "WATCHLIST")),
                encoding="utf-8",
            )
            db_path = root / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute("INSERT INTO models (id, model_name) VALUES (1, 'Fixture')")
                conn.execute(
                    "INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes) "
                    "VALUES (1, 1, '2026-07-18', 'fixture', ?)",
                    (f"benchmark_run_id={run_id}",),
                )
                values = [1, 1] + [0.0] * len(METRIC_FIELDS) + [
                    0.0,
                    "WATCHLIST",
                    "draft",
                ]
                conn.execute(
                    "INSERT INTO eval_scores VALUES ({})".format(
                        ",".join("?" for _ in values)
                    ),
                    values,
                )
                conn.commit()

            result = actions._auto_reject_invalid_artifacts(db_path, root)

            self.assertEqual(len(result["rejected"]), 1)
            self.assertEqual(result["rejected"][0]["recommended_action"], "rescore")
            self.assertTrue((run_dir / "raw_responses.jsonl").is_file())
            self.assertTrue((run_dir / "draft-scores.json").is_file())
            state = score_review.review_state(run_dir)
            self.assertEqual(state["status"], "rejected")
            self.assertEqual(state["human_action"], "automatic_invalid_evidence")
            with db.connect(db_path) as conn:
                self.assertEqual(db.table_count(conn, "eval_scores"), 0)

    def test_automatic_quarantine_routes_empty_capture_before_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "empty-capture"
            run_dir.mkdir()
            (run_dir / "metadata.json").write_text(
                json.dumps({"model": {"model_name": "Qwen local"}}),
                encoding="utf-8",
            )

            result = actions._auto_reject_invalid_artifacts(
                root / "dashboard.sqlite",
                root,
            )

            self.assertEqual(len(result["rejected"]), 1)
            self.assertEqual(
                result["rejected"][0]["recommended_action"],
                "rerun_capture",
            )
            state = score_review.review_state(run_dir)
            self.assertEqual(state["status"], "rejected")
            self.assertIn("capture_evidence_missing", state["flags"])

    def test_confirmed_score_uses_human_edits_and_recalculates_total(self):
        primary = score_record(80)
        edits = {field: 90 for field in METRIC_FIELDS}
        edits["reasoning"] = 70

        result = score_review.build_confirmed_score(
            primary,
            edits,
            "CODING_SPECIALIST",
            reviewer="dashboard-human",
        )

        self.assertEqual(result["score_status"], "confirmed")
        self.assertEqual(result["scores"]["reasoning"], 70.0)
        self.assertEqual(result["total_score"], 88.18)
        self.assertEqual(result["final_label"], "CODING_SPECIALIST")
        self.assertEqual(result["human_confirmation"]["reviewer"], "dashboard-human")

    def test_review_queue_excludes_confirmed_machine_reviewed_and_rejected_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for run_id in (
                "needs-review",
                "machine-reviewed",
                "disagreement",
                "rejected",
                "confirmed",
            ):
                run_dir = root / run_id
                run_dir.mkdir()
                (run_dir / "draft-scores.json").write_text(
                    json.dumps(score_record()),
                    encoding="utf-8",
                )
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"raw_response":"answer"}\n',
                    encoding="utf-8",
                )
            (root / "machine-reviewed" / "score-review.json").write_text(
                json.dumps({"status": "machine_reviewed"}),
                encoding="utf-8",
            )
            (root / "disagreement" / "score-review.json").write_text(
                json.dumps({"status": "disagreement"}),
                encoding="utf-8",
            )
            (root / "rejected" / "score-review.json").write_text(
                json.dumps({"status": "rejected"}),
                encoding="utf-8",
            )
            (root / "confirmed" / "scores.json").write_text(
                json.dumps(score_record()),
                encoding="utf-8",
            )

            self.assertEqual(
                score_review.reviewable_artifact_ids(root),
                ["needs-review"],
            )

    def test_review_state_is_derived_without_mutating_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            draft = score_record()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(draft),
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                {"status": "rejected", "flags": ["human_rejected"]},
            )

            self.assertEqual(score_review.review_state(run_dir)["status"], "rejected")
            self.assertEqual(
                json.loads((run_dir / "draft-scores.json").read_text(encoding="utf-8")),
                draft,
            )

    def test_reviewer_preflight_requires_a_different_model(self):
        with self.assertRaisesRegex(ValueError, "different model"):
            actions._reviewer_preflight(
                "http://127.0.0.1:1234/v1",
                "judge-a",
                "http://127.0.0.1:1234/v1",
                "judge-a",
                5,
            )

        with mock.patch.object(
            actions,
            "_judge_preflight",
            return_value={"model": "judge-b", "available_models": 2},
        ):
            result = actions._reviewer_preflight(
                "http://127.0.0.1:1234/v1",
                "judge-b",
                "http://127.0.0.1:1234/v1",
                "judge-a",
                5,
            )

        self.assertEqual(result["model"], "judge-b")

    def test_independent_review_is_blind_and_writes_review_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "review-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record(80, model="judge-a")),
                encoding="utf-8",
            )
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"answer"}\n',
                encoding="utf-8",
            )
            review_path = run_dir / "review-scores.json"

            def fake_suggest(*_args, **kwargs):
                self.assertEqual(kwargs["output_path"], review_path.resolve())
                kwargs["output_path"].write_text(
                    json.dumps(score_record(84, model="judge-b")),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr=""), review_path

            with (
                mock.patch.object(
                    actions,
                    "_suggest_draft_scores",
                    side_effect=fake_suggest,
                ) as suggest,
                mock.patch.object(
                    actions,
                    "_export_dashboard_import",
                    return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                ) as export,
                mock.patch.object(
                    actions,
                    "_import_artifact",
                    return_value={"benchmark_run_id": run_id, "counts": {}},
                ) as import_artifact,
            ):
                result = actions._review_artifact(
                    run_id,
                    root,
                    5,
                    "http://127.0.0.1:1234/v1",
                    "judge-b",
                    root / "dashboard.sqlite",
                )

            self.assertEqual(result["status"], "machine_reviewed")
            self.assertEqual(suggest.call_args.args[0], run_id)
            self.assertNotIn("draft-scores.json", str(suggest.call_args))
            export.assert_called_once_with(
                run_id,
                root,
                5,
                scores_path=(run_dir / "draft-scores.json").resolve(),
            )
            import_artifact.assert_called_once()
            stored = json.loads((run_dir / "score-review.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["reviewer_judge"], "judge-b")

    def test_human_confirmation_requires_acknowledgement_and_writes_confirmed_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "confirm-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record(80, model="judge-a")),
                encoding="utf-8",
            )
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"answer"}\n',
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                score_review.compare_independent_scores(
                    score_record(80, model="judge-a"),
                    score_record(84, model="judge-b"),
                ),
            )
            edits = {field: ["90"] for field in METRIC_FIELDS}
            edits.update(
                {
                    "human_reviewed": ["yes"],
                    "confirmation_mode": ["edited"],
                    "final_label": ["CODING_SPECIALIST"],
                }
            )

            with (
                mock.patch.object(
                    actions,
                    "_export_dashboard_import",
                    return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                ),
                mock.patch.object(
                    actions,
                    "_import_artifact",
                    return_value={"benchmark_run_id": run_id, "counts": {"eval_scores": 1}},
                ),
            ):
                result = actions._confirm_artifact_score(
                    run_id,
                    edits,
                    Path("/fake/dashboard.sqlite"),
                    root,
                    5,
                )

            confirmed = json.loads((run_dir / "scores.json").read_text(encoding="utf-8"))
            self.assertEqual(confirmed["score_status"], "confirmed")
            self.assertEqual(confirmed["total_score"], 90.0)
            self.assertEqual(confirmed["final_label"], "CODING_SPECIALIST")
            self.assertEqual(result["status"], "confirmed")
            self.assertEqual(score_review.review_state(run_dir)["status"], "confirmed")

            with self.assertRaisesRegex(ValueError, "Human review acknowledgement"):
                actions._confirm_artifact_score(
                    run_id,
                    {"confirmation_mode": ["primary"]},
                    Path("/fake/dashboard.sqlite"),
                    root,
                    5,
                )

    def test_human_confirmation_requires_independent_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "unreviewed-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record()),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Independent review is required"):
                actions._confirm_artifact_score(
                    run_id,
                    {"human_reviewed": ["yes"], "confirmation_mode": ["primary"]},
                    root / "dashboard.sqlite",
                    root,
                    5,
                )

    def test_confirmable_agreements_exclude_disagreements_and_invalid_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agreement = root / "agreement"
            disagreement = root / "disagreement"
            invalid = root / "invalid"
            for run_dir in (agreement, disagreement, invalid):
                run_dir.mkdir()
                (run_dir / "metadata.json").write_text(
                    json.dumps({"model": {"model_name": "Qwen 14B"}}),
                    encoding="utf-8",
                )
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"raw_response":"answer"}\n',
                    encoding="utf-8",
                )
            agreement_primary = score_record(80, model="judge-a")
            agreement_reviewer = score_record(84, model="judge-b")
            for name, payload in (
                ("draft-scores.json", agreement_primary),
                ("review-scores.json", agreement_reviewer),
            ):
                (agreement / name).write_text(json.dumps(payload), encoding="utf-8")
            score_review.write_review_record(
                agreement,
                score_review.compare_independent_scores(
                    agreement_primary,
                    agreement_reviewer,
                ),
            )
            disagreement_primary = score_record(80, model="judge-a")
            disagreement_reviewer = score_record(40, model="judge-b")
            for name, payload in (
                ("draft-scores.json", disagreement_primary),
                ("review-scores.json", disagreement_reviewer),
            ):
                (disagreement / name).write_text(json.dumps(payload), encoding="utf-8")
            score_review.write_review_record(
                disagreement,
                score_review.compare_independent_scores(
                    disagreement_primary,
                    disagreement_reviewer,
                ),
            )
            (invalid / "draft-scores.json").write_text(
                json.dumps(score_record()),
                encoding="utf-8",
            )
            score_review.write_review_record(invalid, {"status": "machine_reviewed"})

            self.assertEqual(
                score_review.confirmable_agreement_ids(root),
                ["agreement"],
            )

    def test_batch_confirmation_requires_acknowledgement_and_agreements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "agreement"
            run_dir.mkdir()
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"answer"}\n',
                encoding="utf-8",
            )
            primary = score_record(80, model="judge-a")
            reviewer = score_record(84, model="judge-b")
            (run_dir / "draft-scores.json").write_text(
                json.dumps(primary),
                encoding="utf-8",
            )
            (run_dir / "review-scores.json").write_text(
                json.dumps(reviewer),
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                score_review.compare_independent_scores(primary, reviewer),
            )

            with self.assertRaisesRegex(ValueError, "Human review acknowledgement"):
                actions._confirm_reviewed_agreements(
                    ["agreement"],
                    {},
                    root / "dashboard.sqlite",
                    root,
                    5,
                )

            with mock.patch.object(
                actions,
                "_confirm_artifact_score",
                return_value={"status": "confirmed"},
            ) as confirm:
                result = actions._confirm_reviewed_agreements(
                    ["agreement"],
                    {"human_reviewed": ["yes"]},
                    root / "dashboard.sqlite",
                    root,
                    5,
                )

            self.assertEqual(result["confirmed"], 1)
            self.assertEqual(result["failed"], 0)
            confirm.assert_called_once()

            with self.assertRaisesRegex(ValueError, "review queue changed"):
                actions._confirm_reviewed_agreements(
                    ["not-reviewed"],
                    {"human_reviewed": ["yes"]},
                    root / "dashboard.sqlite",
                    root,
                    5,
                )

    def test_artifact_page_exposes_reviewed_draft_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "artifact-confirm-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "metadata.json").write_text(
                json.dumps({"model": {"model_name": "Qwen 14B"}}),
                encoding="utf-8",
            )
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record(80, model="judge-a")),
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                score_review.compare_independent_scores(
                    score_record(80, model="judge-a"),
                    score_record(84, model="judge-b"),
                ),
            )

            html = artifact_page._artifact_review_panel(
                run_id,
                run_dir,
                enable_score_actions=True,
                action_token="fixture-token",
                reviewer_model="judge-b",
            )

            self.assertIn("Confirm Draft Score", html)
            self.assertIn('action="/actions/confirm-score"', html)
            self.assertIn(f'/reviews/{run_id}', html)
            self.assertIn("Independent review never confirms automatically", html)

    def test_rejection_preserves_artifact_and_removes_imported_draft_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "reject-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record()),
                encoding="utf-8",
            )
            db_path = root / "dashboard.sqlite"
            db.init_db(db_path, reset=True)
            with db.connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO models (id, model_name) VALUES (1, 'Fixture')"
                )
                conn.execute(
                    "INSERT INTO model_runs (id, model_id, date_tested, backend, run_notes) "
                    "VALUES (1, 1, '2026-07-17', 'fixture', ?)",
                    (f"benchmark_run_id={run_id}",),
                )
                values = [1, 1] + [80.0] * len(METRIC_FIELDS) + [
                    80.0,
                    "LOCAL_AI_ASSISTANT",
                    "draft",
                ]
                conn.execute(
                    "INSERT INTO eval_scores VALUES ({})".format(
                        ",".join("?" for _ in values)
                    ),
                    values,
                )
                conn.commit()

            result = actions._reject_artifact_score(
                run_id,
                {"human_reviewed": ["yes"]},
                db_path,
                root,
            )

            self.assertEqual(result["status"], "rejected")
            self.assertTrue((run_dir / "draft-scores.json").is_file())
            self.assertEqual(score_review.review_state(run_dir)["status"], "rejected")
            with db.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM eval_scores").fetchone()[0], 0)

    def test_review_pages_expose_machine_review_and_human_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "page-run"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record(80, model="judge-a")),
                encoding="utf-8",
            )
            (run_dir / "raw_responses.jsonl").write_text(
                '{"raw_response":"answer"}\n',
                encoding="utf-8",
            )
            (run_dir / "review-scores.json").write_text(
                json.dumps(score_record(84, model="judge-b")),
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                score_review.compare_independent_scores(
                    score_record(80, model="judge-a"),
                    score_record(84, model="judge-b"),
                ),
            )

            queue_html = review_page._review_queue(
                root,
                enable_score_actions=True,
                action_token="fixture-token",
                reviewer_model="judge-b",
            )
            detail_html = review_page._review_detail(
                run_id,
                root,
                enable_score_actions=True,
                action_token="fixture-token",
                reviewer_model="judge-b",
            )

            self.assertIn("Draft Review Queue", queue_html)
            self.assertIn("machine reviewed", queue_html.lower())
            self.assertIn("evidence owner, not another judge", queue_html)
            self.assertIn("Rerun</strong> is the safest choice", queue_html)
            self.assertIn(f'/reviews/{run_id}', queue_html)
            self.assertIn('action="/actions/confirm-score"', detail_html)
            self.assertIn('value="primary"', detail_html)
            self.assertIn('value="edited"', detail_html)
            self.assertIn('action="/actions/reject-score"', detail_html)
            self.assertIn("does not confirm the score", detail_html)
            self.assertIn("Choose by evidence quality", detail_html)
            self.assertIn(
                'action="/actions/confirm-reviewed-agreements"',
                queue_html,
            )
            self.assertIn("Confirm 1 reviewed agreement", queue_html)
            self.assertIn("Disagreements remain", queue_html)
            self.assertIn("Inspect evidence and resolve", queue_html)

    def test_review_queue_hides_invalid_and_rejected_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = root / "valid-disagreement"
            invalid = root / "all-zero"
            rejected = root / "owner-rejected"
            for run_dir in (valid, invalid, rejected):
                run_dir.mkdir()
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"raw_response":"usable answer"}\n',
                    encoding="utf-8",
                )
            (valid / "draft-scores.json").write_text(
                json.dumps(score_record(80, model="judge-a")),
                encoding="utf-8",
            )
            (valid / "review-scores.json").write_text(
                json.dumps(score_record(55, "WATCHLIST", "judge-b")),
                encoding="utf-8",
            )
            score_review.write_review_record(
                valid,
                score_review.compare_independent_scores(
                    score_record(80, model="judge-a"),
                    score_record(55, "WATCHLIST", "judge-b"),
                ),
            )
            (invalid / "draft-scores.json").write_text(
                json.dumps(score_record(0, "WATCHLIST")),
                encoding="utf-8",
            )
            (rejected / "draft-scores.json").write_text(
                json.dumps(score_record(80)),
                encoding="utf-8",
            )
            score_review.write_review_record(
                rejected,
                {"status": "rejected", "human_action": "rejected"},
            )

            html = review_page._review_queue(root, query={"scope": ["all"]})

            self.assertIn("valid-disagreement", html)
            self.assertIn("judge disagreement", html)
            self.assertNotIn("/reviews/all-zero", html)
            self.assertNotIn("/reviews/owner-rejected", html)

    def test_rejected_review_detail_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "owner-rejected"
            run_dir = root / run_id
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record(80)),
                encoding="utf-8",
            )
            score_review.write_review_record(
                run_dir,
                {"status": "rejected", "human_action": "rejected"},
            )

            html = review_page._review_detail(
                run_id,
                root,
                enable_score_actions=True,
                action_token="fixture-token",
                reviewer_model="judge-b",
            )

            self.assertIn("Rejected evidence", html)
            self.assertIn("cannot be confirmed", html)
            self.assertNotIn('action="/actions/reject-score"', html)
            self.assertNotIn("You can still edit and confirm", html)

    def test_independent_review_queue_excludes_artifacts_without_raw_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "empty-evidence"
            run_dir.mkdir()
            (run_dir / "draft-scores.json").write_text(
                json.dumps(score_record()),
                encoding="utf-8",
            )

            self.assertEqual(score_review.reviewable_artifact_ids(root), [])
            result = actions._review_artifact(
                "empty-evidence",
                root,
                5,
                "http://127.0.0.1:1234/v1",
                "judge-b",
            )

            self.assertEqual(result["status"], "rejected")
            self.assertEqual(result["recommended_action"], "rerun_capture")

    def test_review_queue_defaults_to_imported_dashboard_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for run_id in ("current-run", "archival-run"):
                run_dir = root / run_id
                run_dir.mkdir()
                (run_dir / "draft-scores.json").write_text(
                    json.dumps(score_record()),
                    encoding="utf-8",
                )
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"prompt_id":"one","raw_response":"answer"}\n',
                    encoding="utf-8",
                )

            database_path = root / "dashboard.sqlite"
            db.init_db(database_path, reset=True)
            with db.connect(database_path) as conn:
                conn.execute(
                    "INSERT INTO models (id, model_name, provider, source_url) "
                    "VALUES (1, 'Current Model', 'LM Studio', 'local://current')"
                )
                conn.execute(
                    "INSERT INTO model_runs "
                    "(id, model_id, date_tested, backend, run_notes) "
                    "VALUES (1, 1, '2026-07-18', 'lmstudio-cli', "
                    "'benchmark_run_id=current-run')"
                )
                metric_columns = ", ".join(METRIC_FIELDS)
                metric_placeholders = ", ".join("?" for _ in METRIC_FIELDS)
                conn.execute(
                    f"INSERT INTO eval_scores "
                    f"(id, run_id, {metric_columns}, total_score, final_label, score_status) "
                    f"VALUES (?, ?, {metric_placeholders}, ?, ?, ?)",
                    (1, 1, *([80] * len(METRIC_FIELDS)), 80, "LOCAL_AI_ASSISTANT", "draft"),
                )

                current_html = review_page._review_queue(
                    root,
                    conn=conn,
                    enable_score_actions=True,
                    action_token="fixture-token",
                    reviewer_model="judge-b",
                )
                all_html = review_page._review_queue(
                    root,
                    conn=conn,
                    query={"scope": ["all"]},
                    enable_score_actions=True,
                    action_token="fixture-token",
                    reviewer_model="judge-b",
                )

            self.assertIn('/reviews/current-run', current_html)
            self.assertNotIn('/reviews/archival-run', current_html)
            self.assertIn('value="current-run"', current_html)
            self.assertNotIn('value="archival-run"', current_html)
            self.assertIn("Current dashboard (1)", current_html)
            self.assertIn("All artifacts (2)", current_html)
            self.assertIn('/reviews/current-run', all_html)
            self.assertIn('/reviews/archival-run', all_html)

    def test_review_queue_excludes_embedding_artifacts_from_generative_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for run_id, model_name in (
                ("generator-run", "Qwen 14B"),
                ("embedding-run", "bge-m3:latest"),
            ):
                run_dir = root / run_id
                run_dir.mkdir()
                (run_dir / "metadata.json").write_text(
                    json.dumps({"model": {"model_name": model_name}}),
                    encoding="utf-8",
                )
                (run_dir / "draft-scores.json").write_text(
                    json.dumps(score_record()),
                    encoding="utf-8",
                )
                (run_dir / "raw_responses.jsonl").write_text(
                    '{"prompt_id":"one","raw_response":"answer"}\n',
                    encoding="utf-8",
                )

            html = review_page._review_queue(
                root,
                enable_score_actions=True,
                action_token="fixture-token",
                reviewer_model="judge-b",
            )

            self.assertIn('/reviews/generator-run', html)
            self.assertNotIn('/reviews/embedding-run', html)
            self.assertIn("retrieval-specific evaluation", html)

    def test_review_batch_continues_after_per_artifact_failure(self):
        status = actions._new_review_batch_status("batch", ["one", "two"])

        def fake_review(run_id, *_args):
            if run_id == "one":
                raise ValueError("review unavailable")
            return {"benchmark_run_id": run_id, "status": "machine_reviewed"}

        with mock.patch.object(actions, "_review_artifact", side_effect=fake_review):
            actions._background_review_batch(
                ["one", "two"],
                Path("/fake/evals"),
                5,
                "http://127.0.0.1:1234/v1",
                "judge-b",
                status,
            )

        self.assertEqual(status["state"], "complete")
        self.assertEqual([row["status"] for row in status["results"]], ["failed", "passed"])
        self.assertEqual(
            status["results"][0]["reason"],
            "Independent review did not complete; inspect the local reviewer and retry.",
        )


if __name__ == "__main__":
    unittest.main()
