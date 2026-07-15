"""Installed-model inventory page and gated removal actions."""

# ruff: noqa: E501,F403,F405,I001
from __future__ import annotations

import hashlib
import csv
import importlib.util
import json
import shutil
import sys
from contextlib import suppress
from datetime import datetime
from pathlib import Path

from .. import db, fit, removal
from ..components import *
from ..filters import *
from ..layout import _layout
from ..sorting import _sort_rows, _sortable_headers
from .storage import _storage_decision_table

LMSTUDIO_MODELS_ROOT = Path.home() / ".lmstudio" / "models"
LMSTUDIO_BUNDLED_MODELS_ROOT = Path.home() / ".lmstudio" / ".internal" / "bundled-models"
OLLAMA_MODELS_ROOT = Path.home() / ".ollama" / "models"
HF_HUB_CACHE_ROOT = Path.home() / ".cache" / "huggingface" / "hub"
LMSTUDIO_WEIGHT_SUFFIXES = (".gguf", ".safetensors", ".bin", ".mlx", ".npz")
INVENTORY_DECISIONS_ANCHOR = "inventory-decisions"
INVENTORY_DECISION_FILTERS = {
    "all": {
        "label": "Decisions",
        "href": f"/inventory#{INVENTORY_DECISIONS_ANCHOR}",
        "icon": "ti-checkup-list",
    },
    "keep": {
        "label": "Keep installed",
        "href": f"/inventory?keep=yes#{INVENTORY_DECISIONS_ANCHOR}",
        "icon": "ti-circle-check",
    },
    "watchlist": {
        "label": "Watchlist",
        "href": f"/inventory?decision=watchlist#{INVENTORY_DECISIONS_ANCHOR}",
        "icon": "ti-eye",
    },
    "retest": {
        "label": "Retest",
        "href": f"/inventory?decision=retest#{INVENTORY_DECISIONS_ANCHOR}",
        "icon": "ti-player-play",
    },
    "skip": {
        "label": "Skip",
        "href": f"/inventory?decision=skip#{INVENTORY_DECISIONS_ANCHOR}",
        "icon": "ti-circle",
    },
}
INVENTORY_SORT_HEADERS = {
    "Runtime": "runtime",
    "Model id": "model_id",
    "Display name": "display_name",
    "Status": "status",
    "Paths": "paths",
    "Registry match": "registry_match",
    "Tested": "tested",
    "Action": "action",
}
CANDIDATE_FIELDNAMES = (
    "candidate_id",
    "model_name",
    "model_family",
    "provider_or_org",
    "status",
    "format_or_runtime",
    "source_packet_path",
    "report_path",
    "benchmark_run_id",
    "model_page_url",
    "github_url",
    "lm_studio_url",
    "ollama_url",
    "runtime_availability",
    "local_runner",
    "local_model_id",
    "default_endpoint",
    "why_interesting",
    "risk_notes",
    "proposed_eval",
    "security_review_status",
    "download_approval",
    "license_review_status",
    "provenance_status",
    "security_notes",
    "isolation_notes",
    "security_review_path",
)

def _inventory_model_key(model):
    payload = "|".join(
        str(model.get(field) or "")
        for field in ("runtime", "model_id", "source_path", "local_path")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _inventory_model_removable(model):
    return not _inventory_removal_blocked_reason(model)


def _inventory_removal_blocked_reason(model, lmstudio_root=None, hf_cache_root=None):
    lmstudio_root = LMSTUDIO_MODELS_ROOT if lmstudio_root is None else lmstudio_root
    hf_cache_root = HF_HUB_CACHE_ROOT if hf_cache_root is None else hf_cache_root
    runtime = model.get("runtime")
    if model.get("removal_blocked_reason"):
        return str(model["removal_blocked_reason"])
    try:
        if runtime == "LM Studio":
            removal._resolve_lmstudio_folder(model, lmstudio_root)
            return ""
        if runtime == "Ollama":
            removal._validated_ollama_model_id(model.get("model_id"))
            return ""
        if runtime == "MLX-LM":
            raw_path = model.get("local_path") or model.get("model_id")
            removal._hf_snapshot_target(raw_path, hf_cache_root)
            return ""
    except removal.RemovalError as exc:
        if runtime == "LM Studio" and str(model.get("model_type") or "").lower() == "embedding":
            return "Embedding row — remove via LM Studio."
        return str(exc)
    label = str(runtime or "Unknown runtime")
    return f"{label} removal is not supported by this dashboard."


def _remove_model_control(model, enable_delete_actions=False, action_token=""):
    reason = _inventory_removal_blocked_reason(model)
    if reason:
        return f'<span class="empty">{_text(reason)}</span>'
    if not enable_delete_actions:
        return """
        <div class="cell-stack">
          <button type="button" class="danger-secondary" disabled>Remove</button>
          <div class="empty">Restart with <code>--enable-delete-actions</code></div>
        </div>
        """
    return f"""
    <form class="inline-form" method="post" action="/actions/delete-model">
      <input type="hidden" name="token" value="{_text(action_token)}">
      <input type="hidden" name="remove_key" value="{_text(_inventory_model_key(model))}">
      <button class="danger-secondary" type="submit">Remove</button>
    </form>
    """


def _inventory_action_cell(
    model,
    candidate,
    enable_run_tests=False,
    enable_delete_actions=False,
    action_token="",
):
    actions = []
    if _inventory_run_allowed(model, candidate):
        actions.append(_run_test_control(candidate, enable_run_tests, action_token))
    elif model.get("status") == "filesystem_only":
        actions.append('<span class="empty">Filesystem-only; index/load in LM Studio first</span>')
    elif str(model.get("model_type") or "").lower() == "embedding":
        actions.append('<span class="empty">Embedding model; LLM benchmark not applicable</span>')
    elif candidate:
        actions.append('<span class="empty">Registered; no runnable local benchmark runner</span>')
    else:
        actions.append('<span class="empty">Register exact local model id first</span>')
    actions.append(_remove_model_control(model, enable_delete_actions, action_token))
    return '<div class="cell-stack">{}</div>'.format("".join(actions))


def _run_note_value(notes, key):
    prefix = f"{key}="
    for part in str(notes or "").split("|"):
        part = part.strip()
        if part.startswith(prefix):
            return part.split("=", 1)[1].strip()
    return ""


def _normalized_model_name(value):
    return "".join(char for char in str(value or "").casefold() if char.isalnum())


def _normalized_local_model_id(value):
    return str(value or "").strip().casefold()


def _inventory_run_record(row):
    return {
        "dashboard_model_id": row["model_id"],
        "date_tested": row["date_tested"] or "",
        "benchmark_run_id": _run_note_value(row["run_notes"], "benchmark_run_id"),
        "score_status": row["score_status"] or "",
        "final_label": row["final_label"] or "",
        "params_b": row["params_b"],
        "quantization": row["quantization"],
        "tokens_per_sec": row["tokens_per_sec"],
    }


def _inventory_run_history(conn):
    history = {}
    if conn is None:
        return history

    rows = _real_rows(db.list_runs(conn))
    latest_by_model = {}
    owners_by_key = {}

    def register_owner(key, dashboard_model_id):
        if not key:
            return
        owners_by_key.setdefault(key, set()).add(dashboard_model_id)

    for row in rows:
        dashboard_model_id = row["model_id"]
        latest_by_model.setdefault(dashboard_model_id, _inventory_run_record(row))

        local_model_id = _normalized_local_model_id(
            _run_note_value(row["run_notes"], "model_id")
        )
        if local_model_id:
            register_owner(f"local:{local_model_id}", dashboard_model_id)

        candidate_id = _run_note_value(row["run_notes"], "candidate_id")
        if candidate_id:
            register_owner(candidate_id, dashboard_model_id)
            register_owner(f"candidate:{candidate_id}", dashboard_model_id)

        model_name = str(row["model_name"] or "").strip()
        normalized_name = _normalized_model_name(model_name)
        if normalized_name:
            register_owner(f"name:{normalized_name}", dashboard_model_id)
        if model_name:
            register_owner(f"model:{model_name.casefold()}", dashboard_model_id)

    for key, owners in owners_by_key.items():
        history[key] = latest_by_model[next(iter(owners))] if len(owners) == 1 else None
    return history


def _inventory_matching_run(model, candidate, run_history=None):
    history = run_history or {}
    local_model_ids = []
    for value in (_inventory_exact_model_id(model), model.get("model_id")):
        normalized = _normalized_local_model_id(value)
        if normalized and normalized not in local_model_ids:
            local_model_ids.append(normalized)

    for local_model_id in local_model_ids:
        run = history.get(f"local:{local_model_id}")
        if run:
            return run

    candidate_id = str((candidate or {}).get("candidate_id") or "").strip()
    candidate_local_model_id = _normalized_local_model_id(
        (candidate or {}).get("local_model_id")
    )
    if (
        candidate_id
        and candidate_local_model_id
        and candidate_local_model_id in local_model_ids
    ):
        run = history.get(f"candidate:{candidate_id}") or history.get(candidate_id)
        if run:
            return run

    if candidate_id:
        run = history.get(f"candidate:{candidate_id}") or history.get(candidate_id)
        if run:
            return run

    normalized_names = []
    for value in (
        model.get("display_name"),
        (candidate or {}).get("model_name"),
        model.get("model_id") if not model.get("display_name") else "",
    ):
        normalized = _normalized_model_name(value)
        if normalized and normalized not in normalized_names:
            normalized_names.append(normalized)

    matches = []
    for normalized_name in normalized_names:
        key = f"name:{normalized_name}"
        if key in history and history[key] is None:
            return None
        run = history.get(key)
        if run:
            matches.append(run)
    model_ids = {run.get("dashboard_model_id") for run in matches}
    if len(model_ids) == 1:
        return matches[0]
    return None


def _inventory_test_status_cell(model, candidate, run_history=None):
    if not candidate:
        return '<span class="empty">Register first</span>'
    if str(model.get("model_type") or "").lower() == "embedding":
        return """
        <div class="cell-stack">
          <span class="pill">not applicable</span>
          <span class="empty">Embedding model; no LLM run expected</span>
        </div>
        """
    if not _candidate_run_ready(candidate):
        return """
        <div class="cell-stack">
          <span class="pill">not runnable</span>
          <span class="empty">No local benchmark runner</span>
        </div>
        """
    run = (run_history or {}).get(candidate.get("candidate_id", ""))
    if not run:
        return """
        <div class="cell-stack">
          <span class="pill">not tested</span>
          <span class="empty">No dashboard run yet</span>
        </div>
        """

    details = []
    if run.get("date_tested"):
        details.append(f'<span class="empty">Last: {_text(run["date_tested"])}</span>')
    if run.get("benchmark_run_id"):
        details.append(_artifact_link(run["benchmark_run_id"]))
    if run.get("score_status"):
        details.append(f'<span class="empty">Score: {_text(run["score_status"])}</span>')
    return '<div class="cell-stack"><span class="pill">tested</span>{}</div>'.format(
        "".join(details)
    )


def _inventory_test_sort_value(entry, run_history=None):
    model = entry["model"]
    candidate = entry.get("candidate")
    if not candidate:
        return "register first"
    if str(model.get("model_type") or "").lower() == "embedding":
        return "not applicable"
    if not _candidate_run_ready(candidate):
        return "not runnable"
    return (
        "tested"
        if (run_history or {}).get(candidate.get("candidate_id", ""))
        else "not tested"
    )


def _inventory_sort_columns(run_history=None):
    return {
        "runtime": (lambda entry: entry["model"].get("runtime"), "text"),
        "model_id": (lambda entry: entry["model"].get("model_id"), "text"),
        "display_name": (lambda entry: entry["model"].get("display_name"), "text"),
        "status": (lambda entry: entry["model"].get("status"), "text"),
        "paths": (
            lambda entry: entry["model"].get("local_path")
            or entry["model"].get("source_path"),
            "text",
        ),
        "registry_match": (lambda entry: entry.get("match_state"), "text"),
        "tested": (
            lambda entry: _inventory_test_sort_value(entry, run_history),
            "text",
        ),
        "action": (
            lambda entry: "run"
            if _inventory_run_allowed(entry["model"], entry.get("candidate"))
            else _inventory_removal_blocked_reason(entry["model"]),
            "text",
        ),
    }


def _lmstudio_cli_path():
    bundled = Path.home() / ".lmstudio" / "bin" / "lms"
    if bundled.exists() and bundled.is_file():
        return str(bundled)
    return shutil.which("lms")


def _collect_json_objects(value):
    objects = []
    if isinstance(value, dict):
        objects.append(value)
        for item in value.values():
            objects.extend(_collect_json_objects(item))
    elif isinstance(value, list):
        for item in value:
            objects.extend(_collect_json_objects(item))
    return objects


def _first_value(row, fields):
    for field in fields:
        value = row.get(field)
        if value not in (None, ""):
            return str(value)
    return ""


def _looks_like_lmstudio_model(row):
    model_keys = (
        "modelKey",
        "identifier",
        "indexedModelIdentifier",
        "model_id",
        "modelId",
    )
    if any(row.get(field) for field in model_keys):
        return True
    return bool(row.get("type") in ("llm", "embedding") and row.get("path"))


def _lmstudio_identity_values(row):
    values = []
    for field in (
        "modelKey",
        "identifier",
        "indexedModelIdentifier",
        "model_id",
        "modelId",
        "id",
        "path",
        "name",
        "displayName",
    ):
        value = row.get(field)
        if value not in (None, ""):
            values.append(str(value))
    return values


def _local_path_from_source(root, source_path):
    if not source_path:
        return ""
    path = Path(str(source_path)).expanduser()
    if path.is_absolute():
        return str(path)
    return str(Path(root).expanduser() / path)


def _lmstudio_local_path_and_removal_reason(
    source_path,
    root=None,
    bundled_root=None,
):
    root = LMSTUDIO_MODELS_ROOT if root is None else root
    bundled_root = LMSTUDIO_BUNDLED_MODELS_ROOT if bundled_root is None else bundled_root
    local_path = _local_path_from_source(root, source_path)
    if not source_path:
        return local_path, ""
    path = Path(str(source_path)).expanduser()
    if path.is_absolute():
        return str(path), ""

    bundled_path = Path(bundled_root).expanduser() / path
    if bundled_path.exists():
        return str(bundled_path), "Bundled LM Studio internal model; remove in LM Studio if supported."
    return local_path, ""


def _ollama_manifest_path(model_id, root=OLLAMA_MODELS_ROOT):
    if not model_id:
        return ""
    name, _, tag = model_id.partition(":")
    tag = tag or "latest"
    parts = [part for part in name.split("/") if part]
    if len(parts) == 1:
        manifest_parts = ["registry.ollama.ai", "library", parts[0], tag]
    elif len(parts) == 2:
        manifest_parts = ["registry.ollama.ai", parts[0], parts[1], tag]
    else:
        manifest_parts = [*parts, tag]
    return str(Path(root).expanduser() / "manifests" / Path(*manifest_parts))


def _parse_lmstudio_inventory(ls_stdout, ps_stdout="", root=LMSTUDIO_MODELS_ROOT):
    loaded_ids = set()
    try:
        ps_data = json.loads(ps_stdout) if ps_stdout.strip() else []
    except json.JSONDecodeError:
        ps_data = []
    for row in _collect_json_objects(ps_data):
        if not _looks_like_lmstudio_model(row):
            continue
        for value in _lmstudio_identity_values(row):
            loaded_ids.add(value.lower())

    try:
        data = json.loads(ls_stdout) if ls_stdout.strip() else []
    except json.JSONDecodeError:
        return []
    seen = set()
    models = []
    for row in _collect_json_objects(data):
        if not _looks_like_lmstudio_model(row):
            continue
        model_id = _first_value(
            row,
            (
                "modelKey",
                "identifier",
                "indexedModelIdentifier",
                "model_id",
                "modelId",
                "id",
                "path",
                "name",
                "displayName",
            ),
        )
        display_name = _first_value(
            row,
            (
                "displayName",
                "display_name",
                "modelName",
                "model_name",
                "name",
                "modelKey",
                "identifier",
                "id",
            ),
        )
        if not model_id or model_id.lower() in seen:
            continue
        seen.add(model_id.lower())
        path_id = str(row.get("path") or "").lower()
        identities = {value.lower() for value in _lmstudio_identity_values(row)}
        status = (
            "loaded"
            if identities & loaded_ids or (path_id and path_id in loaded_ids)
            else "indexed"
        )
        source_path = row.get("path") or ""
        local_path, removal_blocked_reason = _lmstudio_local_path_and_removal_reason(
            source_path,
            root=root,
        )
        models.append(
            {
                "runtime": "LM Studio",
                "model_id": model_id,
                "indexed_model_id": _first_value(
                    row,
                    ("modelId", "model_id", "indexedModelIdentifier", "identifier"),
                ),
                "publisher": _first_value(
                    row,
                    ("publisher", "provider", "organization", "owner"),
                ),
                "display_name": display_name or model_id,
                "status": status,
                "source_path": source_path,
                "local_path": local_path,
                "model_type": row.get("type") or row.get("modelType") or "",
                "removal_blocked_reason": removal_blocked_reason,
            }
        )
    return models


def _read_candidate_rows(path):
    registry_path = Path(path)
    if not registry_path.exists():
        return list(CANDIDATE_FIELDNAMES), []
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or CANDIDATE_FIELDNAMES)
        rows = [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]
    return fieldnames, rows


def _candidate_matches_inventory_without_exact_id(row, model):
    if row.get("local_model_id"):
        return False
    values = {
        _inventory_exact_model_id(model).strip().lower(),
        str(model.get("model_id") or "").strip().lower(),
        str(model.get("display_name") or "").strip().lower(),
    }
    if row.get("model_name", "").strip().lower() in values:
        return True
    source_path = str(model.get("source_path") or "").strip().lower()
    if not source_path:
        return False
    return (
        row.get("runtime_availability", "").strip().lower() == source_path
        or row.get("model_page_url", "").strip().lower().rstrip("/").endswith(source_path)
    )


def _inventory_model_auto_registerable(model):
    if not model.get("model_id"):
        return False
    runtime = model.get("runtime")
    if runtime == "LM Studio":
        if str(model.get("model_type") or "").lower() == "embedding":
            return True
        return not model.get("removal_blocked_reason")
    return runtime in ("Ollama", "MLX-LM", "llama.cpp")


def _inventory_local_runner(model):
    if model.get("runner_hint"):
        return model["runner_hint"]
    if str(model.get("model_type") or "").lower() == "embedding":
        return ""
    if model.get("runtime") == "LM Studio" and model.get("status") in ("indexed", "loaded"):
        return "lmstudio-cli"
    if model.get("runtime") == "Ollama" and model.get("status") == "installed":
        return "ollama"
    if model.get("runtime") == "MLX-LM" and model.get("status") == "cached":
        return "mlx-lm"
    if model.get("runtime") == "llama.cpp" and model.get("status") == "installed":
        return "llama-cpp"
    return ""


def _inventory_exact_model_id(model):
    return str(model.get("exact_model_id") or model.get("model_id") or "")


def _inventory_candidate_id(model):
    identity = "{}|{}".format(model.get("runtime", ""), _inventory_exact_model_id(model))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]
    runtime = _slug(model.get("runtime", "local"))
    return "local-{}-{}-{}".format(runtime, _slug(model.get("model_id")), digest)


def _local_inventory_candidate_row(model, fieldnames, matched_row=None):
    row = {field: "" for field in fieldnames}
    if matched_row:
        row.update({field: matched_row.get(field, "") for field in fieldnames})

    runner = _inventory_local_runner(model)
    generated = matched_row is None
    if not row.get("candidate_id"):
        row["candidate_id"] = _inventory_candidate_id(model)
    if not row.get("model_name"):
        row["model_name"] = model.get("display_name") or model.get("model_id") or ""
    if not row.get("provider_or_org"):
        row["provider_or_org"] = f"local {model.get('runtime', 'runtime')} inventory"
    model_type = str(model.get("model_type") or "").lower()
    row["format_or_runtime"] = (
        model.get("format_or_runtime")
        or ("LM Studio embedding" if model_type == "embedding" else "")
        or model.get("runtime", "local")
    )
    if runner or generated or row.get("status") in ("", "watchlist", "needs_more_info"):
        row["status"] = "ready_for_eval" if runner else "needs_more_info"
    row["runtime_availability"] = (
        "Auto-detected by {} inventory refresh as {}; exact local model id recorded. "
        "No download, score, or decision implied."
    ).format(model.get("runtime", "local runtime"), model.get("status") or "detected")
    row["local_runner"] = runner
    row["local_model_id"] = _inventory_exact_model_id(model)
    row["why_interesting"] = (
        row.get("why_interesting")
        or "Detected in local runtime inventory with an exact runtime model id."
    )
    row["risk_notes"] = (
        row.get("risk_notes")
        or "Auto-generated from local inventory. License and upstream provenance still need review before a keep/share decision."
    )
    runner_label = _candidate_runner_label(row)
    row["proposed_eval"] = (
        "Do not run the local LLM benchmark; use an embedding retrieval eval lane when available."
        if model_type == "embedding"
        else f"Run evals/local-llm-benchmark/SPEC.md through {runner_label} after explicit local-run approval."
        if runner
        else "Install or enable the matching local runner before running the benchmark."
    )
    row["security_review_status"] = "local_inventory_reviewed"
    row["download_approval"] = "not_needed_local"
    row["license_review_status"] = row.get("license_review_status") or "needs_review"
    row["provenance_status"] = "local_inventory"
    row["security_notes"] = (
        "Detected as already installed in local runtime inventory; no new download was approved or performed. "
        "Verify upstream source, license, and checksum before reinstalling or updating."
    )
    row["isolation_notes"] = (
        "Run only through the detected local runner or a loopback local endpoint; keep raw responses and evidence local."
    )
    return row


def _sync_local_inventory_candidates(
    inventory_result,
    registry_path=CANDIDATE_REGISTRY_PATH,
    local_inventory_path=LOCAL_INVENTORY_REGISTRY_PATH,
):
    fieldnames, durable_rows = _read_candidate_rows(registry_path)
    exact_ids = {
        row.get("local_model_id", "").strip().lower()
        for row in durable_rows
        if row.get("local_model_id")
    }
    generated_rows = []
    skipped = 0
    updated_existing = 0
    for model in (inventory_result or {}).get("models", []):
        if not _inventory_model_auto_registerable(model):
            skipped += 1
            continue
        model_id = _inventory_exact_model_id(model).strip().lower()
        if model_id in exact_ids:
            continue
        soft_matches = [
            row for row in durable_rows if _candidate_matches_inventory_without_exact_id(row, model)
        ]
        matched = soft_matches[0] if len(soft_matches) == 1 else None
        if matched:
            updated_existing += 1
        generated_rows.append(_local_inventory_candidate_row(model, fieldnames, matched))

    overlay_path = Path(local_inventory_path)
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    with overlay_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(generated_rows)
    return {
        "path": str(overlay_path),
        "registered": len(generated_rows),
        "updated_existing": updated_existing,
        "skipped": skipped,
    }


def _primary_lmstudio_weight_file(model_dir):
    for item in sorted(Path(model_dir).rglob("*"), key=lambda path: str(path).lower()):
        if item.name.startswith(".") or not item.is_file():
            continue
        if item.suffix.lower() in LMSTUDIO_WEIGHT_SUFFIXES:
            return item
    return None


def _normalized_lmstudio_indexed_paths(indexed_paths, root=LMSTUDIO_MODELS_ROOT):
    root = Path(root).expanduser()
    values = set()
    for raw_path in indexed_paths:
        raw = str(raw_path or "").strip()
        if not raw:
            continue
        candidates = [raw]
        expanded = Path(raw).expanduser()
        if expanded.is_absolute():
            with suppress(ValueError):
                candidates.append(expanded.relative_to(root).as_posix())

        for candidate in candidates:
            clean = candidate.replace("\\", "/").strip("/")
            if not clean:
                continue
            values.add(clean.lower())
            parts = [part for part in clean.split("/") if part]
            parent_parts = parts[:-1]
            while len(parent_parts) >= 2:
                values.add("/".join(parent_parts).lower())
                parent_parts = parent_parts[:-1]
    return values


def _scan_lmstudio_filesystem_models(
    root=LMSTUDIO_MODELS_ROOT,
    indexed_paths=(),
    llama_cpp_available=False,
):
    root = Path(root)
    if not root.exists():
        return []
    indexed = _normalized_lmstudio_indexed_paths(indexed_paths, root)
    models = []
    for publisher_dir in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not publisher_dir.is_dir() or publisher_dir.name.startswith("."):
            continue
        for model_dir in sorted(publisher_dir.iterdir(), key=lambda item: item.name.lower()):
            if not model_dir.is_dir() or model_dir.name.startswith("."):
                continue
            weight_file = _primary_lmstudio_weight_file(model_dir)
            if not weight_file:
                continue
            relative_path = f"{publisher_dir.name}/{model_dir.name}"
            if relative_path.lower() in indexed:
                continue
            model = {
                "runtime": "LM Studio",
                "model_id": relative_path,
                "display_name": model_dir.name,
                "status": "filesystem_only",
                "source_path": relative_path,
                "local_path": str(model_dir),
            }
            if llama_cpp_available and weight_file.suffix.lower() == ".gguf":
                model["runner_hint"] = "llama-cpp"
                model["exact_model_id"] = str(weight_file)
                model["format_or_runtime"] = "GGUF through llama.cpp"
            models.append(model)
    return models


def _has_lmstudio_weight_file(model_dir):
    return _primary_lmstudio_weight_file(model_dir) is not None


def _hf_cache_repo_id(cache_dir):
    name = Path(cache_dir).name
    if not name.startswith("models--"):
        return ""
    encoded = name.removeprefix("models--")
    owner, separator, repo = encoded.partition("--")
    if not separator or not owner or not repo:
        return ""
    return f"{owner}/{repo}"


def _looks_like_mlx_lm_repo(repo_id):
    lower = str(repo_id or "").lower()
    return lower.startswith("mlx-community/") or "-mlx" in lower or "/mlx" in lower


def _snapshot_has_mlx_weights(snapshot_dir):
    snapshot = Path(snapshot_dir)
    if not (snapshot / "config.json").exists():
        return False
    for item in snapshot.iterdir():
        if item.is_file() and item.suffix.lower() in (".safetensors", ".npz"):
            return True
    return False


def _scan_mlx_lm_cached_models(root=HF_HUB_CACHE_ROOT):
    root = Path(root).expanduser()
    if not root.exists():
        return []
    models = []
    for cache_dir in sorted(root.glob("models--*--*"), key=lambda path: path.name.lower()):
        repo_id = _hf_cache_repo_id(cache_dir)
        if not repo_id or not _looks_like_mlx_lm_repo(repo_id):
            continue
        snapshots_dir = cache_dir / "snapshots"
        if not snapshots_dir.exists():
            continue
        snapshots = [
            item
            for item in snapshots_dir.iterdir()
            if item.is_dir() and _snapshot_has_mlx_weights(item)
        ]
        if not snapshots:
            continue
        snapshot = max(snapshots, key=lambda item: item.stat().st_mtime)
        models.append(
            {
                "runtime": "MLX-LM",
                "model_id": str(snapshot),
                "display_name": repo_id,
                "status": "cached",
                "source_path": repo_id,
                "local_path": str(snapshot),
                "model_type": "llm",
                "format_or_runtime": "MLX-LM local cache",
            }
        )
    return models


def _python_module_available(module_name):
    return importlib.util.find_spec(module_name) is not None


def _runtime_check(name, command, available, detail):
    return {
        "name": name,
        "command": command,
        "status": "ok" if available else "unavailable",
        "exit_code": "",
        "stdout": detail if available else "",
        "stderr": "" if available else detail,
    }


def _parse_ollama_inventory(stdout):
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines or not lines[0].lower().startswith("name"):
        return []
    models = []
    for line in lines[1:]:
        parts = line.split()
        model_id = parts[0] if parts else ""
        if model_id:
            models.append(
                {
                    "runtime": "Ollama",
                    "model_id": model_id,
                    "display_name": model_id,
                    "status": "installed",
                    "source_path": "",
                    "local_path": _ollama_manifest_path(model_id),
                    "model_type": "llm",
                    "format_or_runtime": "Ollama",
                }
            )
    return models


def _refresh_inventory(timeout=5):
    checks = []
    models = []
    llama_cli_path = shutil.which("llama-cli")
    mlx_lm_available = _python_module_available("mlx_lm")
    lms_path = _lmstudio_cli_path()
    if lms_path:
        lm_ls = _command_result("LM Studio models", [lms_path, "ls", "--json"], timeout)
        lm_ps = _command_result("LM Studio loaded models", [lms_path, "ps", "--json"], timeout)
        checks.extend([lm_ls, lm_ps])
        lmstudio_models = []
        if lm_ls["status"] == "ok":
            lmstudio_models = _parse_lmstudio_inventory(lm_ls["stdout"], lm_ps["stdout"])
            models.extend(lmstudio_models)
        models.extend(
            _scan_lmstudio_filesystem_models(
                indexed_paths=[model.get("source_path") for model in lmstudio_models],
                llama_cpp_available=bool(llama_cli_path),
            )
        )
    else:
        checks.append(
            {
                "name": "LM Studio models",
                "command": "lms ls --json",
                "status": "unavailable",
                "exit_code": "",
                "stdout": "",
                "stderr": "LM Studio CLI not found at ~/.lmstudio/bin/lms or on PATH.",
            }
        )

    ollama_path = shutil.which("ollama")
    if ollama_path:
        ollama = _command_result("Ollama models", [ollama_path, "list"], timeout)
        checks.append(ollama)
        if ollama["status"] == "ok":
            models.extend(_parse_ollama_inventory(ollama["stdout"]))
    else:
        checks.append(
            {
                "name": "Ollama models",
                "command": "ollama list",
                "status": "unavailable",
                "exit_code": "",
                "stdout": "",
                "stderr": "Ollama CLI not found on PATH.",
            }
        )
    checks.append(
        _runtime_check(
            "MLX-LM module",
            f"{sys.executable} -m mlx_lm generate",
            mlx_lm_available,
            "mlx_lm importable in the dashboard Python environment."
            if mlx_lm_available
            else "mlx_lm is not importable in the dashboard Python environment.",
        )
    )
    if mlx_lm_available:
        models.extend(_scan_mlx_lm_cached_models())
    checks.append(
        _runtime_check(
            "llama.cpp CLI",
            "llama-cli",
            bool(llama_cli_path),
            llama_cli_path or "llama-cli not found on PATH.",
        )
    )
    return {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "models": models,
        "checks": checks,
    }


def _preferred_exact_inventory_match(matches):
    selectors = (
        lambda row: row.get("candidate_id", "").startswith("local-")
        and row.get("provenance_status", "").lower() == "local_inventory",
        lambda row: row.get("candidate_id", "").startswith("local-"),
        lambda row: row.get("provenance_status", "").lower() == "local_inventory",
        lambda row: bool(row.get("local_runner"))
        and row.get("download_approval", "").lower() == "not_needed_local",
    )
    for selector in selectors:
        preferred = [row for row in matches if selector(row)]
        if len(preferred) == 1:
            return preferred[0]
    return None


def _match_inventory_model(model, candidates):
    model_ids = {
        value.strip().lower()
        for value in (str(model.get("model_id", "")), _inventory_exact_model_id(model))
        if value
    }
    exact_matches = [
        row for row in candidates if row.get("local_model_id", "").strip().lower() in model_ids
    ]
    if len(exact_matches) == 1:
        return "registered", exact_matches[0]
    if len(exact_matches) > 1:
        preferred = _preferred_exact_inventory_match(exact_matches)
        if preferred:
            return "registered", preferred
        return "ambiguous", None

    source_path = model.get("source_path", "").lower()
    matches = [
        row
        for row in candidates
        if row.get("model_name", "").lower() in model_ids
        or (
            source_path
            and (
                row.get("runtime_availability", "").lower() == source_path
                or row.get("model_page_url", "").lower().rstrip("/").endswith(source_path)
            )
        )
    ]
    if len(matches) == 1:
        return "registered", matches[0]
    if len(matches) > 1:
        return "ambiguous", None
    return "unregistered", None


def _inventory_run_allowed(model, candidate):
    if not candidate or not _candidate_run_ready(candidate):
        return False
    if model.get("runtime") == "LM Studio":
        if candidate.get("local_runner") == "llama-cpp":
            return bool(candidate.get("local_model_id"))
        return model.get("status") in ("indexed", "loaded")
    return model.get("status") != "filesystem_only"


def _inventory_run_all_blocked_reason(model, match_state, candidate):
    if str(model.get("model_type") or "").lower() == "embedding":
        return "embedding model — LLM benchmark not applicable"
    if model.get("status") == "filesystem_only":
        return "filesystem-only — index/load in the local runtime first"
    if candidate is None:
        if match_state == "ambiguous":
            return "ambiguous registry match"
        return "no registered candidate with an exact local id and runner"

    model_id = str(candidate.get("local_model_id") or "").strip()
    runner = str(candidate.get("local_runner") or "").strip()
    if not candidate.get("candidate_id"):
        return "missing candidate id"
    if not model_id:
        return "missing exact local model id"
    if not runner:
        return "missing local runner"
    if runner not in SUPPORTED_LOCAL_RUNNERS:
        return f"unsupported local runner: {runner}"
    if runner == "openai-compatible" and not candidate.get("default_endpoint"):
        return "missing loopback endpoint for openai-compatible runner"
    if not _inventory_run_allowed(model, candidate):
        return "local runtime status is not runnable"
    return ""


def _inventory_run_all_plan(
    inventory_result,
    registry_path=CANDIDATE_REGISTRY_PATH,
    local_inventory_path=None,
    eval_results_dir=EVAL_RESULTS_DIR,
):
    candidates = _load_radar_candidates(registry_path, local_inventory_path)
    runnable = []
    skipped = []
    used_run_ids = set()
    seen_targets = set()
    for model in (inventory_result or {}).get("models", []):
        match_state, candidate = _match_inventory_model(model, candidates)
        reason = _inventory_run_all_blocked_reason(model, match_state, candidate)
        model_id = str((candidate or {}).get("local_model_id") or "").strip()
        runner = str((candidate or {}).get("local_runner") or "").strip()
        if not reason:
            target = (runner, model_id)
            if target in seen_targets:
                reason = "duplicate exact local id and runner"
            else:
                seen_targets.add(target)
        if reason:
            skipped.append(
                {
                    "model_name": model.get("display_name") or model.get("model_id") or "",
                    "model_id": model_id or _inventory_exact_model_id(model),
                    "runner": runner,
                    "reason": reason,
                }
            )
            continue

        run_id = _next_dashboard_run_id(candidate, eval_results_dir)
        if run_id in used_run_ids:
            base = run_id
            suffix = 2
            while run_id in used_run_ids or (Path(eval_results_dir) / run_id).exists():
                run_id = f"{base}-{suffix}"
                suffix += 1
        used_run_ids.add(run_id)
        runnable.append(
            {
                "candidate": candidate,
                "candidate_id": candidate.get("candidate_id", ""),
                "model_name": candidate.get("model_name")
                or model.get("display_name")
                or model.get("model_id")
                or "",
                "model_id": model_id,
                "runner": runner,
                "run_id": run_id,
            }
        )
    return {"runnable": runnable, "skipped": skipped}


def _run_all_fingerprint(plan):
    fields = ("candidate_id", "model_id", "runner", "run_id")
    approval_scope = {
        "runnable": [
            {field: str(item.get(field) or "") for field in fields}
            for item in plan.get("runnable", [])
        ],
        "skipped": [
            {
                field: str(item.get(field) or "")
                for field in ("model_name", "model_id", "runner", "reason")
            }
            for item in plan.get("skipped", [])
        ],
    }
    payload = json.dumps(approval_scope, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _run_all_control(enable_run_tests=False):
    if not enable_run_tests:
        return ""
    return """
    <form class="inline-form" method="get" action="/inventory/run-all">
      <button type="submit">Run all runnable</button>
    </form>
    """


def _run_all_confirm_page(plan, action_token=""):
    runnable_rows = [
        [
            f'<code>{_text(item.get("candidate_id") or "—")}</code>',
            _text(item.get("model_name") or "—"),
            f'<code>{_text(item.get("model_id") or "—")}</code>',
            f'<code>{_text(item.get("runner") or "—")}</code>',
            f'<code>{_text(item.get("run_id") or "—")}</code>',
        ]
        for item in plan.get("runnable", [])
    ]
    skipped_rows = [
        [
            _text(item.get("model_name") or "—"),
            f'<code>{_text(item.get("model_id") or "—")}</code>',
            f'<code>{_text(item.get("runner") or "—")}</code>',
            _text(item.get("reason") or "—"),
        ]
        for item in plan.get("skipped", [])
    ]
    confirm = ""
    if runnable_rows:
        token = _text(action_token)
        approval_scope = _text(_run_all_fingerprint(plan))
        confirm = f"""
        <form class="inline-form" method="post" action="/actions/run-all">
          <input type="hidden" name="token" value="{token}">
          <input type="hidden" name="confirm_run_all" value="yes">
          <input type="hidden" name="approval_scope" value="{approval_scope}">
          <button type="submit">Confirm and run sequentially</button>
          <a class="action-link secondary" href="/inventory">Cancel</a>
        </form>
        """
    body = """
    <section class="panel page-intro">
      <h2>Run All Preflight</h2>
      <p>Approval scope: only the exact enumerated runnable batch below.</p>
      <p class="empty">No model executes on this page. Confirmation starts one background worker, runs each model sequentially, and continues after per-model failures.</p>
      {confirm}
    </section>
    <section class="inventory-section">
      <h2>Runnable models ({runnable_count})</h2>
      {runnable_table}
    </section>
    <section class="inventory-section">
      <h2>Skipped models ({skipped_count})</h2>
      {skipped_table}
    </section>
    """.format(
        confirm=confirm,
        runnable_count=len(runnable_rows),
        skipped_count=len(skipped_rows),
        runnable_table=_table(
            ["Candidate", "Model", "Exact model id", "Runner", "Run id"],
            runnable_rows,
            empty_message="No detected model is currently runnable.",
        ),
        skipped_table=_table(
            ["Model", "Local id", "Runner", "Reason"],
            skipped_rows,
            empty_message="No detected models were skipped.",
        ),
    )
    return _layout("Run All Preflight", "/inventory", body)


def _inventory_filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "runtime": _query_value(query, "runtime"),
        "status": _query_value(query, "status"),
        "match": _query_value(query, "match"),
    }


def _matches_inventory_search(entry, search):
    if not search:
        return True
    model = entry["model"]
    candidate = entry.get("candidate")
    haystack = " ".join(
        [
            model.get("runtime", ""),
            model.get("model_id", ""),
            model.get("exact_model_id", ""),
            model.get("display_name", ""),
            model.get("status", ""),
            model.get("source_path", ""),
            model.get("local_path", ""),
            entry.get("match_state", ""),
            candidate.get("candidate_id", "") if candidate else "",
            candidate.get("model_name", "") if candidate else "",
        ]
    )
    return search.lower() in haystack.lower()


def _filter_inventory_entries(entries, filters):
    filtered = []
    for entry in entries:
        model = entry["model"]
        if filters["runtime"] and model.get("runtime") != filters["runtime"]:
            continue
        if filters["status"] and model.get("status") != filters["status"]:
            continue
        if filters["match"] and entry.get("match_state") != filters["match"]:
            continue
        if not _matches_inventory_search(entry, filters["q"]):
            continue
        filtered.append(entry)
    return filtered


def _inventory_filters(entries, filters):
    runtime_options = "".join(
        _option(runtime, runtime, filters["runtime"])
        for runtime in sorted(
            {
                entry["model"].get("runtime", "")
                for entry in entries
                if entry["model"].get("runtime")
            },
            key=lambda value: value.lower(),
        )
    )
    status_options = "".join(
        _option(status, status, filters["status"])
        for status in sorted(
            {entry["model"].get("status", "") for entry in entries if entry["model"].get("status")},
            key=lambda value: value.lower(),
        )
    )
    match_options = "".join(
        _option(match, match, filters["match"])
        for match in sorted(
            {entry.get("match_state", "") for entry in entries if entry.get("match_state")},
            key=lambda value: value.lower(),
        )
    )
    clear_link = (
        '<a class="clear-link" href="/inventory">Clear</a>' if any(filters.values()) else ""
    )
    return """
    <form class="filters" method="get" action="/inventory">
      <div class="field field-wide">
        <label for="inventory-q">Search</label>
        <input id="inventory-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="inventory-runtime">Runtime</label>
        <select id="inventory-runtime" name="runtime">
          {all_runtimes}
          {runtime_options}
        </select>
      </div>
      <div class="field">
        <label for="inventory-status">Status</label>
        <select id="inventory-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="field">
        <label for="inventory-match">Registry match</label>
        <select id="inventory-match" name="match">
          {all_matches}
          {match_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_runtimes=_option("", "All runtimes", filters["runtime"]),
        runtime_options=runtime_options,
        all_statuses=_option("", "All statuses", filters["status"]),
        status_options=status_options,
        all_matches=_option("", "All matches", filters["match"]),
        match_options=match_options,
        clear_link=clear_link,
    )


def _inventory_paths_cell(model):
    source_path = model.get("source_path") or "Not reported by runtime."
    local_path = model.get("local_path") or "Not reported by runtime."
    return f"""
    <div class="cell-stack">
      <div><strong>Runtime source</strong><br><code>{_text(source_path)}</code></div>
      <div><strong>Local file path</strong><br><code>{_text(local_path)}</code></div>
    </div>
    """


def _inventory_registration_note(result):
    registration = (result or {}).get("registration")
    if not registration:
        return ""
    path = _relative_path(registration.get("path", ""))
    return """
      <p class="empty">Auto-registered exact local IDs: {registered} local candidate rows ({updated} existing candidate overlays, {skipped} skipped). Local overlay: <code>{path}</code></p>
    """.format(
        registered=_text(registration.get("registered", 0)),
        updated=_text(registration.get("updated_existing", 0)),
        skipped=_text(registration.get("skipped", 0)),
        path=_text(path),
    )


def _decision_stats(decisions):
    keep_count = sum(1 for row in decisions if row["keep_installed"])
    watchlist_count = sum(1 for row in decisions if str(row["decision"]).lower() == "watchlist")
    retest_count = sum(1 for row in decisions if str(row["decision"]).lower() == "retest")
    skip_count = sum(1 for row in decisions if str(row["decision"]).lower() == "skip")
    return {
        "total": len(decisions),
        "keep": keep_count,
        "watchlist": watchlist_count,
        "retest": retest_count,
        "skip": skip_count,
    }


def _inventory_decision_filter(query):
    keep_filter = _query_value(query or {}, "keep").lower()
    decision_filter = _query_value(query or {}, "decision").lower()
    if keep_filter == "yes":
        return "keep"
    if decision_filter in ("watchlist", "retest", "skip"):
        return decision_filter
    return "all"


def _filter_inventory_decisions(decisions, active_filter):
    if active_filter == "keep":
        return [row for row in decisions if row["keep_installed"]]
    if active_filter in ("watchlist", "retest", "skip"):
        return [
            row
            for row in decisions
            if str(row["decision"] or "").lower() == active_filter
        ]
    return list(decisions)


def _inventory_decision_stat(filter_name, count, active_filter):
    config = INVENTORY_DECISION_FILTERS[filter_name]
    return _stat_card(
        config["label"],
        count,
        config["icon"],
        href=config["href"],
        active=filter_name == active_filter,
        link_class="decision-stat-link",
    )


def _inventory_decision_section(decisions, query=None):
    stats = _decision_stats(decisions)
    active_filter = _inventory_decision_filter(query or {})
    filtered_decisions = _filter_inventory_decisions(decisions, active_filter)
    active_label = INVENTORY_DECISION_FILTERS[active_filter]["label"]
    filter_status = ""
    if active_filter != "all":
        filter_status = (
            '<p class="decision-filter-status" role="status">'
            f"Showing filter: {_text(active_label)} "
            f"({_text(len(filtered_decisions))} of {_text(len(decisions))})."
            "</p>"
        )
    return """
    <section class="inventory-section inventory-decisions-section" id="{anchor}">
      <div class="section-heading-row">
        <div>
          <h2>Keep / Watch Decisions</h2>
          <p class="section-note">Use this log after a benchmark run to decide whether each local model should stay installed, remain on watchlist, be retested, or be skipped.</p>
          {filter_status}
        </div>
        <a class="action-link secondary clear-link" href="/inventory#{anchor}">Clear / All decisions</a>
      </div>
      <section class="grid grid-compact" aria-label="Decision filters">
        {decisions_stat}
        {keep_stat}
        {watchlist_stat}
        {retest_stat}
        {skip_stat}
      </section>
      {table}
    </section>
    """.format(
        anchor=INVENTORY_DECISIONS_ANCHOR,
        filter_status=filter_status,
        decisions_stat=_inventory_decision_stat("all", stats["total"], active_filter),
        keep_stat=_inventory_decision_stat("keep", stats["keep"], active_filter),
        watchlist_stat=_inventory_decision_stat(
            "watchlist", stats["watchlist"], active_filter
        ),
        retest_stat=_inventory_decision_stat("retest", stats["retest"], active_filter),
        skip_stat=_inventory_decision_stat("skip", stats["skip"], active_filter),
        table=_storage_decision_table(
            filtered_decisions,
            empty_message=(
                "No keep/watch decisions have been imported yet."
                if active_filter == "all"
                else "No keep/watch decisions match this filter."
            ),
            scroll_id="inventory-decisions-table-scroll",
            scroll_label="Keep/watch decisions table",
            query=query or {},
            path="/inventory",
            fragment=f"#{INVENTORY_DECISIONS_ANCHOR}",
        ),
    )


def _inventory(
    query=None,
    inventory_result=None,
    action_token="",
    enable_run_tests=False,
    enable_delete_actions=False,
    enable_refresh=True,
    registry_path=CANDIDATE_REGISTRY_PATH,
    local_inventory_path=None,
    run_history=None,
    decisions=None,
    hardware_profiles_dir=REPO_ROOT / "docs" / "lab-notes",
    current_hardware_profile=None,
    read_current_hardware=False,
):
    candidates = _load_radar_candidates(registry_path, local_inventory_path)
    decision_rows = _real_rows(decisions or [])
    result = inventory_result
    filters = _inventory_filter_values(query or {})
    check_rows = []
    model_rows = []
    entries = []
    memory_gb = _fit_memory_gb(
        hardware_profiles_dir,
        current_hardware_profile=current_hardware_profile,
        read_current_hardware=read_current_hardware,
    )
    if result:
        for check in result["checks"]:
            output = check.get("stderr") or check.get("stdout") or ""
            check_rows.append(
                [
                    _text(check["name"]),
                    _pill(check["status"]),
                    _text(check.get("exit_code")),
                    "<code>{}</code>".format(_text(check["command"])),
                    _text(output[:500]),
                ]
            )
        for model in result["models"]:
            match_state, candidate = _match_inventory_model(model, candidates)
            entries.append(
                {
                    "model": model,
                    "match_state": match_state,
                    "candidate": candidate,
                }
            )
        filtered_entries = _filter_inventory_entries(entries, filters)
        sorted_entries = _sort_rows(
            filtered_entries,
            query or {},
            _inventory_sort_columns(run_history),
        )
        for entry in sorted_entries:
            model = entry["model"]
            match_state = entry["match_state"]
            candidate = entry["candidate"]
            candidate_cell = (
                '<a href="/radar?q={id}">{id}</a>'.format(id=_text(candidate["candidate_id"]))
                if candidate
                else _pill(match_state)
            )
            run = _inventory_matching_run(model, candidate, run_history) or {}
            params_b = fit.parse_parameter_count_b(
                model.get("params_b"),
                candidate.get("params_b") if candidate else None,
                run.get("params_b"),
                model.get("display_name"),
                model.get("model_id"),
            )
            bits = fit.parse_quantization_bits(
                model.get("quantization_bits"),
                model.get("quantization"),
                candidate.get("quantization_bits") if candidate else None,
                candidate.get("quantization") if candidate else None,
                run.get("quantization"),
                model.get("format_or_runtime"),
                candidate.get("format_or_runtime") if candidate else None,
                model.get("model_id"),
                model.get("display_name"),
            )
            fit_summary = _fit_summary(
                params_b,
                bits,
                memory_gb,
                run.get("tokens_per_sec"),
            )
            model_rows.append(
                [
                    _text(model["runtime"]),
                    "<code>{}</code>".format(_text(model["model_id"])),
                    '<div class="cell-stack"><span>{}</span>{}</div>'.format(
                        _text(model["display_name"]),
                        fit_summary,
                    ),
                    _pill(model["status"]),
                    _inventory_paths_cell(model),
                    candidate_cell,
                    _inventory_test_status_cell(model, candidate, run_history),
                    _inventory_action_cell(
                        model,
                        candidate,
                        enable_run_tests=enable_run_tests,
                        enable_delete_actions=enable_delete_actions,
                        action_token=action_token,
                    ),
                ]
            )

    body = """
    <section class="panel page-intro">
      <p>What's installed locally. Run a benchmark, then keep, watchlist, retest, or skip each model.</p>
      <p class="empty">My Models reads local LM Studio, Ollama, and MLX-LM inventory on demand and keeps decisions tied to imported local benchmark evidence.</p>
    </section>
    <section class="panel inventory-refresh-panel">
      <h2>Installed Models</h2>
      <p>This page checks local runtime inventory on demand. It does not download, install, benchmark, score, or import models.</p>
      <p>LM Studio rows distinguish <code>loaded</code>, <code>indexed</code>, and <code>filesystem_only</code>. Filesystem-only folders are visible on disk but are not runnable from the dashboard until LM Studio indexes or loads them.</p>
      <p>Use <strong>Local file path</strong> to locate model folders in Finder. Remove actions are disabled unless the server is started with <code>--enable-delete-actions</code>. Confirmed LM Studio folders and MLX-LM snapshots move to macOS Trash; Ollama removal uses the exact inventory id with <code>ollama rm</code>.</p>
      <form class="inline-form" method="post" action="/actions/refresh-inventory">
        <input type="hidden" name="token" value="{token}">
        <button type="submit"{disabled}>Refresh Inventory</button>
      </form>
      {run_all_control}
      {disabled_note}
      <p class="empty">Last refresh: {checked_at}</p>
      {registration_note}
    </section>
    <section class="inventory-section">
      <h2>Detected Models{filtered_count}</h2>
      {filters}
      {models}
    </section>
    {decisions_section}
    <section class="inventory-section">
      <h2>Runtime Checks</h2>
      {checks}
    </section>
    """.format(
        token=_text(action_token),
        run_all_control=_run_all_control(enable_run_tests),
        disabled="" if enable_refresh else " disabled",
        disabled_note=(
            ""
            if enable_refresh
            else '<p class="empty">Inventory refresh is available only on a localhost or loopback dashboard bind.</p>'
        ),
        checked_at=_text(result["checked_at"] if result else "not checked yet"),
        registration_note=_inventory_registration_note(result),
        filtered_count=(
            f" ({len(_filter_inventory_entries(entries, filters))} of {len(entries)})"
            if any(filters.values())
            else ""
        ),
        filters=_inventory_filters(entries, filters),
        decisions_section=_inventory_decision_section(decision_rows, query or {}),
        models=_table(
            [
                "Runtime",
                "Model id",
                "Display name",
                "Status",
                "Paths",
                "Registry match",
                "Tested",
                "Action",
            ],
            model_rows,
            empty_message=(
                "No inventory refresh has run yet."
                if not result
                else "No detected models match these filters."
            ),
            table_class="inventory-models-table",
            scroll_controls=True,
            scroll_id="inventory-models-table-scroll",
            scroll_label="Detected models table",
            sortable_headers=_sortable_headers(
                "/inventory",
                query or {},
                INVENTORY_SORT_HEADERS,
            ),
        ),
        checks=_table(
            ["Check", "Status", "Exit", "Command", "Output"],
            check_rows,
            empty_message="No runtime checks have run yet.",
            table_class="inventory-checks-table",
            scroll_controls=True,
            scroll_id="inventory-checks-table-scroll",
            scroll_label="Runtime checks table",
        ),
    )
    return _layout("My Models", "/inventory", body)


def _format_bytes(value):
    size = float(value or 0)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{int(value or 0)} B"


def _inventory_model_by_key(inventory_result, remove_key):
    if not inventory_result:
        raise ValueError("Refresh inventory before removing a model.")
    for model in inventory_result.get("models", []):
        if _inventory_model_key(model) == remove_key:
            return model
    raise ValueError("Detected model row is no longer available; refresh inventory.")


def _removal_target_from_key(
    inventory_result,
    remove_key,
    lmstudio_root=LMSTUDIO_MODELS_ROOT,
    ollama_root=OLLAMA_MODELS_ROOT,
    hf_cache_root=HF_HUB_CACHE_ROOT,
):
    model = _inventory_model_by_key(inventory_result, remove_key)
    return removal.resolve_target(
        model,
        lmstudio_root,
        ollama_root,
        hf_cache_root=hf_cache_root,
    )


def _delete_confirm_page(target, remove_key, action_token):
    path = target.path if target.path is not None else "Not required — exact runtime id"
    root = target.root if target.root is not None else "Not applicable — no filesystem path used"
    body = f"""
    <section class="panel">
      <h2>Confirm Model Removal</h2>
      <p>This is a recoverable, local-only action. Review the exact target before continuing.</p>
      <div class="cell-stack">
        <div><strong>Runtime</strong><br>{_text(target.runtime)}</div>
        <div><strong>Model id</strong><br><code>{_text(target.model_id)}</code></div>
        <div><strong>Resolved path</strong><br><code>{_text(path)}</code></div>
        <div><strong>Contained under</strong><br><code>{_text(root)}</code></div>
        <div><strong>Size</strong><br>{_text(_format_bytes(target.size_bytes))}</div>
        <div><strong>Action</strong><br>{_text(target.action)}</div>
      </div>
      <form class="inline-form" method="post" action="/actions/delete-model" style="margin-top:16px">
        <input type="hidden" name="token" value="{_text(action_token)}">
        <input type="hidden" name="remove_key" value="{_text(remove_key)}">
        <input type="hidden" name="confirm_delete" value="yes">
        <button class="danger" type="submit">Confirm Remove</button>
        <a class="clear-link" href="/inventory">Cancel</a>
      </form>
    </section>
    """
    return _layout("Confirm Model Removal", "/inventory", body)


def _delete_result_page(result):
    status = "succeeded" if result.returncode == 0 else "failed"
    path = result.target.path if result.target.path is not None else "Not required — exact runtime id"
    body = f"""
    <section class="panel">
      <h2>Model Removal {_text(status)}</h2>
      <p><strong>Runtime:</strong> {_text(result.target.runtime)}</p>
      <p><strong>Model id:</strong> <code>{_text(result.target.model_id)}</code></p>
      <p><strong>Action:</strong> {_text(result.target.action)}</p>
      <p><strong>Resolved path:</strong> <code>{_text(path)}</code></p>
      <p><strong>Exit code:</strong> <code>{_text(result.returncode)}</code></p>
      <pre class="command">{_text(_command_lines(result.command))}</pre>
      <pre class="command">{_text(result.stdout)}{_text(result.stderr)}</pre>
      <p><a href="/inventory">Back to My Models</a></p>
    </section>
    """
    return _layout("Model Removal Result", "/inventory", body)


def _delete_model_action(
    remove_key,
    confirm_delete,
    inventory_result,
    action_token,
    timeout=60,
    lmstudio_root=LMSTUDIO_MODELS_ROOT,
    ollama_root=OLLAMA_MODELS_ROOT,
    hf_cache_root=HF_HUB_CACHE_ROOT,
):
    target = _removal_target_from_key(
        inventory_result,
        remove_key,
        lmstudio_root=lmstudio_root,
        ollama_root=ollama_root,
        hf_cache_root=hf_cache_root,
    )
    if confirm_delete != "yes":
        return _delete_confirm_page(target, remove_key, action_token), None
    result = removal.remove_target(target, timeout=timeout)
    return _delete_result_page(result), result

__all__ = ('_inventory_model_key', '_inventory_model_removable', '_inventory_removal_blocked_reason', '_remove_model_control', '_inventory_action_cell', '_lmstudio_cli_path', '_collect_json_objects', '_first_value', '_looks_like_lmstudio_model', '_lmstudio_identity_values', '_local_path_from_source', '_lmstudio_local_path_and_removal_reason', '_ollama_manifest_path', '_parse_lmstudio_inventory', '_scan_lmstudio_filesystem_models', '_has_lmstudio_weight_file', '_parse_ollama_inventory', '_refresh_inventory', '_match_inventory_model', '_inventory_run_allowed', '_inventory_filter_values', '_matches_inventory_search', '_filter_inventory_entries', '_inventory_filters', '_inventory_paths_cell', '_inventory', '_format_bytes', '_inventory_model_by_key', '_removal_target_from_key', '_delete_confirm_page', '_delete_result_page', '_delete_model_action', 'LMSTUDIO_MODELS_ROOT', 'LMSTUDIO_BUNDLED_MODELS_ROOT', 'OLLAMA_MODELS_ROOT', 'HF_HUB_CACHE_ROOT', 'LMSTUDIO_WEIGHT_SUFFIXES')
