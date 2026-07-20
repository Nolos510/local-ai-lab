"""Artifact-backed independent score review and human confirmation helpers."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

from . import model_roles
from .scoring import METRIC_FIELDS, calculate_total_score, validate_final_label

try:
    from datetime import UTC
except ImportError:  # Python 3.9 system runtime compatibility.
    from datetime import timezone as _timezone

    UTC = _timezone.utc  # noqa: UP017

MAX_MEAN_METRIC_DELTA = 10.0
MAX_SINGLE_METRIC_DELTA = 20.0
MAX_TOTAL_DELTA = 10.0
REVIEW_STATUSES = (
    "draft",
    "machine_reviewed",
    "disagreement",
    "rejected",
    "confirmed",
    "unscored",
)
HARD_SCORE_WARNING_CODES = {
    "all_scores_zero",
    "final_label_missing",
    "rationale_missing",
    "metric_rationales_incomplete",
}


def _utc_now():
    return datetime.now(UTC).isoformat()


def load_json_object(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _validated_scores(record):
    values = record.get("scores") if isinstance(record, dict) else None
    if not isinstance(values, dict):
        raise ValueError("Score record is missing its scores object.")
    validated = {}
    for field in METRIC_FIELDS:
        value = values.get(field)
        if value in (None, ""):
            raise ValueError(f"Score record is missing {field}.")
        number = float(value)
        if not math.isfinite(number) or number < 0 or number > 100:
            raise ValueError(f"Score {field} must be a finite number from 0 to 100.")
        validated[field] = number
    return validated


def compare_independent_scores(primary, reviewer):
    primary_scores = _validated_scores(primary)
    reviewer_scores = _validated_scores(reviewer)
    primary_label = validate_final_label(primary.get("final_label"))
    reviewer_label_value = reviewer.get("final_label")
    reviewer_label = (
        validate_final_label(reviewer_label_value)
        if reviewer_label_value not in (None, "")
        else None
    )
    metric_deltas = {
        field: round(abs(primary_scores[field] - reviewer_scores[field]), 2)
        for field in METRIC_FIELDS
    }
    mean_delta = round(sum(metric_deltas.values()) / len(metric_deltas), 2)
    max_delta = round(max(metric_deltas.values()), 2)
    total_delta = round(
        abs(calculate_total_score(primary_scores) - calculate_total_score(reviewer_scores)),
        2,
    )
    label_agreement = reviewer_label is not None and primary_label == reviewer_label
    flags = []
    primary_output_warnings = [
        str(value)
        for value in primary.get("suggestion_warnings", []) or []
        if str(value).strip()
    ]
    reviewer_output_warnings = [
        str(value)
        for value in reviewer.get("suggestion_warnings", []) or []
        if str(value).strip()
    ]
    if all(value == 0 for value in primary_scores.values()):
        flags.append("primary_all_scores_zero")
    if all(value == 0 for value in reviewer_scores.values()):
        flags.append("reviewer_all_scores_zero")
    if reviewer_label is None:
        flags.append("reviewer_label_missing")
    elif not label_agreement:
        flags.append("label")
    if mean_delta > MAX_MEAN_METRIC_DELTA or max_delta > MAX_SINGLE_METRIC_DELTA:
        flags.append("metric_delta")
    if total_delta > MAX_TOTAL_DELTA:
        flags.append("total_delta")
    if primary_output_warnings and "primary_output_incomplete" not in flags:
        flags.append("primary_output_incomplete")
    if reviewer_output_warnings and "reviewer_output_incomplete" not in flags:
        flags.append("reviewer_output_incomplete")
    return {
        "status": "machine_reviewed" if not flags else "disagreement",
        "primary_judge": str((primary.get("judge") or {}).get("model") or "unknown"),
        "reviewer_judge": str((reviewer.get("judge") or {}).get("model") or "unknown"),
        "primary_label": primary_label,
        "reviewer_label": reviewer_label,
        "label_agreement": label_agreement,
        "metric_deltas": metric_deltas,
        "mean_metric_delta": mean_delta,
        "max_metric_delta": max_delta,
        "total_delta": total_delta,
        "flags": flags,
        "primary_output_warnings": primary_output_warnings,
        "reviewer_output_warnings": reviewer_output_warnings,
        "thresholds": {
            "max_mean_metric_delta": MAX_MEAN_METRIC_DELTA,
            "max_single_metric_delta": MAX_SINGLE_METRIC_DELTA,
            "max_total_delta": MAX_TOTAL_DELTA,
        },
    }


def build_confirmed_score(primary, score_edits, final_label, reviewer="dashboard-human"):
    confirmed_scores = _validated_scores({"scores": score_edits})
    result = dict(primary)
    result["scores"] = confirmed_scores
    result["total_score"] = calculate_total_score(confirmed_scores)
    result["final_label"] = validate_final_label(final_label)
    result["score_status"] = "confirmed"
    result["human_confirmation"] = {
        "reviewer": str(reviewer),
        "confirmed_at": _utc_now(),
    }
    return result


def write_json_atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def write_review_record(artifact_dir, payload):
    record = dict(payload)
    status = str(record.get("status") or "")
    if status not in REVIEW_STATUSES:
        raise ValueError(f"Unknown review status: {status}")
    record["reviewed_at"] = _utc_now()
    return write_json_atomic(Path(artifact_dir) / "score-review.json", record)


def review_state(artifact_dir):
    artifact_dir = Path(artifact_dir)
    if (artifact_dir / "scores.json").is_file():
        return {"status": "confirmed"}
    review = load_json_object(artifact_dir / "score-review.json")
    status = review.get("status")
    if status in ("machine_reviewed", "disagreement"):
        try:
            current = evaluate_artifact_review(artifact_dir)
        except (TypeError, ValueError):
            current = {
                "status": "disagreement",
                "flags": ["review_artifact_invalid"],
            }
        current["benchmark_run_id"] = review.get("benchmark_run_id") or artifact_dir.name
        current["reviewed_at"] = review.get("reviewed_at")
        return current
    if status in REVIEW_STATUSES:
        return review
    if (artifact_dir / "draft-scores.json").is_file():
        return {"status": "draft"}
    return {"status": "unscored"}


def has_raw_evidence(artifact_dir):
    path = Path(artifact_dir) / "raw_responses.jsonl"
    if not path.is_file():
        return False
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if isinstance(record, dict) and str(record.get("raw_response") or "").strip():
                    return True
            return False
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False


def raw_evidence_quality(artifact_dir):
    path = Path(artifact_dir) / "raw_responses.jsonl"
    quality = {
        "record_count": 0,
        "nonempty_response_count": 0,
        "error_count": 0,
        "malformed_count": 0,
    }
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                quality["record_count"] += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    quality["malformed_count"] += 1
                    continue
                if not isinstance(record, dict):
                    quality["malformed_count"] += 1
                    continue
                if str(record.get("raw_response") or "").strip():
                    quality["nonempty_response_count"] += 1
                if str(record.get("error") or "").strip():
                    quality["error_count"] += 1
    except (OSError, UnicodeError):
        quality["malformed_count"] += 1
    return quality


def _score_record_failure_flags(record, prefix):
    if not record:
        return [f"{prefix}_score_invalid"]
    try:
        values = _validated_scores(record)
    except (TypeError, ValueError):
        return [f"{prefix}_score_invalid"]
    flags = []
    if all(value == 0 for value in values.values()):
        flags.append(f"{prefix}_all_scores_zero")
    warnings = {
        str(value).strip()
        for value in record.get("suggestion_warnings", []) or []
        if str(value).strip()
    }
    if warnings & HARD_SCORE_WARNING_CODES:
        flags.append(f"{prefix}_output_incomplete")
    return flags


def automatic_disposition(artifact_dir):
    """Return an objective quarantine decision, or None for human-reviewable evidence."""
    artifact_dir = Path(artifact_dir)
    if (artifact_dir / "scores.json").is_file():
        return None
    role = model_roles.artifact_model_role(artifact_dir)
    if not model_roles.model_supports_generation(role):
        return {
            "flags": ["non_generation_role"],
            "recommended_action": "route_to_role_evaluation",
            "reason": (
                f"{role.title()} evidence does not belong in generative scoring."
            ),
        }
    quality = raw_evidence_quality(artifact_dir)
    capture_flags = []
    if quality["record_count"] == 0 or quality["nonempty_response_count"] == 0:
        capture_flags.append("capture_evidence_missing")
    if quality["error_count"]:
        capture_flags.append("capture_errors_present")
    if quality["malformed_count"]:
        capture_flags.append("capture_evidence_malformed")
    if capture_flags:
        return {
            "flags": capture_flags,
            "recommended_action": "rerun_capture",
            "reason": "Capture evidence is missing, malformed, or contains runtime errors.",
            "capture_evidence": quality,
        }
    primary_path = artifact_dir / "draft-scores.json"
    if primary_path.is_file():
        primary_flags = _score_record_failure_flags(
            load_json_object(primary_path),
            "primary",
        )
        if primary_flags:
            return {
                "flags": primary_flags,
                "recommended_action": "rescore",
                "reason": "Primary judge output is invalid, incomplete, or all zero.",
                "capture_evidence": quality,
            }
    reviewer_path = artifact_dir / "review-scores.json"
    if reviewer_path.is_file():
        reviewer_flags = _score_record_failure_flags(
            load_json_object(reviewer_path),
            "reviewer",
        )
        if reviewer_flags:
            return {
                "flags": reviewer_flags,
                "recommended_action": "rerun_review",
                "reason": "Independent reviewer output is invalid, incomplete, or all zero.",
                "capture_evidence": quality,
            }
    return None


def evaluate_artifact_review(artifact_dir):
    artifact_dir = Path(artifact_dir)
    primary = load_json_object(artifact_dir / "draft-scores.json")
    reviewer = load_json_object(artifact_dir / "review-scores.json")
    result = compare_independent_scores(primary, reviewer)
    quality = raw_evidence_quality(artifact_dir)
    flags = list(result.get("flags") or [])
    if quality["record_count"] == 0 or quality["nonempty_response_count"] == 0:
        flags.append("capture_evidence_missing")
    if quality["error_count"]:
        flags.append("capture_errors_present")
    if quality["malformed_count"]:
        flags.append("capture_evidence_malformed")
    result["flags"] = list(dict.fromkeys(flags))
    result["capture_evidence"] = quality
    if result["flags"]:
        result["status"] = "disagreement"
    return result


def reviewable_artifact_ids(eval_results_dir):
    root = Path(eval_results_dir)
    if not root.is_dir():
        return []
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir()
        and has_raw_evidence(path)
        and model_roles.model_supports_generation(model_roles.artifact_model_role(path))
        and (path / "draft-scores.json").is_file()
        and not (path / "scores.json").is_file()
        and review_state(path)["status"] == "draft"
        and automatic_disposition(path) is None
    )


def confirmable_agreement_ids(eval_results_dir):
    """Return reviewed generative drafts whose two score records still agree."""
    root = Path(eval_results_dir)
    if not root.is_dir():
        return []
    confirmable = []
    for path in root.iterdir():
        if not path.is_dir():
            continue
        if not model_roles.model_supports_generation(
            model_roles.artifact_model_role(path)
        ):
            continue
        if not has_raw_evidence(path):
            continue
        if automatic_disposition(path) is not None:
            continue
        if (path / "scores.json").is_file():
            continue
        if review_state(path).get("status") != "machine_reviewed":
            continue
        try:
            comparison = evaluate_artifact_review(path)
        except (TypeError, ValueError):
            continue
        if comparison.get("status") == "machine_reviewed":
            confirmable.append(path.name)
    return sorted(confirmable)
