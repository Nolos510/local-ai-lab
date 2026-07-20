#!/usr/bin/env python3
"""Validate AI Lab Radar reports and their source packets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_REQUIRED_FIELDS = (
    "project_id",
    "project_name",
    "source_url",
    "item_type",
    "priority_score",
    "priority_rationale",
    "plain_language_summary",
    "problem_it_solves",
    "who_it_is_for",
    "common_use_cases",
    "how_it_works_in_practice",
    "ai_lab_use_case",
    "limitations",
    "why_interesting",
    "business_tie_in",
    "learning_value",
    "local_fit",
    "risk_notes",
    "recommended_next_step",
    "cost_currency",
    "cost_as_of",
    "cost_scope",
    "incremental_cost",
    "from_scratch_cost",
    "portfolio_build_cost",
    "diy_effort_hours",
    "recurring_monthly_cost",
    "cost_confidence",
    "cost_assumptions",
    "cost_exclusions",
    "cost_source_urls",
    "source_last_checked",
    "price_valid_until",
    "refresh_reason",
    "first_seen",
    "last_seen",
    "change_status",
    "change_summary",
    "one_week_deliverable",
    "success_criteria",
    "demo_artifact",
    "prerequisites",
    "first_three_tasks",
    "blockers",
    "stop_conditions",
    "safety_notes",
)

MODEL_REQUIRED_FIELDS = (
    "candidate_id",
    "model_name",
    "source_url",
    "why_interesting",
    "risk_notes",
    "security_review_status",
    "download_approval",
    "provenance_status",
    "recommended_next_step",
    "estimated_artifact_size",
    "estimated_disk_requirement",
    "expected_memory_range",
    "compatible_local_runtimes",
    "benchmark_gap",
    "source_last_checked",
    "first_seen",
    "last_seen",
    "change_status",
    "change_summary",
)

DAILY_REPORT_HEADINGS = (
    "Summary",
    "Delta Summary",
    "Candidate Review",
    "Model Practicality",
    "Project Explainers",
    "Project Priority Review",
    "Project Cost Estimates",
    "Effort-Versus-Value View",
    "MVP Action Cards",
    "Import Or Task Notes",
    "Safety Posture",
)

WEEKLY_REPORT_HEADINGS = (
    "Weekly Shortlist",
    "Best Project",
    "Best Model Candidate",
    "Cheapest Useful Build",
    "Strongest Portfolio Opportunity",
    "Delta Summary",
    "Next Approval Task",
    "Safety Posture",
)

ALLOWED_DISPOSITIONS = {
    "ready_for_eval",
    "ready_for_review",
    "watchlist",
    "skip",
    "needs_more_info",
}
ALLOWED_CHANGE_STATUSES = {"new", "material_change"}
CASH_FIELDS = (
    "incremental_cost",
    "from_scratch_cost",
    "portfolio_build_cost",
    "recurring_monthly_cost",
)
ITEM_HEADER_RE = re.compile(
    r"^###\s+(model_candidate|project_opportunity):\s*(.+?)\s*$", re.MULTILINE
)
FIELD_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Radar report Markdown path")
    parser.add_argument(
        "--profile",
        type=Path,
        help="Optional local lab profile JSON; defaults to the ignored local profile when present",
    )
    parser.add_argument(
        "--kind",
        choices=("auto", "daily", "weekly"),
        default="auto",
        help="Report type; auto detects from title and filename",
    )
    return parser.parse_args()


def strip_code(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_iso_date(value: str, label: str, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(strip_code(value))
    except ValueError:
        errors.append(f"{label} must be an ISO date, got {value!r}")
        return None


def find_repo_root(path: Path) -> Path:
    start = path.resolve()
    if start.is_file():
        start = start.parent
    for parent in (start, *start.parents):
        if (parent / ".git").exists() or (
            (parent / "AGENTS.md").exists() and (parent / "automations").exists()
        ):
            return parent
    return Path.cwd().resolve()


def parse_item_sections(text: str) -> list[tuple[str, str, dict[str, str]]]:
    matches = list(ITEM_HEADER_RE.finditer(text))
    sections: list[tuple[str, str, dict[str, str]]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        fields: dict[str, str] = {}
        for line in text[match.end() : end].splitlines():
            field_match = FIELD_ROW_RE.match(line)
            if field_match:
                fields[field_match.group(1)] = field_match.group(2).strip()
        sections.append((match.group(1), match.group(2).strip(), fields))
    return sections


def require_fields(
    item_type: str,
    item_name: str,
    fields: dict[str, str],
    required: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    for field in required:
        if not fields.get(field, "").strip():
            errors.append(f"{item_type} {item_name!r} is missing required field `{field}`")
    return errors


def validate_delta_fields(item_name: str, fields: dict[str, str]) -> list[str]:
    errors: list[str] = []
    first_seen = parse_iso_date(fields.get("first_seen", ""), f"{item_name} first_seen", errors)
    last_seen = parse_iso_date(fields.get("last_seen", ""), f"{item_name} last_seen", errors)
    if first_seen and last_seen and first_seen > last_seen:
        errors.append(f"{item_name} first_seen must not be after last_seen")
    status = strip_code(fields.get("change_status", ""))
    if status not in ALLOWED_CHANGE_STATUSES:
        errors.append(
            f"{item_name} change_status must be one of {sorted(ALLOWED_CHANGE_STATUSES)}"
        )
    return errors


def validate_disposition(item_name: str, value: str) -> list[str]:
    normalized = strip_code(value).lower()
    if not any(disposition in normalized for disposition in ALLOWED_DISPOSITIONS):
        return [
            f"{item_name} recommended_next_step must include one of "
            f"{sorted(ALLOWED_DISPOSITIONS)}"
        ]
    return []


def validate_project(item_name: str, fields: dict[str, str]) -> list[str]:
    errors = require_fields("project_opportunity", item_name, fields, PROJECT_REQUIRED_FIELDS)
    if errors:
        return errors

    if strip_code(fields["item_type"]) != "project_opportunity":
        errors.append(f"{item_name} item_type must be `project_opportunity`")
    if not fields["source_url"].startswith(("http://", "https://")):
        errors.append(f"{item_name} source_url must be an HTTP(S) URL")
    if "http://" not in fields["cost_source_urls"] and "https://" not in fields["cost_source_urls"]:
        errors.append(f"{item_name} cost_source_urls must contain at least one HTTP(S) URL")

    if all("unknown" in fields[field].lower() for field in CASH_FIELDS):
        errors.append(f"{item_name} cannot mark every cash price field unknown")
    if not re.match(r"^(low|medium|high)\b", strip_code(fields["cost_confidence"]), re.I):
        errors.append(f"{item_name} cost_confidence must start with Low, Medium, or High")

    cost_as_of = parse_iso_date(fields["cost_as_of"], f"{item_name} cost_as_of", errors)
    checked = parse_iso_date(
        fields["source_last_checked"], f"{item_name} source_last_checked", errors
    )
    valid_until = parse_iso_date(
        fields["price_valid_until"], f"{item_name} price_valid_until", errors
    )
    if cost_as_of and checked and cost_as_of != checked:
        errors.append(f"{item_name} cost_as_of must match source_last_checked")
    if checked and valid_until:
        validity_days = (valid_until - checked).days
        if validity_days < 0:
            errors.append(f"{item_name} price_valid_until must not precede source_last_checked")
        elif validity_days > 30:
            errors.append(f"{item_name} hardware/public price validity cannot exceed 30 days")

    tasks = fields["first_three_tasks"]
    if not all(re.search(rf"(?:^|\s){number}\.\s", tasks) for number in (1, 2, 3)):
        errors.append(f"{item_name} first_three_tasks must contain ordered tasks 1, 2, and 3")

    errors.extend(validate_delta_fields(item_name, fields))
    errors.extend(validate_disposition(item_name, fields["recommended_next_step"]))
    return errors


def validate_model(item_name: str, fields: dict[str, str]) -> list[str]:
    errors = require_fields("model_candidate", item_name, fields, MODEL_REQUIRED_FIELDS)
    if errors:
        return errors
    if not fields["source_url"].startswith(("http://", "https://")):
        errors.append(f"{item_name} source_url must be an HTTP(S) URL")
    errors.extend(validate_delta_fields(item_name, fields))
    errors.extend(validate_disposition(item_name, fields["recommended_next_step"]))
    return errors


def validate_source_packet(path: Path) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return [f"source packet does not exist: {path}"], [], []
    text = path.read_text(encoding="utf-8")
    sections = parse_item_sections(text)
    if not sections:
        return [f"source packet has no candidate/project sections: {path}"], [], []

    projects: list[str] = []
    models: list[str] = []
    for item_type, item_name, fields in sections:
        if item_type == "project_opportunity":
            projects.append(item_name)
            errors.extend(validate_project(item_name, fields))
        else:
            models.append(item_name)
            errors.extend(validate_model(item_name, fields))
    return errors, projects, models


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", text[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end]


def validate_profile(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"lab profile does not exist: {path}"]
    except json.JSONDecodeError as exc:
        return [f"lab profile is not valid JSON: {exc}"]

    if not isinstance(data, dict):
        return ["lab profile root must be a JSON object"]
    for field in (
        "profile_version",
        "available_hardware",
        "budget_tiers",
        "max_diy_hours",
        "priority_categories",
    ):
        if field not in data:
            errors.append(f"lab profile is missing required field {field!r}")
    if "available_hardware" in data and not isinstance(data["available_hardware"], list):
        errors.append("lab profile available_hardware must be a list")
    if "priority_categories" in data and not isinstance(data["priority_categories"], list):
        errors.append("lab profile priority_categories must be a list")
    budget = data.get("budget_tiers")
    if not isinstance(budget, dict):
        errors.append("lab profile budget_tiers must be an object")
    else:
        for field in ("weekend_project_usd", "sub_300_build_usd", "portfolio_investment_usd"):
            if field not in budget:
                errors.append(f"lab profile budget_tiers is missing {field!r}")
    max_hours = data.get("max_diy_hours")
    if max_hours is not None and (not isinstance(max_hours, int) or max_hours < 0):
        errors.append("lab profile max_diy_hours must be a non-negative integer or null")
    return errors


def detect_kind(path: Path, text: str, requested: str) -> str:
    if requested != "auto":
        return requested
    if "weekly-rollup" in path.name or text.startswith("# AI Lab Radar Weekly Rollup"):
        return "weekly"
    return "daily"


def validate_weekly_report(text: str) -> list[str]:
    errors: list[str] = []
    for heading in WEEKLY_REPORT_HEADINGS:
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(f"weekly report is missing required heading: {heading}")
    if "http://127.0.0.1:8765/radar" not in text:
        errors.append("weekly report is missing the local dashboard link")
    return errors


def validate_daily_report(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for heading in DAILY_REPORT_HEADINGS:
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(f"daily report is missing required heading: {heading}")
    if "http://127.0.0.1:8765/radar" not in text:
        errors.append("daily report is missing the local dashboard link")

    source_match = re.search(r"^Source packet:\s*`([^`]+)`\s*$", text, re.MULTILINE)
    if not source_match:
        errors.append("daily report is missing a backticked Source packet path")
        return errors
    source_path = Path(source_match.group(1))
    if not source_path.is_absolute():
        source_path = find_repo_root(path) / source_path

    packet_errors, projects, models = validate_source_packet(source_path)
    errors.extend(packet_errors)
    cost_section = extract_section(text, "Project Cost Estimates")
    explainer_section = extract_section(text, "Project Explainers")
    action_section = extract_section(text, "MVP Action Cards")
    practicality_section = extract_section(text, "Model Practicality")
    delta_section = extract_section(text, "Delta Summary")
    for project in projects:
        if project not in cost_section:
            errors.append(f"daily report cost section does not mention project {project!r}")
        if not re.search(rf"^###\s+{re.escape(project)}\s*$", explainer_section, re.MULTILINE):
            errors.append(f"daily report is missing a project explainer for {project!r}")
        if not re.search(rf"^###\s+{re.escape(project)}\s*$", action_section, re.MULTILINE):
            errors.append(f"daily report is missing an MVP action card for {project!r}")
        if project not in delta_section:
            errors.append(f"daily report delta section does not mention project {project!r}")
    for model in models:
        if model not in practicality_section:
            errors.append(f"daily report model practicality section omits {model!r}")
        if model not in delta_section:
            errors.append(f"daily report delta section does not mention model {model!r}")
    return errors


def main() -> int:
    args = parse_args()
    report = args.report.resolve()
    if not report.exists():
        print(f"ERROR: report does not exist: {report}", file=sys.stderr)
        return 1
    text = report.read_text(encoding="utf-8")
    kind = detect_kind(report, text, args.kind)
    errors = (
        validate_weekly_report(text)
        if kind == "weekly"
        else validate_daily_report(report, text)
    )

    profile = args.profile
    if profile is None:
        local_profile = find_repo_root(report) / "automations/ai-lab-radar/lab-profile.local.json"
        if local_profile.exists():
            profile = local_profile
    if profile is not None:
        errors.extend(validate_profile(profile.resolve()))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} radar validation error(s)", file=sys.stderr)
        return 1
    print(f"PASS: {kind} radar report validated: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
