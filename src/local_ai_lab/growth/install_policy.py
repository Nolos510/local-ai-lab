"""Tracked, structured execution approvals for official host plugins only."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from local_ai_lab.growth.privacy import contains_sensitive_literal, safe_public_url

HOSTS = frozenset({"codex", "claude"})
SCOPES = frozenset({"user", "project", "local"})
COMPONENTS = frozenset(
    {
        "agents",
        "apps",
        "commands",
        "connectors",
        "hooks",
        "lsp_servers",
        "mcp_servers",
        "skills",
    }
)
EXEC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
EXEC_TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}$")
IMMUTABLE_REVISION_RE = re.compile(r"^[a-f0-9]{40,64}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_TEXT_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,240}$")
SAFE_ARTIFACT_PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]*$")
REVIEWED_READ_ONLY_MCP_WRITE_FACTS = frozenset(
    {
        "Research packet describes the MCP surface as read-only.",
        "Research packet describes the tool as read-only.",
    }
)
POLICY_FIELDS = {
    "target_id",
    "host",
    "plugin_id",
    "marketplace",
    "marketplace_source",
    "marketplace_revision",
    "reviewed_version",
    "scope",
    "components",
    "auth_policy",
    "data_scope",
    "high_risk",
    "data_scope_ack_required",
    "threat_review_artifact",
    "threat_review_sha256",
    "threat_review_version",
    "threat_review_scope",
    "reviewed_at",
    "pin_mode",
}


class InstallPolicyError(ValueError):
    """A tracked install policy is missing or cannot safely authorize execution."""

    def __init__(self, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True, slots=True)
class InstallPolicy:
    target_id: str
    host: str
    plugin_id: str
    marketplace: str
    marketplace_source: str
    marketplace_revision: str
    reviewed_version: str
    scope: str
    components: tuple[str, ...]
    auth_policy: str
    data_scope: str
    high_risk: bool
    data_scope_ack_required: bool
    threat_review_artifact: str | None
    threat_review_sha256: str | None
    threat_review_version: str | None
    threat_review_scope: str | None
    reviewed_at: str
    pin_mode: str

    @property
    def plugin_ref(self) -> str:
        return f"{self.plugin_id}@{self.marketplace}"

    def fingerprint_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["components"] = list(self.components)
        return payload


def _safe_artifact(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and all(SAFE_ARTIFACT_PART_RE.fullmatch(part) for part in path.parts)
    )


def _safe_tracked_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(SAFE_TEXT_RE.fullmatch(value))
        and not contains_sensitive_literal(value)
    )


def _artifact_digest(path: Path, *, repo_root: Path) -> str | None:
    try:
        root = repo_root.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file():
            return None
        return hashlib.sha256(resolved.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None


def validate_policy(raw: object, *, repo_root: Path) -> InstallPolicy:
    if not isinstance(raw, dict) or set(raw) != POLICY_FIELDS:
        raise InstallPolicyError("tracked Growth install policy is malformed")
    target_id = raw.get("target_id")
    if not isinstance(target_id, str) or not EXEC_TARGET_RE.fullmatch(target_id):
        raise InstallPolicyError("tracked Growth install target is invalid")
    host = raw.get("host")
    plugin_id = raw.get("plugin_id")
    marketplace = raw.get("marketplace")
    if host not in HOSTS:
        raise InstallPolicyError("tracked Growth install host is unsupported")
    if not isinstance(plugin_id, str) or not EXEC_ID_RE.fullmatch(plugin_id):
        raise InstallPolicyError("tracked Growth plugin id is invalid")
    if not isinstance(marketplace, str) or not EXEC_ID_RE.fullmatch(marketplace):
        raise InstallPolicyError("tracked Growth marketplace id is invalid")
    marketplace_source = safe_public_url(raw.get("marketplace_source"))
    if marketplace_source is None or marketplace_source != raw.get("marketplace_source"):
        raise InstallPolicyError("tracked Growth marketplace source is invalid")
    marketplace_revision = raw.get("marketplace_revision")
    if not isinstance(marketplace_revision, str) or not IMMUTABLE_REVISION_RE.fullmatch(
        marketplace_revision
    ):
        raise InstallPolicyError("tracked Growth marketplace revision is not immutable")
    reviewed_version = raw.get("reviewed_version")
    if not isinstance(reviewed_version, str) or not VERSION_RE.fullmatch(reviewed_version):
        raise InstallPolicyError("tracked Growth reviewed version is invalid")
    scope = raw.get("scope")
    if scope not in SCOPES or (host == "codex" and scope != "user"):
        raise InstallPolicyError("tracked Growth install scope is unsupported")
    components = raw.get("components")
    if (
        not isinstance(components, list)
        or not components
        or len(components) != len(set(components))
        or not set(components) <= COMPONENTS
    ):
        raise InstallPolicyError("tracked Growth plugin components are invalid")
    if not _safe_tracked_text(raw.get("auth_policy")) or not _safe_tracked_text(
        raw.get("data_scope")
    ):
        raise InstallPolicyError("tracked Growth authorization scope is invalid")
    if not isinstance(raw.get("high_risk"), bool) or not isinstance(
        raw.get("data_scope_ack_required"), bool
    ):
        raise InstallPolicyError("tracked Growth risk gate is invalid")
    if "connectors" in components and raw["high_risk"] is not True:
        raise InstallPolicyError("connector execution requires the high-risk review lane")
    if raw["high_risk"] is False and raw["data_scope_ack_required"] is not False:
        raise InstallPolicyError("standard-risk Growth policy has an invalid confirmation gate")
    reviewed_at = raw.get("reviewed_at")
    try:
        parsed_review_date = (
            date.fromisoformat(reviewed_at)
            if isinstance(reviewed_at, str) and DATE_RE.fullmatch(reviewed_at)
            else None
        )
    except ValueError:
        parsed_review_date = None
    if parsed_review_date is None or parsed_review_date > date.today():
        raise InstallPolicyError("tracked Growth policy review date is invalid")
    if raw.get("pin_mode") != "immutable_marketplace_revision":
        raise InstallPolicyError("tracked Growth policy does not enforce an immutable pin")

    artifact = raw.get("threat_review_artifact")
    artifact_sha = raw.get("threat_review_sha256")
    threat_version = raw.get("threat_review_version")
    threat_scope = raw.get("threat_review_scope")
    if raw["high_risk"]:
        if raw["data_scope_ack_required"] is not True:
            raise InstallPolicyError("high-risk Growth policy requires data-scope acknowledgement")
        if (
            not _safe_artifact(artifact)
            or not isinstance(artifact_sha, str)
            or not SHA256_RE.fullmatch(artifact_sha)
            or threat_version != reviewed_version
            or threat_scope != scope
        ):
            raise InstallPolicyError("high-risk Growth policy lacks an exact threat review")
        actual_digest = _artifact_digest(repo_root / artifact, repo_root=repo_root)
        if actual_digest != artifact_sha:
            raise InstallPolicyError("high-risk Growth threat review is missing or changed")
    elif any(value is not None for value in (artifact, artifact_sha, threat_version, threat_scope)):
        raise InstallPolicyError("standard-risk Growth policy has unexpected threat-review fields")

    return InstallPolicy(
        target_id=target_id,
        host=host,
        plugin_id=plugin_id,
        marketplace=marketplace,
        marketplace_source=marketplace_source,
        marketplace_revision=marketplace_revision,
        reviewed_version=reviewed_version,
        scope=scope,
        components=tuple(components),
        auth_policy=raw["auth_policy"],
        data_scope=raw["data_scope"],
        high_risk=raw["high_risk"],
        data_scope_ack_required=raw["data_scope_ack_required"],
        threat_review_artifact=artifact,
        threat_review_sha256=artifact_sha,
        threat_review_version=threat_version,
        threat_review_scope=threat_scope,
        reviewed_at=reviewed_at,
        pin_mode=raw["pin_mode"],
    )


def load_install_policies(path: Path, *, repo_root: Path) -> dict[str, InstallPolicy]:
    payload: object | None = None
    read_failed = False
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        read_failed = True
    if read_failed:
        raise InstallPolicyError("tracked Growth install policies could not be read")
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schema_version", "policies"}
        or payload.get("schema_version") != "growth-install-policy-v1"
        or not isinstance(payload.get("policies"), list)
    ):
        raise InstallPolicyError("tracked Growth install policy envelope is invalid")
    policies: dict[str, InstallPolicy] = {}
    for raw in payload["policies"]:
        policy = validate_policy(raw, repo_root=repo_root)
        if policy.target_id in policies:
            raise InstallPolicyError("tracked Growth install policies contain duplicate targets")
        policies[policy.target_id] = policy
    return policies


def policy_for_execution(
    *,
    policies: dict[str, InstallPolicy],
    catalog_items: list[dict[str, Any]],
    target_id: str,
    scope: str,
    operation: str,
) -> tuple[InstallPolicy, dict[str, Any]]:
    if not isinstance(target_id, str) or not EXEC_TARGET_RE.fullmatch(target_id):
        raise InstallPolicyError("Growth install target id is invalid")
    if scope not in SCOPES:
        raise InstallPolicyError("Growth install scope is invalid")
    if operation not in {"install", "remove"}:
        raise InstallPolicyError("Growth plugin operation is invalid")
    policy = policies.get(target_id)
    item = next((entry for entry in catalog_items if entry.get("id") == target_id), None)
    if policy is None or item is None or policy.scope != scope:
        raise InstallPolicyError("Growth target has no exact reviewed execution policy")
    if item.get("catalog_kind") != "extension" or item.get("official") is not True:
        raise InstallPolicyError("Growth target is not an approved official host plugin")
    item_type = item.get("type")
    risk_facts = item.get("risk_facts")
    reviewed_read_only_mcp = (
        item_type == "mcp"
        and isinstance(risk_facts, dict)
        and risk_facts.get("writes") in REVIEWED_READ_ONLY_MCP_WRITE_FACTS
    )
    requires_high_risk = item_type == "connector" or (
        item_type == "mcp" and not reviewed_read_only_mcp
    )
    if requires_high_risk and policy.high_risk is not True:
        raise InstallPolicyError(
            "connector or non-read-only MCP execution requires an exact high-risk policy"
        )
    if item_type == "connector" and (
        "connectors" not in policy.components
    ):
        raise InstallPolicyError(
            "connector execution requires an exact high-risk connector policy"
        )
    if item_type == "mcp" and "mcp_servers" not in policy.components:
        raise InstallPolicyError("MCP execution policy does not match the catalog type")
    if operation == "install" and (
        item.get("review_state") != "trial_approved" or item.get("status") == "Blocked"
    ):
        raise InstallPolicyError("Growth target remains review-only")
    return policy, item


def build_host_argv(policy: InstallPolicy, operation: str) -> list[str]:
    """Build one of exactly four official host CLI shapes from validated fields."""
    if not EXEC_ID_RE.fullmatch(policy.plugin_id) or not EXEC_ID_RE.fullmatch(policy.marketplace):
        raise InstallPolicyError("Growth plugin execution id is invalid")
    plugin_ref = policy.plugin_ref
    if operation == "install" and policy.host == "codex":
        return ["codex", "plugin", "add", plugin_ref]
    if operation == "remove" and policy.host == "codex":
        return ["codex", "plugin", "remove", plugin_ref]
    if operation == "install" and policy.host == "claude":
        return ["claude", "plugin", "install", plugin_ref, "--scope", policy.scope]
    if operation == "remove" and policy.host == "claude":
        return ["claude", "plugin", "uninstall", plugin_ref, "--scope", policy.scope]
    raise InstallPolicyError("Growth plugin execution host is unsupported")


__all__ = (
    "EXEC_ID_RE",
    "EXEC_TARGET_RE",
    "HOSTS",
    "IMMUTABLE_REVISION_RE",
    "InstallPolicy",
    "InstallPolicyError",
    "SCOPES",
    "VERSION_RE",
    "build_host_argv",
    "load_install_policies",
    "policy_for_execution",
    "validate_policy",
)
