from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_ai_lab.growth.catalog import (
    CATALOG_FILES,
    REQUIRED_FIELDS,
    RISK_FIELDS,
    CatalogError,
    load_catalog,
    load_catalogs,
)
from local_ai_lab.growth.install_policy import load_install_policies

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "data" / "growth_registry"


def test_json_schemas_and_research_packet_catalogs_parse() -> None:
    schemas = sorted((CATALOG_DIR / "schemas").glob("*.schema.json"))
    assert {path.name for path in schemas} == {
        "growth-catalog-v1.schema.json",
        "growth-install-policy-v1.schema.json",
        "growth-state-v1.schema.json",
    }
    for path in schemas:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    items = load_catalogs(CATALOG_DIR)
    assert len(items) == 43
    assert sum(item["catalog_kind"] == "skill" for item in items) == 7
    assert sum(item["catalog_kind"] == "extension" for item in items) == 23
    assert sum(item["catalog_kind"] == "learning" for item in items) == 13
    assert load_install_policies(
        CATALOG_DIR / "install-policies.json",
        repo_root=REPO_ROOT,
    ) == {}
    assert not any(CATALOG_DIR.glob("*.csv"))


def test_every_catalog_item_has_full_risk_and_proof_fields() -> None:
    items = load_catalogs(CATALOG_DIR)
    for item in items:
        assert item.keys() == REQUIRED_FIELDS
        assert set(item["risk_facts"]) == set(RISK_FIELDS)
        proof = Path(item["proof_artifact"])
        assert not proof.is_absolute()
        assert ".." not in proof.parts

    by_id = {item["id"]: item for item in items}
    assert by_id["skill-code-review"]["status"] == "Now"
    assert by_id["skill-local-llm-eval"]["review_state"] == "metadata_reviewed"
    assert by_id["ext-context7"]["risk_facts"]["network"] == (
        "Fetches documentation over the network."
    )
    assert by_id["ext-email"]["status"] == "Blocked"
    assert by_id["ln-lf-mcpa"]["availability"] == "pending"


def test_only_existing_repo_proofs_can_be_evidenced() -> None:
    items = load_catalogs(CATALOG_DIR)
    existing = {
        item["id"]
        for item in items
        if (REPO_ROOT / item["proof_artifact"]).is_file()
    }
    assert existing == {"skill-code-review", "skill-local-llm-eval"}


def test_malformed_catalog_fails_without_echoing_untrusted_content(tmp_path: Path) -> None:
    path = tmp_path / "skills.json"
    path.write_text('{"secret": "sk-private-value"}', encoding="utf-8")
    with pytest.raises(CatalogError) as exc:
        load_catalog(path)
    assert "sk-private-value" not in str(exc.value)
    assert str(tmp_path) not in str(exc.value)


def test_catalog_file_names_are_fixed() -> None:
    assert CATALOG_FILES == ("skills.json", "extensions.json", "learning.json")
