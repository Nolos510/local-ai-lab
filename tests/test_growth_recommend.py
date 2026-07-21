from __future__ import annotations

from local_ai_lab.growth.recommend import RecommendationContext, recommend_item


def item(**overrides):
    value = {
        "id": "skill-example",
        "status": "Now",
        "review_state": "metadata_reviewed",
        "availability": "available",
        "prereqs": [],
        "career_lenses": ["AIA"],
        "effort_tier": "1-3",
        "capability_gaps": ["testing"],
    }
    value.update(overrides)
    return value


def test_recommendation_is_deterministic_from_explicit_inputs() -> None:
    context = RecommendationContext(
        roles=frozenset({"AIA"}),
        max_effort_tier="1-3",
        capability_gaps=frozenset({"testing"}),
    )
    first = recommend_item(item(), context)
    second = recommend_item(item(), context)
    assert first == second
    assert first["recommendation"] == "Now"
    assert first["reasons"] == [
        "catalog priority is Now",
        "career lens matches a selected role",
        "effort fits the selected weekly capacity",
        "addresses a selected capability gap",
        "review state is metadata_reviewed",
    ]


def test_review_availability_and_prerequisites_block_before_ranking() -> None:
    context = RecommendationContext()
    assert recommend_item(item(review_state="blocked"), context)["recommendation"] == "Blocked"
    assert recommend_item(item(availability="pending"), context)["recommendation"] == "Blocked"
    result = recommend_item(item(prereqs=["skill-prereq"]), context)
    assert result == {
        "recommendation": "Blocked",
        "reasons": ["prerequisites are not evidenced"],
    }


def test_role_effort_gap_and_review_penalties_produce_later() -> None:
    context = RecommendationContext(
        roles=frozenset({"MLD"}),
        max_effort_tier="1-3",
        capability_gaps=frozenset({"retrieval"}),
    )
    result = recommend_item(
        item(
            status="Next",
            review_state="unreviewed",
            effort_tier="7-10",
            capability_gaps=["testing"],
        ),
        context,
    )
    assert result["recommendation"] == "Later"
    assert "career lens does not match selected roles" in result["reasons"]
    assert "effort exceeds the selected weekly capacity" in result["reasons"]
    assert "does not address a selected capability gap" in result["reasons"]


def test_evidence_is_distinct_and_promotes_current_work_to_now() -> None:
    context = RecommendationContext(evidenced_items=frozenset({"skill-example"}))
    result = recommend_item(item(status="Later", review_state="unreviewed"), context)
    assert result == {"recommendation": "Now", "reasons": ["proof artifact is evidenced"]}


def test_watch_catalog_status_maps_to_four_outcome_later_rule() -> None:
    result = recommend_item(item(status="Watch"), RecommendationContext())
    assert result["recommendation"] == "Later"
