"""Read-only loader and narrow validator for tracked Growth catalogs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CATALOG_FILES = ("skills.json", "extensions.json", "learning.json")
CATALOG_KINDS = {"skill", "extension", "learning"}
CAREER_LENSES = {"AIA", "AUT", "MLD"}
EFFORT_TIERS = {"1-3", "4-6", "7-10"}
STATUSES = {"Now", "Next", "Later", "Watch", "Blocked"}
REVIEW_STATES = {
    "unreviewed",
    "metadata_reviewed",
    "trial_approved",
    "blocked",
    "retired",
}
AVAILABILITY_STATES = {
    "available",
    "pending",
    "link_requires_verification",
    "unknown",
    "unavailable",
}
RISK_FIELDS = (
    "code_exec",
    "fs",
    "network",
    "creds",
    "private_data",
    "writes",
    "hooks",
    "background",
    "provenance",
    "license",
    "version_pin",
    "rollback",
)
REQUIRED_FIELDS = {
    "id",
    "catalog_kind",
    "type",
    "name",
    "official",
    "provenance",
    "source_url",
    "availability",
    "review_date",
    "career_lenses",
    "practical_value",
    "marketability",
    "effort_tier",
    "cost",
    "prereqs",
    "capability_gaps",
    "risk_facts",
    "status",
    "review_state",
    "proof_artifact",
    "proof_project",
    "next_action",
    "inventory_aliases",
}
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:@-]{0,127}$")
SAFE_PATH_PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CatalogError(ValueError):
    """A catalog cannot be safely loaded."""


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and all(
        SAFE_PATH_PART_RE.fullmatch(part) for part in path.parts
    )


def _safe_public_url(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(entry, str) for entry in value)


def validate_item(item: object, *, expected_kind: str | None = None) -> dict[str, Any]:
    """Validate the security- and honesty-critical subset without a JSON Schema dependency."""
    if not isinstance(item, dict) or REQUIRED_FIELDS - item.keys():
        raise CatalogError("catalog item is missing required fields")
    item_id = item.get("id")
    if not isinstance(item_id, str) or not SAFE_ID_RE.fullmatch(item_id):
        raise CatalogError("catalog item has an invalid id")
    kind = item.get("catalog_kind")
    if kind not in CATALOG_KINDS or (expected_kind and kind != expected_kind):
        raise CatalogError(f"catalog item {item_id} has an invalid catalog kind")
    if not isinstance(item.get("type"), str) or not item["type"]:
        raise CatalogError(f"catalog item {item_id} has an invalid type")
    if not isinstance(item.get("name"), str) or not item["name"]:
        raise CatalogError(f"catalog item {item_id} has an invalid name")
    if item.get("official") not in (True, False, None):
        raise CatalogError(f"catalog item {item_id} has invalid official provenance")
    if not isinstance(item.get("provenance"), str) or not item["provenance"]:
        raise CatalogError(f"catalog item {item_id} has invalid provenance")
    if not _safe_public_url(item.get("source_url")):
        raise CatalogError(f"catalog item {item_id} has an unsafe source URL")
    if item.get("availability") not in AVAILABILITY_STATES:
        raise CatalogError(f"catalog item {item_id} has invalid availability")
    if not isinstance(item.get("review_date"), str) or not DATE_RE.fullmatch(
        item["review_date"]
    ):
        raise CatalogError(f"catalog item {item_id} has an invalid review date")
    lenses = item.get("career_lenses")
    if not _string_list(lenses) or not lenses or not set(lenses) <= CAREER_LENSES:
        raise CatalogError(f"catalog item {item_id} has invalid career lenses")
    for field in ("practical_value", "marketability", "proof_project", "next_action"):
        if not isinstance(item.get(field), str) or not item[field]:
            raise CatalogError(f"catalog item {item_id} has an invalid {field}")
    if item.get("cost") is not None and not isinstance(item["cost"], str):
        raise CatalogError(f"catalog item {item_id} has an invalid cost")
    if item.get("effort_tier") not in EFFORT_TIERS:
        raise CatalogError(f"catalog item {item_id} has an invalid effort tier")
    for field in ("prereqs", "capability_gaps", "inventory_aliases"):
        if not _string_list(item.get(field)):
            raise CatalogError(f"catalog item {item_id} has an invalid {field}")
    if not all(SAFE_ID_RE.fullmatch(alias) for alias in item["inventory_aliases"]):
        raise CatalogError(f"catalog item {item_id} has an unsafe inventory alias")
    risks = item.get("risk_facts")
    if not isinstance(risks, dict) or set(risks) != set(RISK_FIELDS):
        raise CatalogError(f"catalog item {item_id} has incomplete risk facts")
    if not all(isinstance(risks[field], str) and risks[field] for field in RISK_FIELDS):
        raise CatalogError(f"catalog item {item_id} has an invalid risk fact")
    if item.get("status") not in STATUSES:
        raise CatalogError(f"catalog item {item_id} has an invalid status")
    if item.get("review_state") not in REVIEW_STATES:
        raise CatalogError(f"catalog item {item_id} has an invalid review state")
    if not _safe_relative_path(item.get("proof_artifact")):
        raise CatalogError(f"catalog item {item_id} has an unsafe proof artifact")
    return item


def load_catalog(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError(f"could not load tracked catalog {path.name}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "growth-catalog-v1":
        raise CatalogError(f"tracked catalog {path.name} has an invalid schema version")
    expected_kind = path.stem.removesuffix("s")
    if expected_kind == "learnin":
        expected_kind = "learning"
    if payload.get("catalog_kind") != expected_kind or not isinstance(payload.get("items"), list):
        raise CatalogError(f"tracked catalog {path.name} has an invalid envelope")
    items = [validate_item(item, expected_kind=expected_kind) for item in payload["items"]]
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise CatalogError(f"tracked catalog {path.name} contains duplicate ids")
    return items


def load_catalogs(catalog_dir: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for filename in CATALOG_FILES:
        items.extend(load_catalog(catalog_dir / filename))
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise CatalogError("tracked growth catalogs contain duplicate ids")
    return items
