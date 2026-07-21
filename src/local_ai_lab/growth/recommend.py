"""Deterministic, explainable Growth recommendation rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EFFORT_ORDER = {"1-3": 1, "4-6": 2, "7-10": 3}
BASE_PRIORITY = {"Now": 0, "Next": 1, "Later": 2, "Watch": 2}


@dataclass(frozen=True)
class RecommendationContext:
    """Explicit personal inputs; absence of roles or gaps is neutral, never inferred."""

    roles: frozenset[str] = field(default_factory=frozenset)
    max_effort_tier: str = "7-10"
    satisfied_prereqs: frozenset[str] = field(default_factory=frozenset)
    capability_gaps: frozenset[str] = field(default_factory=frozenset)
    evidenced_items: frozenset[str] = field(default_factory=frozenset)


def recommend_item(
    item: dict[str, Any],
    context: RecommendationContext,
) -> dict[str, object]:
    """Return Now/Next/Later/Blocked plus the ordered facts that caused it."""
    reasons: list[str] = []
    item_id = str(item.get("id", ""))
    review_state = str(item.get("review_state", "unreviewed"))
    availability = str(item.get("availability", "unknown"))
    status = str(item.get("status", "Later"))
    prereqs = frozenset(str(value) for value in item.get("prereqs", ()))

    if status == "Blocked":
        return {"recommendation": "Blocked", "reasons": ["catalog status is Blocked"]}
    if review_state in {"blocked", "retired"}:
        return {"recommendation": "Blocked", "reasons": [f"review state is {review_state}"]}
    if availability in {"pending", "unavailable"}:
        return {"recommendation": "Blocked", "reasons": [f"availability is {availability}"]}
    unmet = sorted(prereqs - context.satisfied_prereqs)
    if unmet:
        return {"recommendation": "Blocked", "reasons": ["prerequisites are not evidenced"]}

    if item_id in context.evidenced_items:
        return {"recommendation": "Now", "reasons": ["proof artifact is evidenced"]}

    priority = BASE_PRIORITY.get(status, 2)
    reasons.append(f"catalog priority is {status}")
    lenses = set(str(value) for value in item.get("career_lenses", ()))
    if context.roles and not lenses.intersection(context.roles):
        priority += 1
        reasons.append("career lens does not match selected roles")
    elif context.roles:
        reasons.append("career lens matches a selected role")

    effort = str(item.get("effort_tier", "7-10"))
    if EFFORT_ORDER.get(effort, 3) > EFFORT_ORDER.get(context.max_effort_tier, 3):
        priority += 1
        reasons.append("effort exceeds the selected weekly capacity")
    else:
        reasons.append("effort fits the selected weekly capacity")

    item_gaps = set(str(value) for value in item.get("capability_gaps", ()))
    if context.capability_gaps:
        if item_gaps.intersection(context.capability_gaps):
            reasons.append("addresses a selected capability gap")
        else:
            priority += 1
            reasons.append("does not address a selected capability gap")

    if review_state == "unreviewed":
        priority += 1
        reasons.append("metadata remains unreviewed")
    else:
        reasons.append(f"review state is {review_state}")

    if priority <= 0:
        recommendation = "Now"
    elif priority == 1:
        recommendation = "Next"
    else:
        recommendation = "Later"
    return {"recommendation": recommendation, "reasons": reasons}
