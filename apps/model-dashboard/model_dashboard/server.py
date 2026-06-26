"""Local web server routing for the dependency-free model dashboard."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import db
from .components import (
    CANDIDATE_REGISTRY_PATH,
    DEFAULT_DASHBOARD_DB,
    EVAL_RESULTS_DIR,
    LOCAL_INVENTORY_REGISTRY_PATH,
    PROJECT_REGISTRY_PATH,
    REPO_ROOT,
    _is_loopback_host,
    _text,
)
from .filters import *
from .layout import NAV_ICONS, NAV_ITEMS, _layout
from .pages.actions import (
    _build_candidate_commands,
    _import_action_page,
    _import_artifact,
    _run_action_page,
    _run_action_started_page,
    _run_candidate_test,
    _start_candidate_test,
)
from .pages.artifact import _artifact_detail as _artifact_detail_page
from .pages.capability import _capability
from .pages.compare import _compare
from .pages.demo import _demo
from .pages.inventory import (
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
    _inventory_run_history,
    _lmstudio_cli_path,
    _match_inventory_model,
    _parse_lmstudio_inventory,
    _parse_ollama_inventory,
    _refresh_inventory,
    _remove_model_control,
    _removal_target_from_key,
    _scan_lmstudio_filesystem_models,
    _scan_mlx_lm_cached_models,
    _sync_local_inventory_candidates,
)
from .pages.inventory import _delete_model_action as _inventory_delete_model_action
from .pages.lab import _lab
from .pages.model_detail import _model_detail
from .pages.overview import _overview
from .pages.projects import _projects
from .pages.radar import _radar
from .pages.reports import _reports
from .pages.runs import _runs
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
    action_token="",
):
    return _artifact_detail_page(
        conn,
        benchmark_run_id,
        registry_path=registry_path,
        database_path=database_path,
        enable_import_actions=enable_import_actions,
        action_token=action_token,
        eval_results_dir=EVAL_RESULTS_DIR,
    )


def _delete_model_action(remove_key, confirm_delete, inventory_result, action_token, timeout=60):
    return _inventory_delete_model_action(
        remove_key,
        confirm_delete,
        inventory_result,
        action_token,
        timeout=timeout,
        lmstudio_root=LMSTUDIO_MODELS_ROOT,
        ollama_root=OLLAMA_MODELS_ROOT,
    )


def make_handler(
    database_path,
    enable_run_tests=False,
    enable_import_actions=False,
    enable_delete_actions=False,
    action_token="",
    run_test_timeout=3600,
    inventory_timeout=5,
    enable_inventory_refresh=True,
    candidate_registry_path=None,
    local_inventory_registry_path=None,
    eval_results_dir=None,
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
    inventory_cache = {"result": None}

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            try:
                with db.connect(database_path) as conn:
                    db.create_schema(conn)
                    html = self._route(parsed.path, parse_qs(parsed.query), conn)
                self.send_response(200)
            except Exception as exc:
                html = _layout("Error", "", f"<h2>Error</h2><p>{_text(exc)}</p>")
                self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def do_POST(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path not in (
                    "/actions/run-test",
                    "/actions/refresh-inventory",
                    "/actions/import-artifact",
                    "/actions/delete-model",
                ):
                    html = _layout("Not Found", "", "<h2>Page not found</h2>")
                    self.send_response(404)
                else:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 4096:
                        raise ValueError("Request body too large.")
                    form = parse_qs(self.rfile.read(length).decode("utf-8"))
                    token = _query_value(form, "token")
                    if token != action_token:
                        raise ValueError("Invalid action token.")
                    if parsed.path == "/actions/refresh-inventory":
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
                    elif parsed.path == "/actions/import-artifact":
                        if not enable_import_actions:
                            html = _layout(
                                "Import Actions Disabled",
                                "",
                                "<h2>Import actions disabled</h2><p>Restart the dashboard with <code>--enable-import-actions</code>.</p>",
                            )
                            self.send_response(403)
                        else:
                            benchmark_run_id = _query_value(form, "benchmark_run_id")
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
                    elif not enable_run_tests:
                        html = _layout(
                            "Run Tests Disabled",
                            "",
                            "<h2>Run tests disabled</h2><p>Restart the dashboard with <code>--enable-run-tests</code>.</p>",
                        )
                        self.send_response(403)
                    else:
                        candidate_id = _query_value(form, "candidate_id")
                        result = _start_candidate_test(
                            candidate_id,
                            candidate_registry_path,
                            eval_results_dir,
                            run_test_timeout,
                            database_path,
                        )
                        html = _run_action_started_page(result)
                        self.send_response(200)
            except Exception as exc:
                html = _layout("Action Error", "", f"<h2>Action Error</h2><p>{_text(exc)}</p>")
                self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, fmt, *args):
            return

        def _route(self, path, query, conn):
            if path == "/lab":
                return _lab(
                    conn,
                    enable_run_tests=enable_run_tests,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                    database_path=database_path,
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
                )
            if path == "/runs":
                return _runs(
                    conn,
                    query,
                    database_path=database_path,
                    eval_results_dir=eval_results_dir,
                    enable_import_actions=enable_import_actions,
                    action_token=action_token,
                )
            if path == "/compare":
                return _compare(conn, query)
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
                    run_history=_inventory_run_history(conn),
                )
            if path == "/radar":
                return _radar(conn, query)
            if path == "/specialty":
                return _specialty(conn, query)
            if path == "/projects":
                return _projects(query)
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
                    action_token=action_token,
                )
            if path.startswith("/models/"):
                model_id = int(path.rsplit("/", 1)[-1])
                return _model_detail(conn, model_id)
            return _layout("Not Found", "", "<h2>Page not found</h2>")

        def _inventory_run_history(self):
            with db.connect(database_path) as conn:
                db.create_schema(conn)
                return _inventory_run_history(conn)

    return DashboardHandler


def serve(
    database_path,
    host="127.0.0.1",
    port=8765,
    enable_run_tests=False,
    enable_import_actions=False,
    enable_delete_actions=False,
    run_test_timeout=3600,
    inventory_timeout=5,
):
    if not _is_loopback_host(host):
        raise ValueError("Dashboard serving requires a localhost or loopback bind host.")
    enable_inventory_refresh = _is_loopback_host(host)
    action_token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(
        (host, port),
        make_handler(
            database_path,
            enable_run_tests=enable_run_tests,
            enable_import_actions=enable_import_actions,
            enable_delete_actions=enable_delete_actions,
            action_token=action_token,
            run_test_timeout=run_test_timeout,
            inventory_timeout=inventory_timeout,
            enable_inventory_refresh=enable_inventory_refresh,
        ),
    )
    print(f"Serving Local Model Dashboard at http://{host}:{port}", flush=True)
    if enable_run_tests:
        print("Dashboard run-test actions enabled for local candidates.", flush=True)
    if enable_import_actions:
        print("Dashboard artifact import actions enabled for local CSV artifacts.", flush=True)
    if enable_delete_actions:
        print("Dashboard delete actions enabled for local inventory rows.", flush=True)
    if enable_inventory_refresh:
        print("Installed-model inventory refresh enabled for local runtimes.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
