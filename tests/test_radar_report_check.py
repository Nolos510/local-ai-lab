from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "radar_report_check.py"
SPEC = importlib.util.spec_from_file_location("radar_report_check", SCRIPT_PATH)
assert SPEC and SPEC.loader
radar_report_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(radar_report_check)


def project_fields() -> dict[str, str]:
    fields = {field: "value" for field in radar_report_check.PROJECT_REQUIRED_FIELDS}
    fields.update(
        {
            "project_id": "20260718-example",
            "project_name": "Example Project",
            "source_url": "https://example.com/project",
            "item_type": "`project_opportunity`",
            "recommended_next_step": "`watchlist`: review only",
            "cost_as_of": "2026-07-18",
            "incremental_cost": "$0-$25",
            "from_scratch_cost": "$100-$150",
            "portfolio_build_cost": "$200-$250",
            "recurring_monthly_cost": "$0-$3/month",
            "cost_confidence": "Medium. Public prices are visible.",
            "cost_source_urls": "https://example.com/pricing",
            "source_last_checked": "2026-07-18",
            "price_valid_until": "2026-08-17",
            "first_seen": "2026-07-18",
            "last_seen": "2026-07-18",
            "change_status": "`new`",
            "first_three_tasks": "1. Confirm scope. 2. Draft artifact. 3. Review boundaries.",
        }
    )
    return fields


class RadarReportCheckTests(unittest.TestCase):
    def test_current_daily_report_passes(self) -> None:
        report = (
            REPO_ROOT
            / "automations/ai-lab-radar/reports/2026-07-18-daily-external-radar.md"
        )
        errors = radar_report_check.validate_daily_report(
            report, report.read_text(encoding="utf-8")
        )
        self.assertEqual(errors, [])

    def test_project_missing_required_cost_field_fails(self) -> None:
        fields = project_fields()
        del fields["cost_source_urls"]
        errors = radar_report_check.validate_project("Example Project", fields)
        self.assertTrue(any("cost_source_urls" in error for error in errors))

    def test_project_requires_confidence_disposition_and_safety(self) -> None:
        for field in ("cost_confidence", "recommended_next_step", "safety_notes"):
            with self.subTest(field=field):
                fields = project_fields()
                del fields[field]
                errors = radar_report_check.validate_project("Example Project", fields)
                self.assertTrue(any(field in error for error in errors))

    def test_project_requires_plain_language_explainer_fields(self) -> None:
        for field in (
            "plain_language_summary",
            "problem_it_solves",
            "who_it_is_for",
            "common_use_cases",
            "how_it_works_in_practice",
            "ai_lab_use_case",
            "limitations",
        ):
            with self.subTest(field=field):
                fields = project_fields()
                del fields[field]
                errors = radar_report_check.validate_project("Example Project", fields)
                self.assertTrue(any(field in error for error in errors))

    def test_project_with_every_cash_price_unknown_fails(self) -> None:
        fields = project_fields()
        for field in radar_report_check.CASH_FIELDS:
            fields[field] = "unknown"
        errors = radar_report_check.validate_project("Example Project", fields)
        self.assertTrue(any("every cash price field unknown" in error for error in errors))

    def test_project_price_validity_over_30_days_fails(self) -> None:
        fields = project_fields()
        fields["price_valid_until"] = "2026-08-18"
        errors = radar_report_check.validate_project("Example Project", fields)
        self.assertTrue(any("cannot exceed 30 days" in error for error in errors))

    def test_profile_accepts_unknown_user_preferences(self) -> None:
        profile = {
            "profile_version": 1,
            "available_hardware": [],
            "budget_tiers": {
                "weekend_project_usd": 100,
                "sub_300_build_usd": 300,
                "portfolio_investment_usd": None,
            },
            "max_diy_hours": None,
            "priority_categories": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            self.assertEqual(radar_report_check.validate_profile(path), [])

    def test_daily_report_requires_action_card_for_every_project(self) -> None:
        report = (
            REPO_ROOT
            / "automations/ai-lab-radar/reports/2026-07-18-daily-external-radar.md"
        )
        text = report.read_text(encoding="utf-8").replace(
            "### WildBridge\n\n| Field | Value |",
            "### Removed WildBridge\n\n| Field | Value |",
            1,
        )
        errors = radar_report_check.validate_daily_report(report, text)
        self.assertTrue(any("MVP action card for 'WildBridge'" in error for error in errors))

    def test_daily_report_requires_explainer_for_every_project(self) -> None:
        report = (
            REPO_ROOT
            / "automations/ai-lab-radar/reports/2026-07-18-daily-external-radar.md"
        )
        text = report.read_text(encoding="utf-8").replace(
            "### WildBridge\n\n| Question | Plain-language answer |",
            "### Removed WildBridge\n\n| Question | Plain-language answer |",
            1,
        )
        errors = radar_report_check.validate_daily_report(report, text)
        self.assertTrue(any("project explainer for 'WildBridge'" in error for error in errors))

    def test_weekly_report_requires_shortlist_sections(self) -> None:
        text = "# AI Lab Radar Weekly Rollup\n\n## Weekly Shortlist\n"
        errors = radar_report_check.validate_weekly_report(text)
        self.assertTrue(any("Best Project" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
