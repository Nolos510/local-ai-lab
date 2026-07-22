"""CLI surface for the review-only SkillOpt pilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from local_ai_lab.skills_lab.skillopt import (
    PINNED_SKILLOPT_COMMIT,
    SkillOptEvidenceError,
    evaluate_qualification,
    host_handoff,
    inspect_checkout,
    load_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE = REPO_ROOT / "data" / "skills_lab" / "skillopt-pilot.json"


def _load_result(path: Path):
    evidence = load_evidence(path)
    return evaluate_qualification(evidence)


def _print_status(result, *, as_json: bool) -> None:
    payload = {
        "schema_version": "skillopt-qualification-v1",
        "tool": "SkillOpt",
        "pinned_commit": PINNED_SKILLOPT_COMMIT,
        "mode": "review_only",
        **result.to_dict(),
        "activation_permitted": False,
    }
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print("SkillOpt pilot")
    print(f"Status: {result.status}")
    print("Mode: review-only; no install, transcript harvest, or auto-adopt")
    print(
        f"Fresh trials: {result.trial_count}/{result.required_trials} | "
        f"accepted: {result.accepted_count} | qualified successes: "
        f"{result.successful_count} | rate: {result.success_rate:.0%}"
    )
    for reason in result.reasons:
        print(f"- {reason}")


def command_status(args: argparse.Namespace) -> int:
    try:
        result = _load_result(args.evidence)
    except SkillOptEvidenceError as exc:
        print(f"skills error: {exc}", file=sys.stderr)
        return 1
    _print_status(result, as_json=args.json)
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    try:
        result = _load_result(args.evidence)
    except SkillOptEvidenceError as exc:
        print(f"skills error: {exc}", file=sys.stderr)
        return 1
    checkout = inspect_checkout(args.checkout)
    payload = {
        "schema_version": "skillopt-preflight-v1",
        "checkout": checkout,
        "qualification": result.to_dict(),
        "execution_permitted": checkout["pinned"] and result.qualified,
        "activation_permitted": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["execution_permitted"] else 1


def command_handoff(args: argparse.Namespace) -> int:
    try:
        result = _load_result(args.evidence)
    except SkillOptEvidenceError as exc:
        print(f"skills error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(host_handoff(args.host, result), indent=2, sort_keys=True))
    return 0


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    skills = subparsers.add_parser(
        "skills",
        help="Inspect review-only skill optimizer qualification evidence.",
    )
    commands = skills.add_subparsers(dest="skills_command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--evidence",
        type=Path,
        default=DEFAULT_EVIDENCE,
        help=argparse.SUPPRESS,
    )

    status = commands.add_parser("status", parents=[common], help="Show the SkillOpt gate.")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    preflight = commands.add_parser(
        "preflight",
        parents=[common],
        help="Verify the pinned external checkout and promotion gate without running it.",
    )
    preflight.add_argument("--checkout", type=Path, required=True)
    preflight.set_defaults(func=command_preflight)

    handoff = commands.add_parser(
        "handoff",
        parents=[common],
        help="Show the non-mutating integration state for a supported host.",
    )
    handoff.add_argument("--host", choices=("local", "codex", "claude"), required=True)
    handoff.set_defaults(func=command_handoff)
