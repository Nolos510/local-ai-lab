#!/usr/bin/env python3
"""Generate a Markdown release-readiness report from a versioned JSON scorecard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _weighted_score(criteria):
    weight_total = sum(float(item["weight"]) for item in criteria)
    if abs(weight_total - 100.0) > 0.001:
        raise ValueError(f"Readiness weights must total 100; found {weight_total:g}.")
    for item in criteria:
        rating = float(item["rating"])
        if not 0 <= rating <= 5:
            raise ValueError(f"Rating for {item['criterion']} must be between 0 and 5.")
    score = sum(float(item["weight"]) * float(item["rating"]) / 5 for item in criteria)
    return round(score, 4)


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(scorecard):
    criteria = scorecard["criteria"]
    score = _weighted_score(criteria)
    gate = scorecard["release_gate"]
    critical = [risk for risk in scorecard.get("risks", []) if risk.get("severity") == "P0"]
    below_floor = [
        item for item in criteria if float(item["rating"]) < float(gate["minimum_criterion"])
    ]
    protected_names = set(gate["protected_criteria"])
    protected_below = [
        item
        for item in criteria
        if item["criterion"] in protected_names
        and float(item["rating"]) < float(gate["protected_minimum"])
    ]
    release_ready = (
        score >= float(gate["minimum_score"])
        and not critical
        and not below_floor
        and not protected_below
    )
    decision = "GO" if release_ready else "NO-GO"
    lines = [
        "# Local AI Lab Release-Readiness Assessment",
        "",
        f"- **Measured:** {_cell(scorecard['measured_at'])}",
        f"- **Evaluated revision:** `{_cell(scorecard['evaluated_revision'])}`",
        f"- **Patch state:** {_cell(scorecard['patch_state'])}",
        f"- **Weighted score:** **{score:.1f}/100**",
        f"- **Release decision:** **{decision}**",
        f"- **Previous baseline:** {float(scorecard['baseline_score']):.1f}/100",
        "",
        "## Executive Assessment",
        "",
        scorecard["executive_assessment"],
        "",
        "## Scorecard",
        "",
        "| Criterion | Weight | Rating | Confidence | Evidence | Blockers | Owner |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for item in criteria:
        lines.append(
            "| {criterion} | {weight:g} | {rating:.1f}/5 | {confidence} | {evidence} | "
            "{blockers} | {owner} |".format(
                criterion=_cell(item["criterion"]),
                weight=float(item["weight"]),
                rating=float(item["rating"]),
                confidence=_cell(item["confidence"]),
                evidence=_cell("; ".join(item["evidence"])),
                blockers=_cell("; ".join(item["blockers"]) or "None"),
                owner=_cell(item["owner"]),
            )
        )
    lines.extend(["", "## Release Gate", ""])
    if release_ready:
        lines.append("All score, category, and blocker gates are satisfied.")
    else:
        lines.append("The release gate is not satisfied:")
        if score < float(gate["minimum_score"]):
            lines.append(
                f"- Weighted score is {score:.1f}; required minimum is {gate['minimum_score']}."
            )
        if critical:
            lines.append(f"- {len(critical)} P0 release blocker(s) remain open.")
        if below_floor:
            names = ", ".join(item["criterion"] for item in below_floor)
            lines.append(f"- Criteria below {gate['minimum_criterion']}/5: {names}.")
        if protected_below:
            names = ", ".join(item["criterion"] for item in protected_below)
            lines.append(
                f"- Protected criteria below {gate['protected_minimum']}/5: {names}."
            )
    lines.extend(["", "## Evidence Register", ""])
    for item in scorecard["evidence_register"]:
        lines.append(
            f"- **{_cell(item['id'])}: {_cell(item['title'])}** "
            f"({_cell(item['confidence'])}) - {_cell(item['finding'])}"
        )
    lines.extend(["", "## Risk Register", ""])
    for risk in scorecard["risks"]:
        lines.append(
            f"- **{_cell(risk['severity'])} - {_cell(risk['title'])}:** "
            f"{_cell(risk['impact'])} Mitigation: {_cell(risk['mitigation'])}"
        )
    lines.extend(["", "## Journey Status", ""])
    for journey in scorecard["journeys"]:
        lines.append(
            f"- **{_cell(journey['status'])}: {_cell(journey['name'])}** - "
            f"{_cell(journey['evidence'])}"
        )
    lines.extend(
        [
            "",
            "## Validation",
            "",
        ]
    )
    for item in scorecard["validation"]:
        command = _cell(item["command"])
        status = _cell(item["status"])
        detail = _cell(item["detail"])
        lines.append(f"- `{command}` - **{status}**: {detail}")
    lines.extend(
        [
            "",
            "This report is generated from `scorecard.json`; edit the evidence source "
            "and regenerate it rather than changing the score in Markdown.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    scorecard = json.loads(args.scorecard.read_text(encoding="utf-8"))
    output = render_report(scorecard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
