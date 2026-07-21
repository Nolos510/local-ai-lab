"""Handlers and parser wiring for the reviewed ``ai-lab growth`` flow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from local_ai_lab.growth.catalog import CatalogError, load_catalogs
from local_ai_lab.growth.discovery import (
    DISCOVERY_SOURCES,
    DiscoveryError,
    check_updates,
    create_review_draft,
    discover,
)
from local_ai_lab.growth.install import GrowthInstallService, InstallError
from local_ai_lab.growth.inventory import InventoryError, scan_inventory
from local_ai_lab.growth.state import StateError, load_state, update_progress, write_state_atomic

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG_DIR = REPO_ROOT / "data" / "growth_registry"
DEFAULT_STATE = REPO_ROOT / ".local-ai-lab" / "growth-state-v1.json"
DEFAULT_INBOX = REPO_ROOT / ".local-ai-lab" / "growth-inbox-v1.json"
DEFAULT_POLICY = DEFAULT_CATALOG_DIR / "install-policies.json"
DEFAULT_PREFLIGHTS = REPO_ROOT / ".local-ai-lab" / "growth-preflights-v1.json"
DEFAULT_AUDIT = REPO_ROOT / ".local-ai-lab" / "growth-audit-v1.json"
DEFAULT_OPERATION_LOCK = REPO_ROOT / ".local-ai-lab" / "growth-operation-v1.lock"
EFFORT_FILTERS = ("1-3", "4-6", "7-10")
ROLE_FILTERS = ("AIA", "AUT", "MLD")
PROGRESS_STATUSES = ("queued", "in_progress", "completed", "skipped")


def _safe_error(message: str) -> None:
    print(f"growth error: {message}", file=sys.stderr)


def _proof_is_evidenced(item: dict[str, Any], *, repo_root: Path) -> bool:
    try:
        path = (repo_root / item["proof_artifact"]).resolve()
        path.relative_to(repo_root.resolve())
    except (KeyError, OSError, ValueError):
        return False
    return path.is_file()


def _item_view(
    item: dict[str, Any],
    *,
    repo_root: Path,
    progress_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    view = dict(item)
    progress = progress_by_id.get(item["id"])
    view["progress_status"] = progress["status"] if progress else None
    view["evidenced"] = _proof_is_evidenced(item, repo_root=repo_root) or bool(
        progress and progress.get("evidence")
    )
    return view


def command_list(args: argparse.Namespace) -> int:
    if args.role is not None and args.role not in ROLE_FILTERS:
        _safe_error("unsupported career role")
        return 2
    if args.effort is not None and args.effort not in EFFORT_FILTERS:
        _safe_error("unsupported effort tier")
        return 2
    try:
        items = load_catalogs(args.catalog_dir)
        state = load_state(args.state)
    except (CatalogError, StateError) as exc:
        _safe_error(str(exc))
        return 1
    if args.kind:
        items = [
            item
            for item in items
            if item["catalog_kind"] == args.kind or item["type"] == args.kind
        ]
    if args.role:
        items = [item for item in items if args.role in item["career_lenses"]]
    if args.effort:
        items = [item for item in items if item["effort_tier"] == args.effort]
    progress_by_id = {entry["item_id"]: entry for entry in state["progress"]}
    views = [
        _item_view(item, repo_root=args.repo_root, progress_by_id=progress_by_id)
        for item in items
    ]
    views.sort(key=lambda item: (item["catalog_kind"], item["id"]))
    if args.json:
        print(json.dumps({"schema_version": "growth-list-v1", "items": views}, indent=2))
        return 0
    print("id\tkind\ttype\tstatus\treview_state\teffort\troles\tevidenced")
    for item in views:
        print(
            "{id}\t{catalog_kind}\t{type}\t{status}\t{review_state}\t"
            "{effort_tier}\t{roles}\t{evidenced}".format(
                **item,
                roles=",".join(item["career_lenses"]),
                evidenced="yes" if item["evidenced"] else "no",
            )
        )
    return 0


def command_scan(args: argparse.Namespace) -> int:
    if args.ecosystem not in {"repo", "codex", "claude", "all"}:
        _safe_error("unsupported inventory ecosystem")
        return 2
    try:
        items = load_catalogs(args.catalog_dir)
        state = load_state(args.state)
        inventory = scan_inventory(
            repo_root=args.repo_root,
            catalog_items=items,
            ecosystem=args.ecosystem,
        )
        if not args.dry_run:
            state["inventory"] = inventory
            write_state_atomic(args.state, state)
    except InventoryError as exc:
        _safe_error(str(exc))
        return exc.exit_code
    except (CatalogError, StateError) as exc:
        _safe_error(str(exc))
        return 1
    print(
        "id\tecosystem\tsource\tkind\tavailable\tconfigured\tinstalled\t"
        "enabled\treferenced\tevidenced"
    )
    for entry in inventory:
        bools = {
            field: "yes" if entry[field] else "no"
            for field in (
                "available",
                "configured",
                "installed",
                "enabled",
                "referenced",
                "evidenced",
            )
        }
        output = dict(entry)
        output.update(bools)
        print(
            "{id}\t{ecosystem}\t{source}\t{kind}\t{available}\t{configured}\t"
            "{installed}\t{enabled}\t{referenced}\t{evidenced}".format(
                **output,
            )
        )
    if args.dry_run:
        print("dry-run: private growth state was not changed")
    else:
        print(f"scan complete: {len(inventory)} sanitized inventory records stored")
    return 0


def command_progress(args: argparse.Namespace) -> int:
    if args.status not in PROGRESS_STATUSES:
        _safe_error("unsupported progress status")
        return 2
    try:
        items = load_catalogs(args.catalog_dir)
    except CatalogError as exc:
        _safe_error(str(exc))
        return 1
    item_ids = {item["id"] for item in items}
    if args.item not in item_ids:
        _safe_error("item is not in the reviewed Growth catalog")
        return 2
    try:
        load_state(args.state)
    except StateError as exc:
        _safe_error(str(exc))
        return 1
    try:
        update_progress(
            args.state,
            item_id=args.item,
            status=args.status,
            evidence_path=args.evidence,
            repo_root=args.repo_root,
        )
    except StateError as exc:
        _safe_error(str(exc))
        return 2
    print(f"progress updated: {args.item} -> {args.status}")
    return 0


def command_discover(args: argparse.Namespace) -> int:
    if not args.lookup:
        _safe_error("public metadata lookup requires explicit --lookup")
        return 2
    try:
        result = discover(
            source=args.source,
            query=args.query,
            inbox_path=args.inbox,
            repo_root=args.repo_root,
            sensitive_tokens=(Path.home().name,),
        )
    except DiscoveryError as exc:
        _safe_error(str(exc))
        return exc.exit_code
    print(
        "discovery complete: {stored} untrusted record(s) stored; {skipped} skipped; "
        "popularity is context, never approval".format(**result)
    )
    return 0


def command_check_updates(args: argparse.Namespace) -> int:
    if not args.lookup:
        _safe_error("public metadata lookup requires explicit --lookup")
        return 2
    try:
        items = load_catalogs(args.catalog_dir)
        result = check_updates(
            catalog_items=items,
            inbox_path=args.inbox,
            repo_root=args.repo_root,
            sensitive_tokens=(Path.home().name,),
        )
    except DiscoveryError as exc:
        _safe_error(str(exc))
        return exc.exit_code
    except CatalogError as exc:
        _safe_error(str(exc))
        return 1
    print(
        "update lookup complete: {stored} review record(s) stored; {skipped} unsupported; "
        "{failures} item failure(s)".format(**result)
    )
    return 0


def command_review(args: argparse.Namespace) -> int:
    try:
        draft = create_review_draft(
            inbox_path=args.inbox,
            repo_root=args.repo_root,
            inbox_id=args.inbox_id,
        )
    except DiscoveryError as exc:
        _safe_error(str(exc))
        return exc.exit_code
    print(
        f"review draft created: {draft['id']} "
        "(catalog promotion still requires a reviewed repo patch)"
    )
    return 0


def _install_service(args: argparse.Namespace) -> GrowthInstallService:
    return GrowthInstallService(
        repo_root=args.repo_root,
        catalog_dir=args.catalog_dir,
        policy_path=args.policy,
        preflight_path=args.preflights,
        audit_path=args.audit,
        operation_lock_path=args.operation_lock,
    )


def _mutation_paths_are_canonical(args: argparse.Namespace) -> bool:
    expected = {
        "repo_root": REPO_ROOT,
        "catalog_dir": DEFAULT_CATALOG_DIR,
        "policy": DEFAULT_POLICY,
        "preflights": DEFAULT_PREFLIGHTS,
        "audit": DEFAULT_AUDIT,
        "operation_lock": DEFAULT_OPERATION_LOCK,
    }
    return all(Path(getattr(args, field)) == path for field, path in expected.items())


def _print_preflight(result: dict[str, Any]) -> None:
    payload = {"schema_version": "growth-preflight-v1", **result}
    print(json.dumps(payload, indent=2, sort_keys=True))


def _command_mutation(args: argparse.Namespace, *, operation: str) -> int:
    allowed = args.allow_install if operation == "install" else args.allow_remove
    if not allowed:
        _safe_error(f"explicit --allow-{operation} consent is required")
        return 2
    if not _mutation_paths_are_canonical(args):
        _safe_error("Growth mutation authority is limited to canonical reviewed repository state")
        return 2
    if args.dry_run and args.yes:
        _safe_error("--dry-run cannot be combined with execution confirmation")
        return 2
    try:
        service = _install_service(args)
        if not args.yes:
            result = service.preflight(
                target=args.target,
                scope=args.scope,
                operation=operation,
                dry_run=args.dry_run,
            )
            _print_preflight(result)
            return 0
        if not args.nonce:
            _safe_error("a live preflight nonce is required for confirmation")
            return 2
        service.execute(
            nonce=args.nonce,
            target=args.target,
            scope=args.scope,
            operation=operation,
            yes=True,
            allowed=True,
            typed_plugin_id=args.confirm_target,
            data_scope_ack=args.ack_data_scope,
        )
    except InstallError as exc:
        _safe_error(str(exc))
        return exc.exit_code
    print(f"growth {operation} complete: {args.target}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    return _command_mutation(args, operation="install")


def command_remove(args: argparse.Namespace) -> int:
    return _command_mutation(args, operation="remove")


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    growth = subparsers.add_parser(
        "growth",
        help="Inspect tracked Growth catalogs and sanitized local inventory.",
    )
    commands = growth.add_subparsers(dest="growth_command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--catalog-dir",
        type=Path,
        default=DEFAULT_CATALOG_DIR,
        help=argparse.SUPPRESS,
    )
    common.add_argument("--state", type=Path, default=DEFAULT_STATE, help=argparse.SUPPRESS)
    common.add_argument("--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    common.add_argument("--inbox", type=Path, default=DEFAULT_INBOX, help=argparse.SUPPRESS)

    list_parser = commands.add_parser("list", parents=[common], help="List tracked catalog items.")
    list_parser.add_argument("--kind")
    list_parser.add_argument("--role")
    list_parser.add_argument("--effort")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(func=command_list)

    scan_parser = commands.add_parser(
        "scan",
        parents=[common],
        help="Run explicit read-only local inventory adapters.",
    )
    scan_parser.add_argument("--ecosystem", default="all")
    scan_parser.add_argument("--dry-run", action="store_true")
    scan_parser.set_defaults(func=command_scan)

    progress_parser = commands.add_parser(
        "progress",
        parents=[common],
        help="Update ignored personal progress without changing a catalog.",
    )
    progress_parser.add_argument("item", metavar="ITEM")
    progress_parser.add_argument("--status", required=True)
    progress_parser.add_argument("--evidence", type=Path)
    progress_parser.set_defaults(func=command_progress)

    discover_parser = commands.add_parser(
        "discover",
        parents=[common],
        help="Opt in to public metadata discovery without downloading or installing anything.",
    )
    discover_parser.add_argument("--source", required=True, choices=sorted(DISCOVERY_SOURCES))
    discover_parser.add_argument("--lookup", action="store_true")
    discover_parser.add_argument("--query")
    discover_parser.set_defaults(func=command_discover)

    updates_parser = commands.add_parser(
        "check-updates",
        parents=[common],
        help="Opt in to per-item public update metadata lookup.",
    )
    updates_parser.add_argument("--lookup", action="store_true")
    updates_parser.set_defaults(func=command_check_updates)

    review_parser = commands.add_parser(
        "review",
        parents=[common],
        help="Create an ignored review draft from an untrusted discovery record.",
    )
    review_parser.add_argument("inbox_id", metavar="INBOX_ID")
    review_parser.set_defaults(func=command_review)

    mutation_common = argparse.ArgumentParser(add_help=False, parents=[common])
    mutation_common.add_argument(
        "--policy", type=Path, default=DEFAULT_POLICY, help=argparse.SUPPRESS
    )
    mutation_common.add_argument(
        "--preflights",
        type=Path,
        default=DEFAULT_PREFLIGHTS,
        help=argparse.SUPPRESS,
    )
    mutation_common.add_argument(
        "--audit", type=Path, default=DEFAULT_AUDIT, help=argparse.SUPPRESS
    )
    mutation_common.add_argument(
        "--operation-lock",
        type=Path,
        default=DEFAULT_OPERATION_LOCK,
        help=argparse.SUPPRESS,
    )
    mutation_common.add_argument("--target", required=True)
    mutation_common.add_argument("--scope", required=True)
    mutation_common.add_argument("--dry-run", action="store_true")
    mutation_common.add_argument("--yes", action="store_true")
    mutation_common.add_argument("--nonce", help=argparse.SUPPRESS)
    mutation_common.add_argument("--confirm-target")
    mutation_common.add_argument("--ack-data-scope", action="store_true")

    install_parser = commands.add_parser(
        "install",
        parents=[mutation_common],
        help="Preflight or execute one reviewed official-host plugin install.",
    )
    install_parser.add_argument("--allow-install", action="store_true")
    install_parser.set_defaults(func=command_install, allow_remove=False)

    remove_parser = commands.add_parser(
        "remove",
        parents=[mutation_common],
        help="Preflight or execute one reviewed official-host plugin removal.",
    )
    remove_parser.add_argument("--allow-remove", action="store_true")
    remove_parser.set_defaults(func=command_remove, allow_install=False)
