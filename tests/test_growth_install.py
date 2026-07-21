from __future__ import annotations

import hashlib
import json
import multiprocessing
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_ai_lab.growth.install import (
    GrowthInstallService,
    InstallError,
    OperationLease,
    PreflightStore,
)
from local_ai_lab.growth.install_policy import build_host_argv, load_install_policies

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = REPO_ROOT / "data" / "growth_registry"
REVISION = "a" * 40


def _hold_operation_lease(repo_text: str, ready, release) -> None:
    repo = Path(repo_text)
    with OperationLease(
        repo / ".local-ai-lab" / "growth-operation-v1.lock",
        repo_root=repo,
    ):
        ready.set()
        if not release.wait(10):
            raise RuntimeError("test release timed out")


def _exception_graph_text(error: BaseException) -> str:
    pending = [error]
    visited: set[int] = set()
    values: list[str] = []
    while pending:
        current = pending.pop()
        if id(current) in visited:
            continue
        visited.add(id(current))
        values.append(f"{type(current).__name__}: {current}")
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return "\n".join(values)


def subprocess_result(payload: object = None, *, returncode: int = 0, raw: str | None = None):
    stdout = raw if raw is not None else json.dumps(payload if payload is not None else {})
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="raw sk-never-store")


def live_payload(
    *,
    installed: bool,
    version: str = "1.2.3",
    source: str | None = None,
    scope: str = "user",
):
    return {
        "plugins": [
            {
                "plugin_id": "safe-plugin",
                "marketplace": "official-marketplace",
                "marketplace_source": source or "https://github.com/openai/official-plugins",
                "marketplace_revision": REVISION,
                "version": version,
                "scope": scope,
                "installed": installed,
                "enabled": installed,
            }
        ]
    }


def prepare_repo(tmp_path: Path, *, high_risk: bool = False, valid_threat_review: bool = True):
    repo = tmp_path / "repo"
    catalog_dir = repo / "data" / "growth_registry"
    catalog_dir.mkdir(parents=True)
    for name in ("skills.json", "extensions.json", "learning.json"):
        payload = json.loads((SOURCE_CATALOG / name).read_text(encoding="utf-8"))
        if name == "extensions.json":
            item = next(entry for entry in payload["items"] if entry["id"] == "ext-semgrep-mcp")
            item["review_state"] = "trial_approved"
            item["status"] = "Next"
        (catalog_dir / name).write_text(json.dumps(payload), encoding="utf-8")

    artifact = repo / "reports" / "growth" / "safe-plugin-threat-review.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("exact 1.2.3 user-scope threat review\n", encoding="utf-8")
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    policy = {
        "target_id": "ext-semgrep-mcp",
        "host": "codex",
        "plugin_id": "safe-plugin",
        "marketplace": "official-marketplace",
        "marketplace_source": "https://github.com/openai/official-plugins",
        "marketplace_revision": REVISION,
        "reviewed_version": "1.2.3",
        "scope": "user",
        "components": ["skills", "mcp_servers"],
        "auth_policy": "No credentials are granted by installation.",
        "data_scope": "Only the selected non-private repository fixture.",
        "high_risk": high_risk,
        "data_scope_ack_required": high_risk,
        "threat_review_artifact": (
            "reports/growth/safe-plugin-threat-review.md" if high_risk else None
        ),
        "threat_review_sha256": artifact_sha if high_risk and valid_threat_review else None,
        "threat_review_version": "1.2.3" if high_risk else None,
        "threat_review_scope": "user" if high_risk else None,
        "reviewed_at": "2026-07-21",
        "pin_mode": "immutable_marketplace_revision",
    }
    policy_path = catalog_dir / "install-policies.json"
    policy_path.write_text(
        json.dumps({"schema_version": "growth-install-policy-v1", "policies": [policy]}),
        encoding="utf-8",
    )
    return repo, catalog_dir, policy_path


def service_for(repo: Path, catalog_dir: Path, policy_path: Path, runner, **kwargs):
    private = repo / ".local-ai-lab"
    kwargs.setdefault("nonce_factory", lambda: "N" * 32)
    return GrowthInstallService(
        repo_root=repo,
        catalog_dir=catalog_dir,
        policy_path=policy_path,
        preflight_path=private / "growth-preflights-v1.json",
        audit_path=private / "growth-audit-v1.json",
        operation_lock_path=private / "growth-operation-v1.lock",
        runner=runner,
        which=lambda _host: "/Users/alice/bin/codex",
        environ={"PATH": "/safe/bin", "API_TOKEN": "sk-never-pass"},
        home_dir=Path("/Users/alice"),
        **kwargs,
    )


def test_target_charset_is_rejected_before_lookup_or_subprocess(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    calls = []
    service = service_for(
        repo,
        catalog_dir,
        policy_path,
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    for hostile in (
        "--help",
        "safe;curl",
        "safe plugin",
        "safe\nplugin",
        "$(id)",
        "`id`",
        "safe@other",
        "safe:other",
        "safe/path",
    ):
        with pytest.raises(InstallError) as exc:
            service.preflight(target=hostile, scope="user", operation="install")
        assert exc.value.exit_code == 2
    assert calls == []


def test_dry_run_builds_reviewed_plan_without_cli_lookup_nonce_or_state(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)

    def forbidden_runner(*_args, **_kwargs):
        raise AssertionError("dry-run must not execute a host CLI")

    service = service_for(repo, catalog_dir, policy_path, forbidden_runner)
    result = service.preflight(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["nonce"] is None
    assert result["expires_at"] is None
    assert result["plan"]["live_version"] is None
    assert not (repo / ".local-ai-lab").exists()


def test_tampered_preflight_argv_is_rejected_before_confirmation_lookup(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess_result(live_payload(installed=False))

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    preflight_path = repo / ".local-ai-lab" / "growth-preflights-v1.json"
    state = json.loads(preflight_path.read_text(encoding="utf-8"))
    state["entries"][0]["plan"]["argv"] = ["sh", "-c", "id"]
    preflight_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 2
    assert calls == [["codex", "plugin", "list", "--json"]]


def test_all_four_argv_shapes_are_lists_from_validated_policy(tmp_path: Path) -> None:
    repo, _catalog_dir, policy_path = prepare_repo(tmp_path)
    codex = load_install_policies(policy_path, repo_root=repo)["ext-semgrep-mcp"]
    assert build_host_argv(codex, "install") == [
        "codex",
        "plugin",
        "add",
        "safe-plugin@official-marketplace",
    ]
    assert build_host_argv(codex, "remove") == [
        "codex",
        "plugin",
        "remove",
        "safe-plugin@official-marketplace",
    ]
    claude = codex.__class__(
        **{
            **codex.fingerprint_payload(),
            "host": "claude",
            "scope": "project",
            "components": codex.components,
        }
    )
    assert build_host_argv(claude, "install") == [
        "claude",
        "plugin",
        "install",
        "safe-plugin@official-marketplace",
        "--scope",
        "project",
    ]
    assert build_host_argv(claude, "remove") == [
        "claude",
        "plugin",
        "uninstall",
        "safe-plugin@official-marketplace",
        "--scope",
        "project",
    ]


@pytest.mark.parametrize("field", ["plugin_id", "marketplace"])
def test_host_argv_ids_reject_flag_injection_before_subprocess(
    tmp_path: Path,
    field: str,
) -> None:
    repo, _catalog_dir, policy_path = prepare_repo(tmp_path)
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    payload["policies"][0][field] = "--help"
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Exception) as exc:
        load_install_policies(policy_path, repo_root=repo)
    assert "invalid" in str(exc.value)


def test_connector_policy_cannot_bypass_high_risk_threat_review(tmp_path: Path) -> None:
    repo, _catalog_dir, policy_path = prepare_repo(tmp_path)
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    payload["policies"][0]["components"] = ["connectors"]
    policy_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Exception) as exc:
        load_install_policies(policy_path, repo_root=repo)
    assert "high-risk review lane" in str(exc.value)


def test_install_uses_list_argv_verifies_exact_version_and_writes_sanitized_audit(
    tmp_path: Path,
) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    installed = False
    calls = []

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append((argv, kwargs))
        assert isinstance(argv, list)
        assert kwargs["shell"] is False
        assert kwargs["env"] == {
            "HOME": "/Users/alice",
            "PATH": "/safe/bin",
            "NO_COLOR": "1",
        }
        assert kwargs["cwd"] == str(repo)
        if argv[1:3] == ["plugin", "list"]:
            return subprocess_result(live_payload(installed=installed))
        if argv[1:3] == ["plugin", "add"]:
            installed = True
            return subprocess_result(raw="installed /Users/alice sk-raw-host-output")
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
    )
    assert preflight["plan"]["argv"] == [
        "codex",
        "plugin",
        "add",
        "safe-plugin@official-marketplace",
    ]
    result = service.execute(
        nonce=preflight["nonce"],
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        yes=True,
        allowed=True,
    )
    assert result["outcome"] == "success"
    assert any(argv[1:3] == ["plugin", "add"] for argv, _kwargs in calls)
    audit_path = repo / ".local-ai-lab" / "growth-audit-v1.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert [event["outcome"] for event in audit["events"]] == ["started", "success"]
    assert all(isinstance(event["argv"], list) for event in audit["events"])
    serialized = json.dumps(audit)
    assert "/Users/alice" not in serialized
    assert "sk-raw-host-output" not in serialized
    assert "sk-never" not in serialized
    assert audit_path.stat().st_mode & 0o777 == 0o600


def test_claude_project_scope_lookup_and_mutation_are_bound_to_reviewed_repo(
    tmp_path: Path,
) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    policy_payload = json.loads(policy_path.read_text(encoding="utf-8"))
    policy_payload["policies"][0]["host"] = "claude"
    policy_payload["policies"][0]["scope"] = "project"
    policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")
    installed = False
    calls = []

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append((argv, kwargs))
        assert kwargs["cwd"] == str(repo)
        if argv[1:3] == ["plugin", "list"]:
            return subprocess_result(live_payload(installed=installed, scope="project"))
        if argv[1:3] == ["plugin", "install"]:
            installed = True
            return subprocess_result()
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(
        target="ext-semgrep-mcp",
        scope="project",
        operation="install",
    )
    service.execute(
        nonce=preflight["nonce"],
        target="ext-semgrep-mcp",
        scope="project",
        operation="install",
        yes=True,
        allowed=True,
    )
    assert ["claude", "plugin", "list", "--available", "--json"] in [
        argv for argv, _kwargs in calls
    ]
    assert [
        "claude",
        "plugin",
        "install",
        "safe-plugin@official-marketplace",
        "--scope",
        "project",
    ] in [argv for argv, _kwargs in calls]


def test_verify_failure_triggers_allowlisted_rollback_and_failure_audit(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    calls = []
    installed = False

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            version = "9.9.9" if installed else "1.2.3"
            return subprocess_result(live_payload(installed=installed, version=version))
        if argv[1:3] == ["plugin", "add"]:
            installed = True
        elif argv[1:3] == ["plugin", "remove"]:
            installed = False
        return subprocess_result(raw="raw /Users/alice sk-private")

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 1
    assert ["codex", "plugin", "remove", "safe-plugin@official-marketplace"] in calls
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    outcomes = [event["outcome"] for event in audit["events"]]
    assert "verify_failed" in outcomes
    assert "rollback_started" in outcomes
    assert "rollback_success" in outcomes
    assert "verify_failed_rolled_back" in outcomes


def test_live_version_drift_consumes_nonce_and_reblocks_before_install(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    list_calls = 0
    calls = []

    def runner(argv, **kwargs):
        nonlocal list_calls
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            list_calls += 1
            version = "1.2.3" if list_calls == 1 else "2.0.0"
            return subprocess_result(live_payload(installed=False, version=version))
        raise AssertionError("install must not run after drift")

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 2
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)
    with pytest.raises(InstallError):
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    assert audit["events"][-1]["outcome"] == "blocked_version_drift"


def test_live_marketplace_source_drift_reblocks_before_install(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    list_calls = 0
    calls = []

    def runner(argv, **kwargs):
        nonlocal list_calls
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            list_calls += 1
            source = (
                "https://github.com/openai/official-plugins"
                if list_calls == 1
                else "https://github.com/example/drifted-marketplace"
            )
            return subprocess_result(live_payload(installed=False, source=source))
        raise AssertionError("install must not run after source drift")

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 2
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    assert audit["events"][-1]["outcome"] == "blocked_version_drift"


@pytest.mark.parametrize("suffix", ["?ref=other", "#other"])
def test_marketplace_source_query_or_fragment_cannot_normalize_to_reviewed_source(
    tmp_path: Path,
    suffix: str,
) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    list_calls = 0
    calls = []

    def runner(argv, **kwargs):
        nonlocal list_calls
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            list_calls += 1
            source = "https://github.com/openai/official-plugins"
            if list_calls > 1:
                source += suffix
            return subprocess_result(live_payload(installed=False, source=source))
        raise AssertionError("install must not run after exact-source mismatch")

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 1
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)


def test_live_scope_drift_reblocks_before_install(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    list_calls = 0
    calls = []

    def runner(argv, **kwargs):
        nonlocal list_calls
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            list_calls += 1
            scope = "user" if list_calls == 1 else "project"
            return subprocess_result(live_payload(installed=False, scope=scope))
        raise AssertionError("install must not run after scope drift")

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 1
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    assert audit["events"][-1]["outcome"] == "blocked_policy_drift"


def test_nonce_expiry_blocks_without_mutation(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    now = [1000.0]
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess_result(live_payload(installed=False))

    service = service_for(
        repo,
        catalog_dir,
        policy_path,
        runner,
        clock=lambda: now[0],
    )
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    now[0] += 301
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 2
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)


def test_remove_uses_allowlisted_argv_verifies_absence_and_journals(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    installed = True
    calls = []

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append((argv, kwargs))
        assert isinstance(argv, list)
        assert kwargs["shell"] is False
        if argv[1:3] == ["plugin", "list"]:
            return subprocess_result(live_payload(installed=installed))
        if argv[1:3] == ["plugin", "remove"]:
            installed = False
            return subprocess_result(raw="removed /Users/alice sk-private-output")
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(
        target="ext-semgrep-mcp",
        scope="user",
        operation="remove",
    )
    result = service.execute(
        nonce=preflight["nonce"],
        target="ext-semgrep-mcp",
        scope="user",
        operation="remove",
        yes=True,
        allowed=True,
    )
    assert result["outcome"] == "success"
    assert ["codex", "plugin", "remove", "safe-plugin@official-marketplace"] in [
        argv for argv, _kwargs in calls
    ]
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    assert [(event["operation"], event["outcome"]) for event in audit["events"]] == [
        ("remove", "started"),
        ("remove", "success"),
    ]
    serialized = json.dumps(audit)
    assert "/Users/alice" not in serialized
    assert "sk-private-output" not in serialized


def test_high_risk_policy_requires_exact_threat_review_and_confirmations(tmp_path: Path) -> None:
    repo, _catalog_dir, policy_path = prepare_repo(
        tmp_path,
        high_risk=True,
        valid_threat_review=False,
    )
    with pytest.raises(Exception) as exc:
        load_install_policies(policy_path, repo_root=repo)
    assert "exact threat review" in str(exc.value)

    repo, catalog_dir, policy_path = prepare_repo(
        tmp_path / "valid",
        high_risk=True,
        valid_threat_review=True,
    )
    calls = []
    installed = False

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            return subprocess_result(live_payload(installed=installed))
        if argv[1:3] == ["plugin", "add"]:
            installed = True
            return subprocess_result()
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
            typed_plugin_id="wrong-plugin",
            data_scope_ack=False,
        )
    assert exc.value.exit_code == 2
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)

    confirmed = service.preflight(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
    )
    result = service.execute(
        nonce=confirmed["nonce"],
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        yes=True,
        allowed=True,
        typed_plugin_id="safe-plugin",
        data_scope_ack=True,
    )
    assert result["outcome"] == "success"


def test_mutations_are_serialized_across_service_instances(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    entered = threading.Event()
    release = threading.Event()
    installed = False
    add_calls = 0

    def runner(argv, **kwargs):
        nonlocal installed, add_calls
        if argv[1:3] == ["plugin", "list"]:
            return subprocess_result(live_payload(installed=installed))
        if argv[1:3] == ["plugin", "add"]:
            add_calls += 1
            entered.set()
            assert release.wait(5)
            installed = True
            return subprocess_result()
        raise AssertionError(argv)

    first = service_for(repo, catalog_dir, policy_path, runner, nonce_factory=lambda: "A" * 32)
    second = service_for(repo, catalog_dir, policy_path, runner, nonce_factory=lambda: "B" * 32)
    one = first.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    two = second.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    failures = []

    def execute_first():
        try:
            first.execute(
                nonce=one["nonce"],
                target="ext-semgrep-mcp",
                scope="user",
                operation="install",
                yes=True,
                allowed=True,
            )
        except Exception as exc:  # pragma: no cover - assertion captures unexpected worker failure
            failures.append(exc)

    thread = threading.Thread(target=execute_first)
    thread.start()
    assert entered.wait(5)
    with pytest.raises(InstallError) as exc:
        second.execute(
            nonce=two["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 2
    release.set()
    thread.join(5)
    assert not failures
    assert add_calls == 1


@pytest.mark.parametrize("failure_mode", ["nonzero", "timeout"])
def test_uncertain_install_command_always_triggers_verified_rollback(
    tmp_path: Path,
    failure_mode: str,
) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    installed = False
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            return subprocess_result(live_payload(installed=installed))
        if argv[1:3] == ["plugin", "add"]:
            installed = True
            if failure_mode == "timeout":
                raise subprocess.TimeoutExpired(
                    argv,
                    1,
                    output="/Users/alice sk-timeout-raw-output",
                )
            return subprocess_result(
                returncode=7,
                raw="/Users/alice sk-nonzero-raw-output",
            )
        if argv[1:3] == ["plugin", "remove"]:
            installed = False
            return subprocess_result(raw="removed")
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 1
    assert installed is False
    assert ["codex", "plugin", "remove", "safe-plugin@official-marketplace"] in calls
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    outcomes = [event["outcome"] for event in audit["events"]]
    assert outcomes == [
        "started",
        "command_failed",
        "rollback_started",
        "rollback_success",
        "command_failed_rolled_back",
    ]
    serialized = json.dumps(audit) + _exception_graph_text(exc.value)
    assert "/Users/alice" not in serialized
    assert "sk-timeout-raw-output" not in serialized
    assert "sk-nonzero-raw-output" not in serialized


def test_malformed_installed_record_cannot_fake_absence_during_rollback(
    tmp_path: Path,
) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    installed = False
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        nonlocal installed
        calls.append(argv)
        if argv[1:3] == ["plugin", "list"]:
            if installed:
                malformed = live_payload(installed=True)
                del malformed["plugins"][0]["version"]
                return subprocess_result(malformed)
            return subprocess_result(live_payload(installed=False))
        if argv[1:3] == ["plugin", "add"]:
            installed = True
            return subprocess_result()
        if argv[1:3] == ["plugin", "remove"]:
            installed = False
            return subprocess_result()
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    with pytest.raises(InstallError):
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert installed is False
    assert ["codex", "plugin", "remove", "safe-plugin@official-marketplace"] in calls


def test_malformed_inventory_cannot_false_verify_removal(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    installed = True
    remove_ran = False

    def runner(argv, **kwargs):
        nonlocal remove_ran
        if argv[1:3] == ["plugin", "list"]:
            if remove_ran:
                malformed = live_payload(installed=installed)
                malformed["plugins"][0]["installed"] = "true"
                return subprocess_result(malformed)
            return subprocess_result(live_payload(installed=True))
        if argv[1:3] == ["plugin", "remove"]:
            remove_ran = True
            return subprocess_result()
        raise AssertionError(argv)

    service = service_for(repo, catalog_dir, policy_path, runner)
    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="remove")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="remove",
            yes=True,
            allowed=True,
        )
    assert exc.value.exit_code == 1
    audit = json.loads(
        (repo / ".local-ai-lab" / "growth-audit-v1.json").read_text(encoding="utf-8")
    )
    assert audit["events"][-1]["outcome"] == "remove_verify_failed"


def test_catalog_connector_type_cannot_be_downgraded_by_policy(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    extension_path = catalog_dir / "extensions.json"
    payload = json.loads(extension_path.read_text(encoding="utf-8"))
    item = next(entry for entry in payload["items"] if entry["id"] == "ext-semgrep-mcp")
    item["type"] = "connector"
    extension_path.write_text(json.dumps(payload), encoding="utf-8")
    calls = []
    service = service_for(
        repo,
        catalog_dir,
        policy_path,
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(InstallError) as exc:
        service.preflight(
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            dry_run=True,
        )
    assert "high-risk policy" in str(exc.value)
    assert calls == []


def test_write_capable_or_unknown_mcp_cannot_bypass_high_risk_lane(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    extension_path = catalog_dir / "extensions.json"
    payload = json.loads(extension_path.read_text(encoding="utf-8"))
    item = next(entry for entry in payload["items"] if entry["id"] == "ext-semgrep-mcp")
    item["risk_facts"]["writes"] = "Write capability is not established by the review packet."
    extension_path.write_text(json.dumps(payload), encoding="utf-8")
    calls = []
    service = service_for(
        repo,
        catalog_dir,
        policy_path,
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(InstallError) as exc:
        service.preflight(
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            dry_run=True,
        )
    assert "non-read-only MCP" in str(exc.value)
    assert calls == []


def test_preflight_transactions_prevent_consumed_nonce_resurrection(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    service = service_for(repo, catalog_dir, policy_path, lambda *_args, **_kwargs: None)
    plan = service.plan(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        live_lookup=False,
    )
    state_path = repo / ".local-ai-lab" / "growth-preflights-v1.json"
    seed = PreflightStore(
        state_path,
        repo_root=repo,
        clock=lambda: 1000.0,
        nonce_factory=lambda: "A" * 32,
    )
    consumed_nonce, _expires = seed.issue(plan)
    issuer = PreflightStore(
        state_path,
        repo_root=repo,
        clock=lambda: 1000.0,
        nonce_factory=lambda: "B" * 32,
    )
    consumer = PreflightStore(state_path, repo_root=repo, clock=lambda: 1000.0)
    entered = threading.Event()
    release = threading.Event()
    issuer_done = threading.Event()
    consumer_done = threading.Event()
    failures: list[BaseException] = []
    original_write = issuer._write

    def delayed_write(payload):
        entered.set()
        assert release.wait(5)
        original_write(payload)

    issuer._write = delayed_write

    def issue_second():
        try:
            issuer.issue(plan)
        except BaseException as error:  # pragma: no cover - asserted below
            failures.append(error)
        finally:
            issuer_done.set()

    def consume_first():
        try:
            consumer.consume(consumed_nonce)
        except BaseException as error:  # pragma: no cover - asserted below
            failures.append(error)
        finally:
            consumer_done.set()

    issuer_thread = threading.Thread(target=issue_second)
    issuer_thread.start()
    assert entered.wait(5)
    consumer_thread = threading.Thread(target=consume_first)
    consumer_thread.start()
    assert not consumer_done.wait(0.1)
    release.set()
    assert issuer_done.wait(5)
    assert consumer_done.wait(5)
    issuer_thread.join(5)
    consumer_thread.join(5)
    assert failures == []
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert [entry["nonce"] for entry in state["entries"]] == ["B" * 32]


def test_nonce_expiry_is_checked_after_waiting_for_state_lock(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    service = service_for(repo, catalog_dir, policy_path, lambda *_args, **_kwargs: None)
    plan = service.plan(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        live_lookup=False,
    )
    state_path = repo / ".local-ai-lab" / "growth-preflights-v1.json"
    clock = [1000.0]
    seed = PreflightStore(
        state_path,
        repo_root=repo,
        clock=lambda: clock[0],
        nonce_factory=lambda: "A" * 32,
    )
    nonce, _expires = seed.issue(plan)
    holder = PreflightStore(
        state_path,
        repo_root=repo,
        clock=lambda: clock[0],
        nonce_factory=lambda: "B" * 32,
    )
    consumer = PreflightStore(state_path, repo_root=repo, clock=lambda: clock[0])
    entered = threading.Event()
    release = threading.Event()
    consume_done = threading.Event()
    consume_errors: list[BaseException] = []
    original_write = holder._write

    def delayed_write(payload):
        entered.set()
        assert release.wait(5)
        original_write(payload)

    holder._write = delayed_write
    holder_thread = threading.Thread(target=lambda: holder.issue(plan))
    holder_thread.start()
    assert entered.wait(5)

    def consume():
        try:
            consumer.consume(nonce)
        except BaseException as error:
            consume_errors.append(error)
        finally:
            consume_done.set()

    consumer_thread = threading.Thread(target=consume)
    consumer_thread.start()
    assert not consume_done.wait(0.1)
    clock[0] = 1301.0
    release.set()
    holder_thread.join(5)
    consumer_thread.join(5)
    assert len(consume_errors) == 1
    assert isinstance(consume_errors[0], InstallError)
    assert "invalid or expired" in str(consume_errors[0])


def test_operation_lease_serializes_across_processes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    release = context.Event()
    process = context.Process(
        target=_hold_operation_lease,
        args=(str(repo), ready, release),
    )
    process.start()
    try:
        assert ready.wait(10)
        with pytest.raises(InstallError) as exc, OperationLease(
            repo / ".local-ai-lab" / "growth-operation-v1.lock",
            repo_root=repo,
        ):
            raise AssertionError("second process must not acquire the mutation lease")
        assert exc.value.exit_code == 2
    finally:
        release.set()
        process.join(10)
        if process.is_alive():
            process.terminate()
            process.join(5)
    assert process.exitcode == 0


def test_audit_journal_retains_oldest_event_after_one_thousand(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    service = service_for(repo, catalog_dir, policy_path, lambda *_args, **_kwargs: None)
    plan = service.plan(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        live_lookup=False,
    )
    audit_path = repo / ".local-ai-lab" / "growth-audit-v1.json"
    audit_path.parent.mkdir(mode=0o700)
    events = []
    for index in range(1000):
        suffix = f"{index:020x}"
        events.append(
            {
                "id": f"audit-{suffix}",
                "correlation_id": f"job-{suffix}",
                "operation": "install",
                "target": plan.target,
                "host": plan.host,
                "source": plan.marketplace_source,
                "marketplace": plan.marketplace,
                "reviewed_version": plan.reviewed_version,
                "argv": list(plan.argv),
                "timestamp": "2026-07-21T12:00:00Z",
                "outcome": "started",
            }
        )
    audit_path.write_text(
        json.dumps({"schema_version": "growth-audit-v1", "events": events}),
        encoding="utf-8",
    )
    service.audit.append(
        plan,
        correlation_id="job-ffffffffffffffffffff",
        operation="install",
        argv=plan.argv,
        outcome="started",
    )
    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    assert len(payload["events"]) == 1001
    assert payload["events"][0]["id"] == "audit-00000000000000000000"


def test_nonfinite_preflight_expiry_and_private_raw_errors_fail_closed(
    tmp_path: Path,
) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess_result(live_payload(installed=False))

    service = service_for(repo, catalog_dir, policy_path, runner)
    plan = service.plan(
        target="ext-semgrep-mcp",
        scope="user",
        operation="install",
        live_lookup=False,
    )
    with pytest.raises(InstallError):
        service.preflights.issue(plan, ttl=float("nan"))

    preflight = service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    state_path = repo / ".local-ai-lab" / "growth-preflights-v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["entries"][0]["expires_at"] = float("nan")
    state_path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(InstallError) as exc:
        service.execute(
            nonce=preflight["nonce"],
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            yes=True,
            allowed=True,
        )
    assert not any(argv[1:3] == ["plugin", "add"] for argv in calls)
    graph = _exception_graph_text(exc.value)
    assert "/Users/alice" not in graph
    assert "sk-" not in graph

    state_path.write_text(
        '{"raw":"/Users/alice sk-private-state",',
        encoding="utf-8",
    )
    with pytest.raises(InstallError) as malformed:
        service.preflights.consume("Z" * 32)
    malformed_graph = _exception_graph_text(malformed.value)
    assert "/Users/alice" not in malformed_graph
    assert "sk-private-state" not in malformed_graph


def test_raw_inventory_exception_chain_is_fully_sanitized(tmp_path: Path) -> None:
    repo, catalog_dir, policy_path = prepare_repo(tmp_path)

    def runner(_argv, **_kwargs):
        raise OSError("/Users/alice sk-raw-subprocess-exception")

    service = service_for(repo, catalog_dir, policy_path, runner)
    with pytest.raises(InstallError) as exc:
        service.preflight(target="ext-semgrep-mcp", scope="user", operation="install")
    graph = _exception_graph_text(exc.value)
    assert "/Users/alice" not in graph
    assert "sk-raw-subprocess-exception" not in graph


def test_tracked_manifest_keeps_every_real_target_review_only() -> None:
    calls = []
    private = REPO_ROOT / ".local-ai-lab"
    service = GrowthInstallService(
        repo_root=REPO_ROOT,
        catalog_dir=SOURCE_CATALOG,
        policy_path=SOURCE_CATALOG / "install-policies.json",
        preflight_path=private / "growth-preflights-v1.json",
        audit_path=private / "growth-audit-v1.json",
        operation_lock_path=private / "growth-operation-v1.lock",
        runner=lambda *args, **kwargs: calls.append((args, kwargs)),
        which=lambda _host: "/safe/codex",
        environ={"PATH": "/safe/bin"},
        home_dir=Path("/safe/home"),
    )
    with pytest.raises(InstallError) as exc:
        service.preflight(
            target="ext-semgrep-mcp",
            scope="user",
            operation="install",
            dry_run=True,
        )
    assert exc.value.exit_code == 2
    assert "no exact reviewed execution policy" in str(exc.value)
    assert calls == []
