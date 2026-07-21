"""Local web server routing for the dependency-free model dashboard."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import db, discover, growth as growth_data, score_review
from .runtime_health import runtime_health_snapshot
from .components import (
    CANDIDATE_REGISTRY_PATH,
    DEFAULT_DASHBOARD_DB,
    EVAL_RESULTS_DIR,
    LOCAL_INVENTORY_REGISTRY_PATH,
    PROJECT_REGISTRY_PATH,
    RADAR_UPSTREAM_STATE_PATH,
    REPO_ROOT,
    _is_loopback_host,
    _text,
)
from .filters import *
from .layout import NAV_ICONS, NAV_ITEMS, _layout
from .pages.actions import (
    _background_candidate_batch,
    _auto_reject_invalid_artifacts,
    _build_candidate_commands,
    _import_action_page,
    _import_artifact,
    _new_run_all_status,
    _run_action_page,
    _run_action_started_page,
    _run_all_started_page,
    _run_all_status_page,
    _run_candidate_test,
    _score_action_page,
    _score_all_started_page,
    _score_all_status_page,
    _score_artifact,
    _start_score_batch,
    _start_candidate_batch,
    _start_candidate_test,
    _startup_import_sync,
    _sync_pending_artifacts,
    _unscored_artifact_ids,
    _judge_preflight,
    _human_confirmation_batch_page,
    _human_score_action_page,
    _reject_artifact_score,
    _review_all_started_page,
    _review_all_status_page,
    _reviewer_preflight,
    _confirm_artifact_score,
    _confirm_reviewed_agreements,
    _start_review_batch,
)
from .pages.artifact import (
    _artifact_compare as _artifact_compare_page,
    _artifact_detail as _artifact_detail_page,
)
from .pages.capability import _capability
from .pages.compare import _compare
from .pages.demo import _demo
from .pages.inventory import (
    HF_HUB_CACHE_ROOT,
    LMSTUDIO_MODELS_ROOT,
    LMSTUDIO_WEIGHT_SUFFIXES,
    OLLAMA_MODELS_ROOT,
    _delete_confirm_page,
    _delete_result_page,
    _format_bytes,
    _has_lmstudio_weight_file,
    _inventory,
    _inventory_action_cell,
    _inventory_filter_values,
    _inventory_model_by_key,
    _inventory_model_key,
    _inventory_model_removable,
    _inventory_paths_cell,
    _inventory_run_allowed,
    _inventory_run_all_plan,
    _inventory_run_history,
    _lmstudio_cli_path,
    _match_inventory_model,
    _parse_lmstudio_inventory,
    _parse_ollama_inventory,
    _refresh_inventory,
    _remove_model_control,
    _removal_target_from_key,
    _run_all_confirm_page,
    _run_all_fingerprint,
    _scan_lmstudio_filesystem_models,
    _scan_mlx_lm_cached_models,
    _sync_local_inventory_candidates,
)
from .pages.inventory import _delete_model_action as _inventory_delete_model_action
from .pages.growth import (
    DEFAULT_GROWTH_CATALOG_DIR,
    DEFAULT_GROWTH_INBOX_PATH,
    DEFAULT_GROWTH_POLICY_PATH,
    DEFAULT_GROWTH_STATE_PATH,
    _growth,
    _growth_job_status_page,
    _growth_preflight_page,
)
from .pages.lab import _lab
from .pages.model_detail import _model_detail
from .pages.overview import _overview
from .pages.projects import _projects
from .pages.radar import _radar
from .pages.reports import _reports
from .pages.retrieval import RETRIEVAL_CORPORA_DIR, _retrieval
from .pages.runs import _runs
from .pages.review import _review_detail, _review_queue
from .pages.specialty import _specialty
from .pages.storage import _storage
from .components import *

SERVER_ICON_NAMES = (
    "ti-layout-dashboard",
    "ti-cpu",
    "ti-radar",
    "ti-binoculars",
    "ti-code",
    "ti-list-details",
    "ti-archive",
    "ti-chart-bar",
    "ti-file-analytics",
    "ti-flask",
    "ti-database",
)


def _artifact_detail(
    conn,
    benchmark_run_id,
    registry_path=CANDIDATE_REGISTRY_PATH,
    database_path=DEFAULT_DASHBOARD_DB,
    enable_import_actions=False,
    enable_score_actions=False,
    action_token="",
    eval_results_dir=None,
    reviewer_model=None,
):
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    return _artifact_detail_page(
        conn,
        benchmark_run_id,
        registry_path=registry_path,
        database_path=database_path,
        enable_import_actions=enable_import_actions,
        enable_score_actions=enable_score_actions,
        action_token=action_token,
        eval_results_dir=eval_results_dir,
        reviewer_model=reviewer_model,
    )


def _artifact_compare(conn, query=None, eval_results_dir=None):
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    return _artifact_compare_page(conn, query, eval_results_dir=eval_results_dir)


def _delete_model_action(remove_key, confirm_delete, inventory_result, action_token, timeout=60):
    return _inventory_delete_model_action(
        remove_key,
        confirm_delete,
        inventory_result,
        action_token,
        timeout=timeout,
        lmstudio_root=LMSTUDIO_MODELS_ROOT,
        ollama_root=OLLAMA_MODELS_ROOT,
        hf_cache_root=HF_HUB_CACHE_ROOT,
    )


def _resolve_import_actions(host, configured):
    if not _is_loopback_host(host):
        return False
    if configured is not None:
        return bool(configured)
    return True


def _loopback_authority(value, *, scheme=None):
    raw = str(value or "").strip()
    try:
        parsed = urlparse(raw if scheme else f"//{raw}")
        if (
            not raw
            or parsed.username is not None
            or parsed.password is not None
            or not parsed.hostname
            or not _is_loopback_host(parsed.hostname)
        ):
            return None
        if scheme:
            if parsed.scheme != scheme or parsed.path not in ("", "/"):
                return None
            if parsed.params or parsed.query or parsed.fragment:
                return None
        elif parsed.path or parsed.query or parsed.fragment:
            return None
        port = parsed.port
    except ValueError:
        return None
    return parsed.hostname.casefold(), port if port is not None else 80


def _growth_request_is_local(headers):
    """Reject DNS-rebound Growth reads/actions before exposing the token."""
    host = _loopback_authority(headers.get("Host"))
    if host is None:
        return False
    origin_value = headers.get("Origin")
    if not origin_value:
        return True
    return _loopback_authority(origin_value, scheme="http") == host


def _bounded_form_length(headers, *, maximum=4096):
    raw = headers.get("Content-Length")
    if not isinstance(raw, str) or not raw.isdigit() or len(raw) > 8:
        raise ValueError("Request body length is invalid.")
    length = int(raw)
    if length < 0 or length > maximum:
        raise ValueError("Request body too large.")
    content_type = headers.get("Content-Type")
    if content_type and not content_type.casefold().startswith("application/x-www-form-urlencoded"):
        raise ValueError("Request body type is invalid.")
    return length


class _GrowthJobCoordinator:
    """Retain sanitized step-only state for one serialized background mutation."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_job_id = None
        self._statuses = {}

    def start(self, service, *, operation, execute_kwargs):
        if operation not in {"install", "remove"}:
            raise ValueError("Growth plugin operation is invalid.")
        job_id = f"job-{secrets.token_hex(10)}"
        status = {
            "job_id": job_id,
            "operation": operation,
            "stage": "preflight",
            "step": 0,
            "total_steps": 3,
            "outcome": "pending",
        }
        with self._lock:
            if self._active_job_id is not None:
                raise ValueError("Another Growth install or removal is already running.")
            self._active_job_id = job_id
            self._statuses[job_id] = status
            while len(self._statuses) > 20:
                oldest = next(iter(self._statuses))
                if oldest == self._active_job_id:
                    break
                self._statuses.pop(oldest)

        def update_stage(stage, step, total_steps):
            safe_stage = (
                stage
                if stage in {"preflight", "installing", "verifying", "complete", "failed"}
                else "failed"
            )
            with self._lock:
                current = self._statuses.get(job_id)
                if current is not None:
                    current.update(
                        {
                            "stage": safe_stage,
                            "step": step if isinstance(step, int) and 0 <= step <= 3 else 0,
                            "total_steps": (
                                total_steps
                                if isinstance(total_steps, int) and total_steps == 3
                                else 3
                            ),
                        }
                    )

        def worker():
            try:
                service.execute(
                    **execute_kwargs,
                    stage=update_stage,
                    correlation_id=job_id,
                )
                outcome = "success"
                final_stage = "complete"
                final_step = 3
            except Exception as exc:
                outcome = "blocked" if getattr(exc, "exit_code", 1) == 2 else "failed"
                final_stage = "failed"
                final_step = None
            with self._lock:
                current = self._statuses.get(job_id)
                if current is not None:
                    retained_step = current.get("step", 0)
                    current.update(
                        {
                            "stage": final_stage,
                            "step": (
                                final_step
                                if final_step is not None
                                else retained_step
                                if isinstance(retained_step, int) and 0 <= retained_step <= 3
                                else 0
                            ),
                            "total_steps": 3,
                            "outcome": outcome,
                        }
                    )
                if self._active_job_id == job_id:
                    self._active_job_id = None

        thread = threading.Thread(target=worker, name=f"growth-{operation}", daemon=True)
        start_failed = False
        try:
            thread.start()
        except Exception:
            start_failed = True
            with self._lock:
                current = self._statuses.get(job_id)
                if current is not None:
                    current.update(
                        {
                            "stage": "failed",
                            "step": 0,
                            "total_steps": 3,
                            "outcome": "failed",
                        }
                    )
                if self._active_job_id == job_id:
                    self._active_job_id = None
        if start_failed:
            raise ValueError("Growth background job could not be started safely.")
        return self.snapshot(job_id)

    def snapshot(self, job_id):
        with self._lock:
            status = self._statuses.get(job_id)
            return dict(status) if status is not None else None


def _start_confirmed_candidate_batch(
    form,
    action_token,
    plan,
    eval_results_dir,
    run_test_timeout,
    database_path,
    starter,
):
    if _query_value(form, "token") != action_token:
        raise ValueError("Invalid action token.")
    if _query_value(form, "confirm_run_all") != "yes":
        raise ValueError("Run-all confirmation is required before execution.")
    if _query_value(form, "approval_scope") != _run_all_fingerprint(plan):
        raise ValueError("Run-all preflight changed; review the exact batch again before execution.")
    return starter(
        plan["runnable"],
        eval_results_dir,
        run_test_timeout,
        database_path,
    )


def make_handler(
    database_path,
    enable_run_tests=False,
    enable_import_actions=False,
    enable_delete_actions=False,
    enable_score_actions=False,
    enable_growth_installs=False,
    action_token="",
    run_test_timeout=3600,
    inventory_timeout=5,
    enable_inventory_refresh=True,
    candidate_registry_path=None,
    local_inventory_registry_path=None,
    eval_results_dir=None,
    project_registry_path=None,
    upstream_state_path=None,
    import_sync_result=None,
    judge_endpoint="http://127.0.0.1:1234/v1",
    judge_model=None,
    reviewer_endpoint="http://127.0.0.1:1234/v1",
    reviewer_model=None,
    retrieval_corpora_dir=None,
    growth_catalog_dir=None,
    growth_state_path=None,
    growth_inbox_path=None,
    growth_policy_path=None,
    growth_repo_root=None,
    growth_install_service=None,
    growth_job_coordinator=None,
):
    candidate_registry_path = (
        CANDIDATE_REGISTRY_PATH if candidate_registry_path is None else candidate_registry_path
    )
    local_inventory_registry_path = (
        LOCAL_INVENTORY_REGISTRY_PATH
        if local_inventory_registry_path is None
        else local_inventory_registry_path
    )
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    project_registry_path = (
        PROJECT_REGISTRY_PATH if project_registry_path is None else project_registry_path
    )
    upstream_state_path = (
        RADAR_UPSTREAM_STATE_PATH if upstream_state_path is None else upstream_state_path
    )
    retrieval_corpora_dir = (
        RETRIEVAL_CORPORA_DIR if retrieval_corpora_dir is None else retrieval_corpora_dir
    )
    growth_catalog_dir = (
        DEFAULT_GROWTH_CATALOG_DIR if growth_catalog_dir is None else growth_catalog_dir
    )
    growth_state_path = (
        DEFAULT_GROWTH_STATE_PATH if growth_state_path is None else growth_state_path
    )
    growth_repo_root = REPO_ROOT if growth_repo_root is None else growth_repo_root
    growth_inbox_path = (
        growth_repo_root / ".local-ai-lab" / "growth-inbox-v1.json"
        if growth_inbox_path is None
        else growth_inbox_path
    )
    growth_policy_path = (
        growth_catalog_dir / "install-policies.json"
        if growth_policy_path is None
        else growth_policy_path
    )
    if enable_growth_installs and growth_install_service is None:
        from local_ai_lab.growth.install import GrowthInstallService

        private_growth_dir = growth_repo_root / ".local-ai-lab"
        growth_install_service = GrowthInstallService(
            repo_root=growth_repo_root,
            catalog_dir=growth_catalog_dir,
            policy_path=growth_policy_path,
            preflight_path=private_growth_dir / "growth-preflights-v1.json",
            audit_path=private_growth_dir / "growth-audit-v1.json",
            operation_lock_path=private_growth_dir / "growth-operation-v1.lock",
        )
    growth_job_coordinator = growth_job_coordinator or _GrowthJobCoordinator()
    inventory_cache = {"result": None}
    import_sync_cache = {"result": import_sync_result}
    batch_run_cache = {}
    score_batch_cache = {}
    review_batch_cache = {}
    run_all_preflight_cache = {}
    runtime_health_cache = {"captured_at": 0.0, "snapshot": None}
    growth_progress_lock = threading.Lock()

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path.startswith("/growth") and not _growth_request_is_local(self.headers):
                html = _layout(
                    "Growth Unavailable",
                    "",
                    "<h2>Growth unavailable</h2><p>This local cockpit requires a loopback Host.</p>",
                )
                self.send_response(400)
            else:
                try:
                    with db.connect(database_path) as conn:
                        db.create_schema(conn)
                        html = self._route(parsed.path, parse_qs(parsed.query), conn)
                    self.send_response(200)
                except Exception as exc:
                    message = (
                        "Growth page could not be rendered safely."
                        if parsed.path.startswith("/growth")
                        else _text(exc)
                    )
                    html = _layout("Error", "", f"<h2>Error</h2><p>{message}</p>")
                    self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if parsed.path.startswith("/growth"):
                self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def do_POST(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path not in (
                    "/actions/run-test",
                    "/actions/refresh-inventory",
                    "/actions/import-artifact",
                    "/actions/import-all",
                    "/actions/suggest-scores",
                    "/actions/score-all-unscored",
                    "/actions/review-all-drafts",
                    "/actions/review-score",
                    "/actions/confirm-score",
                    "/actions/confirm-reviewed-agreements",
                    "/actions/reject-score",
                    "/actions/delete-model",
                    "/actions/run-all",
                    "/actions/dismiss-upstream-update",
                    "/actions/growth-progress",
                    "/actions/growth-install-preflight",
                    "/actions/growth-install-execute",
                ):
                    html = _layout("Not Found", "", "<h2>Page not found</h2>")
                    self.send_response(404)
                else:
                    growth_action = parsed.path.startswith("/actions/growth-")
                    if growth_action and (
                        not _growth_request_is_local(self.headers)
                        or not _is_loopback_host(self.client_address[0])
                    ):
                        raise ValueError("Growth actions require a loopback action token.")
                    if growth_action and not action_token:
                        raise ValueError("Growth actions require a configured action token.")
                    length = _bounded_form_length(self.headers)
                    form = parse_qs(self.rfile.read(length).decode("utf-8"))
                    token = _query_value(form, "token")
                    if token != action_token:
                        raise ValueError("Invalid action token.")
                    if parsed.path in (
                        "/actions/growth-install-preflight",
                        "/actions/growth-install-execute",
                    ):
                        if not enable_growth_installs or growth_install_service is None:
                            html = _layout(
                                "Growth Installs Disabled",
                                "/growth",
                                "<h2>Growth installs disabled</h2><p>Restart the dashboard with <code>--enable-growth-installs</code>.</p>",
                            )
                            self.send_response(403)
                        elif parsed.path == "/actions/growth-install-preflight":
                            result = growth_install_service.preflight(
                                target=_query_value(form, "target"),
                                scope=_query_value(form, "scope"),
                                operation=_query_value(form, "operation"),
                                dry_run=False,
                            )
                            html = _growth_preflight_page(result, action_token)
                            self.send_response(200)
                        else:
                            operation = _query_value(form, "operation")
                            started = growth_job_coordinator.start(
                                growth_install_service,
                                operation=operation,
                                execute_kwargs={
                                    "nonce": _query_value(form, "nonce"),
                                    "target": _query_value(form, "target"),
                                    "scope": _query_value(form, "scope"),
                                    "operation": operation,
                                    "yes": _query_value(form, "yes") == "yes",
                                    "allowed": True,
                                    "typed_plugin_id": _query_value(
                                        form,
                                        "confirm_target",
                                    )
                                    or None,
                                    "data_scope_ack": (
                                        _query_value(form, "ack_data_scope") == "yes"
                                    ),
                                },
                            )
                            html = _growth_job_status_page(started)
                            self.send_response(202)
                    elif parsed.path == "/actions/growth-progress":
                        if not action_token:
                            raise ValueError("Growth progress requires a loopback action token.")
                        item_id = _query_value(form, "item_id")
                        status = _query_value(form, "status")
                        evidence = _query_value(form, "evidence")
                        view = _query_value(form, "view")
                        with growth_progress_lock:
                            catalog_items = growth_data.load_catalogs(growth_catalog_dir)
                            growth_data.update_progress(
                                growth_state_path,
                                catalog_items=catalog_items,
                                item_id=item_id,
                                status=status,
                                evidence=evidence or None,
                                repo_root=growth_repo_root,
                            )
                        html = _growth(
                            {"view": [view]},
                            catalog_dir=growth_catalog_dir,
                            state_path=growth_state_path,
                            repo_root=growth_repo_root,
                            action_token=action_token,
                            notice=f"Personal progress updated: {item_id} → {status}.",
                            inbox_path=growth_inbox_path,
                            policy_path=growth_policy_path,
                            enable_growth_installs=enable_growth_installs,
                        )
                        self.send_response(200)
                    elif parsed.path == "/actions/dismiss-upstream-update":
                        candidate_id = _query_value(form, "candidate_id")
                        discover.dismiss_upstream_update(upstream_state_path, candidate_id)
                        with db.connect(database_path) as conn:
                            db.create_schema(conn)
                            html = _radar(
                                conn,
                                registry_path=candidate_registry_path,
                                local_inventory_path=local_inventory_registry_path,
                                project_registry_path=project_registry_path,
                                upstream_state_path=upstream_state_path,
                                action_token=action_token,
                            )
                        self.send_response(200)
                    elif parsed.path in (
                        "/actions/review-all-drafts",
                        "/actions/review-score",
                        "/actions/confirm-score",
                        "/actions/confirm-reviewed-agreements",
                        "/actions/reject-score",
                    ):
                        if not enable_score_actions:
                            html = _layout(
                                "Score Actions Disabled",
                                "",
                                "<h2>Score actions disabled</h2><p>Restart the dashboard with <code>--enable-score-actions</code>.</p>",
                            )
                            self.send_response(403)
                        else:
                            benchmark_run_id = _query_value(form, "benchmark_run_id")
                            if parsed.path in (
                                "/actions/review-all-drafts",
                                "/actions/review-score",
                            ):
                                if parsed.path == "/actions/review-all-drafts":
                                    available_ids = set(
                                        score_review.reviewable_artifact_ids(eval_results_dir)
                                    )
                                    submitted_ids = form.get("benchmark_run_id", [])
                                    if isinstance(submitted_ids, str):
                                        submitted_ids = [submitted_ids]
                                    run_ids = [
                                        run_id
                                        for run_id in submitted_ids
                                        if run_id in available_ids
                                    ]
                                    if not submitted_ids:
                                        run_ids = sorted(available_ids)
                                else:
                                    run_ids = [benchmark_run_id]
                                started = _start_review_batch(
                                    run_ids,
                                    eval_results_dir,
                                    run_test_timeout,
                                    reviewer_endpoint,
                                    reviewer_model,
                                    judge_endpoint,
                                    judge_model,
                                    database_path,
                                )
                                review_batch_cache[started["batch_id"]] = started["status"]
                                while len(review_batch_cache) > 20:
                                    review_batch_cache.pop(next(iter(review_batch_cache)))
                                html = _review_all_started_page(started)
                            elif parsed.path == "/actions/confirm-score":
                                result = _confirm_artifact_score(
                                    benchmark_run_id,
                                    form,
                                    database_path,
                                    eval_results_dir,
                                    run_test_timeout,
                                )
                                html = _human_score_action_page(result)
                            elif parsed.path == "/actions/confirm-reviewed-agreements":
                                submitted_ids = form.get("benchmark_run_id", [])
                                if isinstance(submitted_ids, str):
                                    submitted_ids = [submitted_ids]
                                result = _confirm_reviewed_agreements(
                                    submitted_ids,
                                    form,
                                    database_path,
                                    eval_results_dir,
                                    run_test_timeout,
                                )
                                html = _human_confirmation_batch_page(result)
                            else:
                                result = _reject_artifact_score(
                                    benchmark_run_id,
                                    form,
                                    database_path,
                                    eval_results_dir,
                                )
                                html = _human_score_action_page(result)
                            self.send_response(200)
                    elif parsed.path == "/actions/refresh-inventory":
                        if not enable_inventory_refresh:
                            html = _layout(
                                "Inventory Refresh Disabled",
                                "",
                                "<h2>Inventory refresh disabled</h2><p>Refresh is available only on a localhost or loopback dashboard bind.</p>",
                            )
                            self.send_response(403)
                        else:
                            inventory_cache["result"] = _refresh_inventory(inventory_timeout)
                            inventory_cache["result"]["registration"] = (
                                _sync_local_inventory_candidates(
                                    inventory_cache["result"],
                                    candidate_registry_path,
                                    local_inventory_registry_path,
                                )
                            )
                            if enable_import_actions:
                                import_sync_cache["result"] = _sync_pending_artifacts(
                                    database_path,
                                    eval_results_dir,
                                    source="automatic",
                                )
                            html = _inventory(
                                inventory_result=inventory_cache["result"],
                                action_token=action_token,
                                enable_run_tests=enable_run_tests,
                                enable_delete_actions=enable_delete_actions,
                                enable_refresh=enable_inventory_refresh,
                                registry_path=candidate_registry_path,
                                local_inventory_path=local_inventory_registry_path,
                                run_history=self._inventory_run_history(),
                            )
                            self.send_response(200)
                    elif parsed.path in (
                        "/actions/import-artifact",
                        "/actions/import-all",
                        "/actions/suggest-scores",
                        "/actions/score-all-unscored",
                    ):
                        if parsed.path in (
                            "/actions/suggest-scores",
                            "/actions/score-all-unscored",
                        ) and not enable_score_actions:
                            html = _layout(
                                "Score Actions Disabled",
                                "",
                                "<h2>Score actions disabled</h2><p>Restart the dashboard with <code>--enable-score-actions</code>.</p>",
                            )
                            self.send_response(403)
                        elif parsed.path not in (
                            "/actions/suggest-scores",
                            "/actions/score-all-unscored",
                        ) and not enable_import_actions:
                            html = _layout(
                                "Import Actions Disabled",
                                "",
                                "<h2>Import actions disabled</h2><p>Restart the dashboard with <code>--enable-import-actions</code>.</p>",
                            )
                            self.send_response(403)
                        else:
                            if parsed.path == "/actions/score-all-unscored":
                                run_ids = _unscored_artifact_ids(
                                    eval_results_dir,
                                    database_path,
                                )
                                started = _start_score_batch(
                                    run_ids,
                                    database_path,
                                    eval_results_dir,
                                    run_test_timeout,
                                    judge_endpoint,
                                    judge_model,
                                )
                                score_batch_cache[started["batch_id"]] = started["status"]
                                while len(score_batch_cache) > 20:
                                    score_batch_cache.pop(next(iter(score_batch_cache)))
                                html = _score_all_started_page(started)
                            elif parsed.path == "/actions/import-all":
                                result = _sync_pending_artifacts(
                                    database_path,
                                    eval_results_dir,
                                    source="manual",
                                )
                                import_sync_cache["result"] = result
                                with db.connect(database_path) as conn:
                                    db.create_schema(conn)
                                    html = _runs(
                                        conn,
                                        database_path=database_path,
                                        eval_results_dir=eval_results_dir,
                                        enable_import_actions=enable_import_actions,
                                        enable_score_actions=enable_score_actions,
                                        action_token=action_token,
                                        import_sync_result=result,
                                    )
                            else:
                                benchmark_run_id = _query_value(form, "benchmark_run_id")
                                if parsed.path == "/actions/suggest-scores":
                                    _judge_preflight(
                                        judge_endpoint,
                                        judge_model,
                                        min(run_test_timeout, 10),
                                    )
                                    result = _score_artifact(
                                        benchmark_run_id,
                                        database_path,
                                        eval_results_dir,
                                        run_test_timeout,
                                        judge_endpoint,
                                        judge_model,
                                    )
                                    html = _score_action_page(result)
                                else:
                                    result = _import_artifact(
                                        benchmark_run_id,
                                        database_path,
                                        eval_results_dir,
                                    )
                                    html = _import_action_page(result)
                            self.send_response(200)
                    elif parsed.path == "/actions/delete-model":
                        if not enable_delete_actions:
                            html = _layout(
                                "Delete Actions Disabled",
                                "",
                                "<h2>Delete actions disabled</h2><p>Restart the dashboard with <code>--enable-delete-actions</code>.</p>",
                            )
                            self.send_response(403)
                        else:
                            remove_key = _query_value(form, "remove_key")
                            confirm_delete = _query_value(form, "confirm_delete")
                            html, result = _delete_model_action(
                                remove_key,
                                confirm_delete,
                                inventory_cache["result"],
                                action_token,
                            )
                            if result is not None:
                                inventory_cache["result"] = _refresh_inventory(
                                    inventory_timeout
                                )
                            self.send_response(200)
                    elif parsed.path == "/actions/run-all":
                        if not enable_run_tests:
                            html = _layout(
                                "Run Tests Disabled",
                                "",
                                "<h2>Run tests disabled</h2><p>Restart the dashboard with <code>--enable-run-tests</code>.</p>",
                            )
                            self.send_response(403)
                        else:
                            if enable_score_actions:
                                _judge_preflight(
                                    judge_endpoint,
                                    judge_model,
                                    min(run_test_timeout, 10),
                                )
                            approval_scope = _query_value(form, "approval_scope")
                            plan = run_all_preflight_cache.get(approval_scope)
                            if plan is None:
                                raise ValueError(
                                    "Run-all preflight is missing or expired; review the exact batch again before execution."
                                )
                            started = _start_confirmed_candidate_batch(
                                form,
                                action_token,
                                plan,
                                eval_results_dir,
                                run_test_timeout,
                                database_path,
                                lambda runnable, eval_dir, timeout, db_path: _start_candidate_batch(
                                    runnable,
                                    eval_dir,
                                    timeout,
                                    db_path,
                                    {
                                        "enabled": enable_score_actions,
                                        "endpoint": judge_endpoint,
                                        "judge_model": judge_model,
                                    },
                                ),
                            )
                            run_all_preflight_cache.pop(approval_scope, None)
                            batch_run_cache[started["batch_id"]] = started["status"]
                            while len(batch_run_cache) > 20:
                                batch_run_cache.pop(next(iter(batch_run_cache)))
                            html = _run_all_started_page(started)
                            self.send_response(200)
                    elif not enable_run_tests:
                        html = _layout(
                            "Run Tests Disabled",
                            "",
                            "<h2>Run tests disabled</h2><p>Restart the dashboard with <code>--enable-run-tests</code>.</p>",
                        )
                        self.send_response(403)
                    else:
                        if enable_score_actions:
                            _judge_preflight(
                                judge_endpoint,
                                judge_model,
                                min(run_test_timeout, 10),
                            )
                        candidate_id = _query_value(form, "candidate_id")
                        result = _start_candidate_test(
                            candidate_id,
                            candidate_registry_path,
                            eval_results_dir,
                            run_test_timeout,
                            database_path,
                            {
                                "enabled": enable_score_actions,
                                "endpoint": judge_endpoint,
                                "judge_model": judge_model,
                            },
                        )
                        html = _run_action_started_page(result)
                        self.send_response(200)
            except Exception as exc:
                message = (
                    "Growth action was blocked or failed safely."
                    if parsed.path.startswith("/actions/growth-")
                    else _text(exc)
                )
                html = _layout("Action Error", "", f"<h2>Action Error</h2><p>{message}</p>")
                self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if parsed.path.startswith("/actions/growth-"):
                self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, fmt, *args):
            return

        def _runtime_health(self):
            now = time.monotonic()
            if (
                runtime_health_cache["snapshot"] is None
                or now - runtime_health_cache["captured_at"] >= 15
            ):
                runtime_health_cache["snapshot"] = runtime_health_snapshot(
                    enable_score_actions=enable_score_actions,
                    judge_endpoint=judge_endpoint,
                    judge_model=judge_model,
                    reviewer_endpoint=reviewer_endpoint,
                    reviewer_model=reviewer_model,
                )
                runtime_health_cache["captured_at"] = now
            return runtime_health_cache["snapshot"]

        def _route(self, path, query, conn):
            if path == "/lab":
                return _lab(
                    conn,
                    enable_run_tests=enable_run_tests,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                    database_path=database_path,
                    registry_path=candidate_registry_path,
                    eval_results_dir=eval_results_dir,
                    project_registry_path=project_registry_path,
                    runtime_health=self._runtime_health(),
                )
            if path == "/capability":
                return _capability(conn)
            if path == "/":
                return _overview(
                    conn,
                    query,
                    registry_path=candidate_registry_path,
                    eval_results_dir=eval_results_dir,
                    local_inventory_path=local_inventory_registry_path,
                    upstream_state_path=upstream_state_path,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                    import_sync_result=import_sync_cache["result"],
                    runtime_health=self._runtime_health(),
                )
            if path == "/reviews":
                return _review_queue(
                    eval_results_dir,
                    conn=conn,
                    query=query,
                    enable_score_actions=enable_score_actions,
                    action_token=action_token,
                    reviewer_model=reviewer_model,
                )
            if path.startswith("/reviews/"):
                benchmark_run_id = path.rsplit("/", 1)[-1]
                return _review_detail(
                    benchmark_run_id,
                    eval_results_dir,
                    enable_score_actions=enable_score_actions,
                    action_token=action_token,
                    reviewer_model=reviewer_model,
                )
            if path == "/runs":
                return _runs(
                    conn,
                    query,
                    database_path=database_path,
                    registry_path=candidate_registry_path,
                    local_inventory_path=local_inventory_registry_path,
                    eval_results_dir=eval_results_dir,
                    enable_import_actions=enable_import_actions,
                    enable_score_actions=enable_score_actions,
                    action_token=action_token,
                    import_sync_result=import_sync_cache["result"],
                )
            if path == "/retrieval":
                return _retrieval(retrieval_corpora_dir)
            if path == "/compare":
                return _compare(conn, query)
            if path == "/artifacts/compare":
                return _artifact_compare(conn, query, eval_results_dir=eval_results_dir)
            if path == "/inventory":
                return _inventory(
                    query=query,
                    inventory_result=inventory_cache["result"],
                    action_token=action_token,
                    enable_run_tests=enable_run_tests,
                    enable_delete_actions=enable_delete_actions,
                    enable_refresh=enable_inventory_refresh,
                    registry_path=candidate_registry_path,
                    local_inventory_path=local_inventory_registry_path,
                    run_history=_inventory_run_history(
                        conn,
                        _load_radar_candidates(
                            candidate_registry_path,
                            local_inventory_registry_path,
                        ),
                    ),
                    decisions=db.list_decisions(conn),
                )
            if path == "/inventory/run-all":
                if not enable_run_tests:
                    return _layout(
                        "Run Tests Disabled",
                        "/inventory",
                        "<h2>Run tests disabled</h2><p>Restart the dashboard with <code>--enable-run-tests</code>.</p>",
                    )
                plan = _inventory_run_all_plan(
                    inventory_cache["result"],
                    candidate_registry_path,
                    local_inventory_registry_path,
                    eval_results_dir,
                    database_path,
                )
                approval_scope = _run_all_fingerprint(plan)
                run_all_preflight_cache[approval_scope] = plan
                while len(run_all_preflight_cache) > 20:
                    run_all_preflight_cache.pop(next(iter(run_all_preflight_cache)))
                return _run_all_confirm_page(plan, action_token)
            if path == "/inventory/run-all/status":
                batch_id = _query_value(query, "batch_id")
                status = batch_run_cache.get(batch_id)
                if status is None:
                    return _layout(
                        "Run All Summary",
                        "/inventory",
                        "<section class=\"panel\"><h2>Batch summary unavailable</h2><p>The batch id is missing, unknown, or no longer retained by this dashboard process.</p><p><a href=\"/inventory\">Back to My Models</a></p></section>",
                    )
                return _run_all_status_page(status)
            if path == "/runs/score-all/status":
                batch_id = _query_value(query, "batch_id")
                status = score_batch_cache.get(batch_id)
                if status is None:
                    return _layout(
                        "Bulk Draft Scoring",
                        "/runs",
                        '<section class="panel"><h2>Scoring summary unavailable</h2><p>The batch id is missing, unknown, or no longer retained by this dashboard process.</p><p><a href="/runs">Back to Benchmark</a></p></section>',
                    )
                return _score_all_status_page(status)
            if path == "/runs/review-all/status":
                batch_id = _query_value(query, "batch_id")
                status = review_batch_cache.get(batch_id)
                if status is None:
                    return _layout(
                        "Independent Draft Review",
                        "/runs",
                        '<section class="panel"><h2>Review summary unavailable</h2><p>The batch id is missing, unknown, or no longer retained by this dashboard process.</p><p><a href="/reviews">Back to Draft Review Queue</a></p></section>',
                    )
                return _review_all_status_page(status)
            if path == "/radar":
                return _radar(
                    conn,
                    query,
                    registry_path=candidate_registry_path,
                    local_inventory_path=local_inventory_registry_path,
                    project_registry_path=project_registry_path,
                    upstream_state_path=upstream_state_path,
                    action_token=action_token,
                )
            if path == "/growth":
                return _growth(
                    query,
                    catalog_dir=growth_catalog_dir,
                    state_path=growth_state_path,
                    repo_root=growth_repo_root,
                    action_token=action_token,
                    inbox_path=growth_inbox_path,
                    policy_path=growth_policy_path,
                    enable_growth_installs=enable_growth_installs,
                )
            if path == "/growth/install/status":
                job_id = _query_value(query, "job")
                status = growth_job_coordinator.snapshot(job_id)
                if status is None:
                    status = {
                        "job_id": "unavailable",
                        "operation": "plugin",
                        "stage": "failed",
                        "step": 0,
                        "total_steps": 3,
                        "outcome": "unavailable",
                    }
                return _growth_job_status_page(status)
            if path == "/specialty":
                return _specialty(conn, query, registry_path=candidate_registry_path)
            if path == "/projects":
                return _projects(query, registry_path=project_registry_path)
            if path == "/storage":
                return _storage(conn, query)
            if path == "/reports":
                return _reports(conn, database_path)
            if path == "/demo":
                return _demo(conn)
            if path.startswith("/artifacts/"):
                benchmark_run_id = path.rsplit("/", 1)[-1]
                return _artifact_detail(
                    conn,
                    benchmark_run_id,
                    database_path=database_path,
                    enable_import_actions=enable_import_actions,
                    enable_score_actions=enable_score_actions,
                    action_token=action_token,
                    eval_results_dir=eval_results_dir,
                    reviewer_model=reviewer_model,
                )
            if path.startswith("/models/"):
                model_id = int(path.rsplit("/", 1)[-1])
                return _model_detail(conn, model_id)
            return _layout("Not Found", "", "<h2>Page not found</h2>")

        def _inventory_run_history(self):
            with db.connect(database_path) as conn:
                db.create_schema(conn)
                return _inventory_run_history(
                    conn,
                    _load_radar_candidates(
                        candidate_registry_path,
                        local_inventory_registry_path,
                    ),
                )

    return DashboardHandler


def serve(
    database_path,
    host="127.0.0.1",
    port=8765,
    enable_run_tests=False,
    enable_import_actions=None,
    enable_delete_actions=False,
    enable_score_actions=False,
    enable_growth_installs=False,
    run_test_timeout=3600,
    inventory_timeout=5,
    eval_results_dir=None,
    judge_endpoint="http://127.0.0.1:1234/v1",
    judge_model=None,
    reviewer_endpoint="http://127.0.0.1:1234/v1",
    reviewer_model=None,
):
    enable_import_actions = _resolve_import_actions(host, enable_import_actions)
    if not _is_loopback_host(host):
        raise ValueError("Dashboard serving requires a localhost or loopback bind host.")
    eval_results_dir = EVAL_RESULTS_DIR if eval_results_dir is None else eval_results_dir
    enable_inventory_refresh = _is_loopback_host(host)
    triage_result = _auto_reject_invalid_artifacts(
        database_path,
        eval_results_dir,
        enabled=enable_score_actions,
    )
    import_sync_result = _startup_import_sync(
        database_path,
        eval_results_dir,
        enabled=enable_import_actions,
    )
    import_sync_result["evidence_triage"] = triage_result
    action_token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(
        (host, port),
        make_handler(
            database_path,
            enable_run_tests=enable_run_tests,
            enable_import_actions=enable_import_actions,
            enable_delete_actions=enable_delete_actions,
            enable_score_actions=enable_score_actions,
            enable_growth_installs=enable_growth_installs,
            action_token=action_token,
            run_test_timeout=run_test_timeout,
            inventory_timeout=inventory_timeout,
            enable_inventory_refresh=enable_inventory_refresh,
            eval_results_dir=eval_results_dir,
            import_sync_result=import_sync_result,
            judge_endpoint=judge_endpoint,
            judge_model=judge_model,
            reviewer_endpoint=reviewer_endpoint,
            reviewer_model=reviewer_model,
        ),
    )
    print(f"Serving Local Model Dashboard at http://{host}:{port}", flush=True)
    if enable_run_tests:
        print("Dashboard run-test actions enabled for local candidates.", flush=True)
    if enable_import_actions:
        print("Dashboard artifact import actions enabled for local CSV artifacts.", flush=True)
    if enable_delete_actions:
        print("Dashboard delete actions enabled for local inventory rows.", flush=True)
    if enable_score_actions:
        print("Dashboard draft-score actions enabled for local benchmark artifacts.", flush=True)
        if reviewer_model:
            print(
                f"Independent draft reviewer configured: {reviewer_model}",
                flush=True,
            )
    if enable_growth_installs:
        print("Reviewed Growth install/remove actions enabled.", flush=True)
    if enable_inventory_refresh:
        print("Installed-model inventory refresh enabled for local runtimes.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
