"""Sanitized, read-only health checks for local dashboard dependencies."""

from __future__ import annotations

import http.client
import ipaddress
import json
import os
import shutil
from datetime import datetime
from urllib.parse import urlparse, urlunparse

try:
    from datetime import UTC
except ImportError:  # Python 3.9 system runtime compatibility.
    from datetime import timezone as _timezone

    UTC = _timezone.utc  # noqa: UP017


def _is_loopback(hostname):
    if str(hostname or "").lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(str(hostname or "")).is_loopback
    except ValueError:
        return False


def _local_endpoint(value, suffix):
    parsed = urlparse(str(value or ""))
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("endpoint must be an HTTP(S) URL with a host")
    if not _is_loopback(parsed.hostname):
        raise ValueError("endpoint must use localhost or a loopback IP")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("endpoint must not include credentials, query, or fragment")
    base_path = parsed.path.rstrip("/")
    path = f"{base_path}/{suffix.lstrip('/')}"
    target = parsed._replace(path=path, params="", query="", fragment="")
    origin = parsed._replace(path="", params="", query="", fragment="")
    return target, urlunparse(origin)


def _get(target, timeout, headers=None):
    connection_class = (
        http.client.HTTPSConnection
        if target.scheme == "https"
        else http.client.HTTPConnection
    )
    connection = connection_class(target.hostname, port=target.port, timeout=timeout)
    try:
        connection.request("GET", target.path, headers=headers or {})
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body
    finally:
        connection.close()


def _model_inventory(endpoint, timeout):
    target, origin = _local_endpoint(endpoint, "models")
    headers = {}
    token = os.environ.get("LM_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        status, body = _get(target, timeout, headers=headers)
    except (OSError, TimeoutError, http.client.HTTPException):
        return {"status": "unreachable", "origin": origin, "model_ids": set()}
    if status == 401:
        return {"status": "auth_required", "origin": origin, "model_ids": set()}
    if status < 200 or status >= 300:
        return {"status": f"http_{status}", "origin": origin, "model_ids": set()}
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {"status": "invalid_json", "origin": origin, "model_ids": set()}
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {"status": "invalid_payload", "origin": origin, "model_ids": set()}
    model_ids = {
        str(row.get("id") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    return {"status": "ready", "origin": origin, "model_ids": model_ids}


def _model_row(name, endpoint, model, enabled, inventory_cache, timeout):
    if not enabled:
        return {
            "name": name,
            "status": "disabled",
            "detail": "Score actions are disabled for this dashboard process.",
            "action": "Restart with --enable-score-actions when scoring is needed.",
        }
    configured_model = str(model or "").strip()
    if not configured_model:
        return {
            "name": name,
            "status": "action_needed",
            "detail": "No exact local model id is configured.",
            "action": "Restart with the matching --judge-model or --reviewer-model value.",
        }
    try:
        target, _origin = _local_endpoint(endpoint, "models")
        cache_key = urlunparse(target)
        if cache_key not in inventory_cache:
            inventory_cache[cache_key] = _model_inventory(endpoint, timeout)
        inventory = inventory_cache[cache_key]
    except ValueError as exc:
        return {
            "name": name,
            "status": "action_needed",
            "detail": str(exc),
            "action": "Use a loopback OpenAI-compatible endpoint without credentials in the URL.",
        }
    inventory_status = inventory["status"]
    if inventory_status == "ready" and configured_model in inventory["model_ids"]:
        return {
            "name": name,
            "status": "ready",
            "detail": f"{configured_model} is available at {inventory['origin']}.",
            "action": "No action required.",
        }
    if inventory_status == "ready":
        return {
            "name": name,
            "status": "action_needed",
            "detail": f"Configured model '{configured_model}' is not in local inventory.",
            "action": "Load the model in LM Studio or choose an id returned by /v1/models.",
        }
    details = {
        "auth_required": "Local model inventory requires LM_API_TOKEN.",
        "unreachable": "Local model server is not reachable.",
        "invalid_json": "Local model inventory returned invalid JSON.",
        "invalid_payload": "Local model inventory returned an unexpected payload.",
    }
    return {
        "name": name,
        "status": "action_needed",
        "detail": details.get(inventory_status, "Local model inventory check failed."),
        "action": "Start the local model server, then verify its /v1/models response.",
    }


def _qdrant_row(qdrant_url, timeout):
    try:
        target, origin = _local_endpoint(qdrant_url, "readyz")
    except ValueError as exc:
        return {
            "name": "Qdrant",
            "status": "action_needed",
            "detail": str(exc),
            "action": "Set LOCAL_AI_LAB_QDRANT_URL to a loopback endpoint.",
        }
    try:
        status, _body = _get(target, timeout)
    except (OSError, TimeoutError, http.client.HTTPException):
        return {
            "name": "Qdrant",
            "status": "action_needed",
            "detail": f"Qdrant is not reachable at {origin}.",
            "action": "Run docker compose up -d qdrant.",
        }
    if 200 <= status < 300:
        return {
            "name": "Qdrant",
            "status": "ready",
            "detail": f"Ready at {origin}.",
            "action": "No action required.",
        }
    return {
        "name": "Qdrant",
        "status": "action_needed",
        "detail": f"Qdrant readiness returned HTTP {status}.",
        "action": "Inspect docker compose ps and the Qdrant container health check.",
    }


def _command_row(name, command, command_finder):
    if command_finder(command):
        return {
            "name": name,
            "status": "ready",
            "detail": f"{command} is available on PATH.",
            "action": "No action required.",
        }
    return {
        "name": name,
        "status": "optional",
        "detail": f"{command} is not available on PATH.",
        "action": "Install it only when that runtime lane is needed.",
    }


def runtime_health_snapshot(
    *,
    enable_score_actions,
    judge_endpoint,
    judge_model,
    reviewer_endpoint,
    reviewer_model,
    qdrant_url=None,
    timeout=0.75,
    command_finder=shutil.which,
):
    inventory_cache = {}
    rows = [
        _model_row(
            "Primary judge",
            judge_endpoint,
            judge_model,
            enable_score_actions,
            inventory_cache,
            timeout,
        ),
        _model_row(
            "Independent reviewer",
            reviewer_endpoint,
            reviewer_model,
            enable_score_actions,
            inventory_cache,
            timeout,
        ),
        _qdrant_row(
            qdrant_url
            or os.environ.get("LOCAL_AI_LAB_QDRANT_URL", "http://127.0.0.1:6333"),
            timeout,
        ),
        _command_row("LM Studio CLI", "lms", command_finder),
        _command_row("Ollama CLI", "ollama", command_finder),
    ]
    action_needed = sum(row["status"] == "action_needed" for row in rows)
    overall = "action_needed" if action_needed else "ready"
    return {
        "overall": overall,
        "action_needed": action_needed,
        "rows": rows,
        "captured_at": datetime.now(UTC).isoformat(),
    }


__all__ = ("runtime_health_snapshot",)
