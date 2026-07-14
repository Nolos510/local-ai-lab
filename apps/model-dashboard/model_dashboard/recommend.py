"""Pure task recommendations from confirmed local benchmark scores."""

from __future__ import annotations

import math
from dataclasses import dataclass

TASK_GROUPS = (
    ("Coding", ("instruction_following", "coding_debugging")),
    ("Reasoning & agents", ("reasoning", "agent_planning")),
    ("Research & writing", ("research_synthesis", "creativity")),
    ("Long context", ("long_context",)),
    ("Fast & practical", ("speed_practicality",)),
)


@dataclass(frozen=True)
class ModelLeader:
    """A model tied for the best confirmed score in a task group."""

    model_id: object
    model_name: str


@dataclass(frozen=True)
class TaskLeader:
    """The best score and all models tied at that score for one task group."""

    task: str
    score: float
    leaders: tuple[ModelLeader, ...]


@dataclass(frozen=True)
class RecommendationSummary:
    """Task leaders plus the number of distinct models with usable confirmed scores."""

    tasks: tuple[TaskLeader, ...]
    scored_model_count: int


def _row_value(row, field):
    if hasattr(row, "get"):
        return row.get(field)
    try:
        return row[field]
    except (IndexError, KeyError):
        return None


def _score(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _task_score(row, fields):
    values = [_score(_row_value(row, field)) for field in fields]
    if any(value is None for value in values):
        return None
    return round(sum(values) / len(values), 2)


def _model_key(model_id, model_name):
    if model_id not in (None, ""):
        return ("id", str(model_id))
    return ("name", model_name.casefold())


def task_recommendations(rows) -> RecommendationSummary:
    """Return deterministic task leaders using confirmed score rows only.

    Each task score is the mean of its configured benchmark dimensions. When a
    model has more than one confirmed row, its highest score for that task is
    retained. Exact co-leaders are preserved instead of breaking ties silently.
    """
    best_by_task = {task: {} for task, _fields in TASK_GROUPS}
    scored_models = set()

    for row in rows:
        if _row_value(row, "score_status") != "confirmed":
            continue
        model_id = _row_value(row, "model_id")
        model_name = str(_row_value(row, "model_name") or "Unnamed model")
        model_key = _model_key(model_id, model_name)
        has_task_score = False

        for task, fields in TASK_GROUPS:
            score = _task_score(row, fields)
            if score is None:
                continue
            has_task_score = True
            prior = best_by_task[task].get(model_key)
            if prior is None or score > prior[0]:
                best_by_task[task][model_key] = (
                    score,
                    ModelLeader(model_id=model_id, model_name=model_name),
                )

        if has_task_score:
            scored_models.add(model_key)

    task_leaders = []
    for task, _fields in TASK_GROUPS:
        model_scores = best_by_task[task].values()
        if not model_scores:
            continue
        best_score = max(score for score, _leader in model_scores)
        leaders = tuple(
            sorted(
                (leader for score, leader in model_scores if score == best_score),
                key=lambda leader: (leader.model_name.casefold(), str(leader.model_id)),
            )
        )
        task_leaders.append(TaskLeader(task=task, score=best_score, leaders=leaders))

    return RecommendationSummary(
        tasks=tuple(task_leaders),
        scored_model_count=len(scored_models),
    )


__all__ = (
    "TASK_GROUPS",
    "ModelLeader",
    "TaskLeader",
    "RecommendationSummary",
    "task_recommendations",
)
