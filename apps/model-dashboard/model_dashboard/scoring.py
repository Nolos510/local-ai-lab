"""Scoring helpers for local model evaluations."""

METRIC_FIELDS = (
    "instruction_following",
    "truthfulness_uncertainty",
    "reasoning",
    "coding_debugging",
    "agent_planning",
    "local_ai_lab_usefulness",
    "research_synthesis",
    "business_seo_strategy",
    "long_context",
    "creativity",
    "speed_practicality",
)

FINAL_LABELS = (
    "DAILY_DRIVER",
    "CODING_SPECIALIST",
    "RESEARCH_SPECIALIST",
    "AGENT_PLANNER",
    "CREATIVE_WRITER",
    "LOCAL_AI_ASSISTANT",
    "SEO_BUSINESS_HELPER",
    "MULTIMODAL_SPECIALIST",
    "SANDBOX_ONLY",
    "WATCHLIST",
    "SKIP",
)

SCORE_STATUSES = ("confirmed", "draft")

SPECIALIST_LABELS = {
    "coding_debugging": "CODING_SPECIALIST",
    "research_synthesis": "RESEARCH_SPECIALIST",
    "agent_planning": "AGENT_PLANNER",
    "creativity": "CREATIVE_WRITER",
    "local_ai_lab_usefulness": "LOCAL_AI_ASSISTANT",
    "business_seo_strategy": "SEO_BUSINESS_HELPER",
}


def _score_value(value):
    if value in (None, ""):
        return 0.0
    score = float(value)
    if score < 0 or score > 100:
        raise ValueError("Scores must be between 0 and 100.")
    return score


def calculate_total_score(values):
    """Return the mean of the configured metric fields on a 0-100 scale."""
    if hasattr(values, "get"):
        scores = [_score_value(values.get(field)) for field in METRIC_FIELDS]
    else:
        scores = [_score_value(value) for value in values]
        if len(scores) != len(METRIC_FIELDS):
            raise ValueError("Expected exactly 11 metric values.")
    return round(sum(scores) / len(scores), 2)


def validate_final_label(label):
    if label not in FINAL_LABELS:
        raise ValueError(
            "Unknown final_label {!r}. Expected one of: {}".format(label, ", ".join(FINAL_LABELS))
        )
    return label


def validate_score_status(status):
    if status in (None, ""):
        return "confirmed"
    if status not in SCORE_STATUSES:
        raise ValueError(
            "Unknown score_status {!r}. Expected one of: {}".format(
                status, ", ".join(SCORE_STATUSES)
            )
        )
    return status


def suggest_final_label(values):
    """Suggest a deterministic final label from metric strengths."""
    total = calculate_total_score(values)
    if total < 45:
        return "SKIP"
    if total < 58:
        return "SANDBOX_ONLY"

    local_score = _score_value(values.get("local_ai_lab_usefulness"))
    speed_score = _score_value(values.get("speed_practicality"))
    if total >= 85 and local_score >= 80 and speed_score >= 70:
        return "DAILY_DRIVER"

    best_metric = max(SPECIALIST_LABELS, key=lambda field: _score_value(values.get(field)))
    if _score_value(values.get(best_metric)) >= 75:
        return SPECIALIST_LABELS[best_metric]
    return "WATCHLIST"


def normalize_score_record(row):
    """Fill derived score fields and validate labels for CSV/database import."""
    normalized = dict(row)
    for field in METRIC_FIELDS:
        normalized[field] = _score_value(normalized.get(field))

    total = normalized.get("total_score")
    normalized["total_score"] = (
        calculate_total_score(normalized) if total in (None, "") else _score_value(total)
    )

    label = normalized.get("final_label")
    normalized["final_label"] = (
        suggest_final_label(normalized) if label in (None, "") else validate_final_label(label)
    )
    normalized["score_status"] = validate_score_status(normalized.get("score_status"))
    return normalized
