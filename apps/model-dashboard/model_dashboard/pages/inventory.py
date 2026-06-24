"""Installed-model inventory page and gated removal actions."""

# ruff: noqa: E501,F403,F405,I001
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from .. import removal
from ..components import *
from ..filters import *
from ..layout import _layout

LMSTUDIO_MODELS_ROOT = Path.home() / ".lmstudio" / "models"
LMSTUDIO_BUNDLED_MODELS_ROOT = Path.home() / ".lmstudio" / ".internal" / "bundled-models"
OLLAMA_MODELS_ROOT = Path.home() / ".ollama" / "models"
LMSTUDIO_WEIGHT_SUFFIXES = (".gguf", ".safetensors", ".bin", ".mlx", ".npz")

def _inventory_model_key(model):
    payload = "|".join(
        str(model.get(field) or "")
        for field in ("runtime", "model_id", "source_path", "local_path")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _inventory_model_removable(model):
    runtime = model.get("runtime")
    if model.get("removal_blocked_reason"):
        return False
    if runtime == "LM Studio":
        raw_path = model.get("local_path") or model.get("source_path")
        if not raw_path:
            return False
        try:
            target_path, _root = removal._lmstudio_folder_target(raw_path, LMSTUDIO_MODELS_ROOT)
        except removal.RemovalError:
            return False
        return target_path.exists()
    if runtime == "Ollama":
        return bool(model.get("model_id") and model.get("local_path"))
    return False


def _remove_model_control(model, enable_delete_actions=False, action_token=""):
    if not _inventory_model_removable(model):
        reason = model.get("removal_blocked_reason") or "Removal unavailable for this row"
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
    else:
        actions.append('<span class="empty">Register exact local model id first</span>')
    actions.append(_remove_model_control(model, enable_delete_actions, action_token))
    return '<div class="cell-stack">{}</div>'.format("".join(actions))


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
                "display_name": display_name or model_id,
                "status": status,
                "source_path": source_path,
                "local_path": local_path,
                "removal_blocked_reason": removal_blocked_reason,
            }
        )
    return models


def _scan_lmstudio_filesystem_models(root=LMSTUDIO_MODELS_ROOT, indexed_paths=()):
    root = Path(root)
    if not root.exists():
        return []
    indexed = {str(path).strip().lower() for path in indexed_paths if path}
    models = []
    for publisher_dir in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not publisher_dir.is_dir() or publisher_dir.name.startswith("."):
            continue
        for model_dir in sorted(publisher_dir.iterdir(), key=lambda item: item.name.lower()):
            if not model_dir.is_dir() or model_dir.name.startswith("."):
                continue
            if not _has_lmstudio_weight_file(model_dir):
                continue
            relative_path = f"{publisher_dir.name}/{model_dir.name}"
            if relative_path.lower() in indexed:
                continue
            models.append(
                {
                    "runtime": "LM Studio",
                    "model_id": relative_path,
                    "display_name": model_dir.name,
                    "status": "filesystem_only",
                    "source_path": relative_path,
                    "local_path": str(model_dir),
                }
            )
    return models


def _has_lmstudio_weight_file(model_dir):
    for item in Path(model_dir).rglob("*"):
        if item.name.startswith(".") or not item.is_file():
            continue
        if item.suffix.lower() in LMSTUDIO_WEIGHT_SUFFIXES:
            return True
    return False


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
                }
            )
    return models


def _refresh_inventory(timeout=5):
    checks = []
    models = []
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
                indexed_paths=[model.get("source_path") for model in lmstudio_models]
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
    return {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "models": models,
        "checks": checks,
    }


def _match_inventory_model(model, candidates):
    model_id = model["model_id"].lower()
    source_path = model.get("source_path", "").lower()
    matches = [
        row
        for row in candidates
        if row.get("local_model_id", "").lower() == model_id
        or row.get("model_name", "").lower() == model_id
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
        return model.get("status") in ("indexed", "loaded")
    return model.get("status") != "filesystem_only"


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


def _inventory(
    query=None,
    inventory_result=None,
    action_token="",
    enable_run_tests=False,
    enable_delete_actions=False,
    enable_refresh=True,
):
    candidates = _load_radar_candidates()
    result = inventory_result
    filters = _inventory_filter_values(query or {})
    check_rows = []
    model_rows = []
    entries = []
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
        for entry in _filter_inventory_entries(entries, filters):
            model = entry["model"]
            match_state = entry["match_state"]
            candidate = entry["candidate"]
            candidate_cell = (
                '<a href="/radar?q={id}">{id}</a>'.format(id=_text(candidate["candidate_id"]))
                if candidate
                else _pill(match_state)
            )
            model_rows.append(
                [
                    _text(model["runtime"]),
                    "<code>{}</code>".format(_text(model["model_id"])),
                    _text(model["display_name"]),
                    _pill(model["status"]),
                    _inventory_paths_cell(model),
                    candidate_cell,
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
    <section class="panel" style="margin-bottom:16px">
      <h2>Installed Models</h2>
      <p>This page checks local runtime inventory on demand. It does not download, install, benchmark, score, or import models.</p>
      <p>LM Studio rows distinguish <code>loaded</code>, <code>indexed</code>, and <code>filesystem_only</code>. Filesystem-only folders are visible on disk but are not runnable from the dashboard until LM Studio indexes or loads them.</p>
      <p>Use <strong>Local file path</strong> to locate leftover model folders in Finder. Remove actions are disabled unless the server is started with <code>--enable-delete-actions</code>, and confirmed LM Studio removals move folders to macOS Trash.</p>
      <form class="inline-form" method="post" action="/actions/refresh-inventory">
        <input type="hidden" name="token" value="{token}">
        <button type="submit"{disabled}>Refresh Inventory</button>
      </form>
      {disabled_note}
      <p class="empty">Last refresh: {checked_at}</p>
    </section>
    <section>
      <h2>Detected Models{filtered_count}</h2>
      {filters}
      {models}
    </section>
    <section style="margin-top:16px">
      <h2>Runtime Checks</h2>
      {checks}
    </section>
    """.format(
        token=_text(action_token),
        disabled="" if enable_refresh else " disabled",
        disabled_note=(
            ""
            if enable_refresh
            else '<p class="empty">Inventory refresh is available only on a localhost or loopback dashboard bind.</p>'
        ),
        checked_at=_text(result["checked_at"] if result else "not checked yet"),
        filtered_count=(
            f" ({len(_filter_inventory_entries(entries, filters))} of {len(entries)})"
            if any(filters.values())
            else ""
        ),
        filters=_inventory_filters(entries, filters),
        models=_table(
            [
                "Runtime",
                "Model id",
                "Display name",
                "Status",
                "Paths",
                "Registry match",
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
    return _layout("Installed Models", "/inventory", body)


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
):
    model = _inventory_model_by_key(inventory_result, remove_key)
    return removal.resolve_target(model, lmstudio_root, ollama_root)


def _delete_confirm_page(target, remove_key, action_token):
    body = f"""
    <section class="panel">
      <h2>Confirm Model Removal</h2>
      <p>This is a recoverable, local-only action. Review the exact target before continuing.</p>
      <div class="cell-stack">
        <div><strong>Runtime</strong><br>{_text(target.runtime)}</div>
        <div><strong>Model id</strong><br><code>{_text(target.model_id)}</code></div>
        <div><strong>Resolved path</strong><br><code>{_text(target.path)}</code></div>
        <div><strong>Contained under</strong><br><code>{_text(target.root)}</code></div>
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
    body = f"""
    <section class="panel">
      <h2>Model Removal {_text(status)}</h2>
      <p><strong>Runtime:</strong> {_text(result.target.runtime)}</p>
      <p><strong>Model id:</strong> <code>{_text(result.target.model_id)}</code></p>
      <p><strong>Action:</strong> {_text(result.target.action)}</p>
      <p><strong>Resolved path:</strong> <code>{_text(result.target.path)}</code></p>
      <p><strong>Exit code:</strong> <code>{_text(result.returncode)}</code></p>
      <pre class="command">{_text(_command_lines(result.command))}</pre>
      <pre class="command">{_text(result.stdout)}{_text(result.stderr)}</pre>
      <p><a href="/inventory">Back to Installed Models</a></p>
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
):
    target = _removal_target_from_key(
        inventory_result,
        remove_key,
        lmstudio_root=lmstudio_root,
        ollama_root=ollama_root,
    )
    if confirm_delete != "yes":
        return _delete_confirm_page(target, remove_key, action_token), None
    result = removal.remove_target(target, timeout=timeout)
    return _delete_result_page(result), result

__all__ = ('_inventory_model_key', '_inventory_model_removable', '_remove_model_control', '_inventory_action_cell', '_lmstudio_cli_path', '_collect_json_objects', '_first_value', '_looks_like_lmstudio_model', '_lmstudio_identity_values', '_local_path_from_source', '_lmstudio_local_path_and_removal_reason', '_ollama_manifest_path', '_parse_lmstudio_inventory', '_scan_lmstudio_filesystem_models', '_has_lmstudio_weight_file', '_parse_ollama_inventory', '_refresh_inventory', '_match_inventory_model', '_inventory_run_allowed', '_inventory_filter_values', '_matches_inventory_search', '_filter_inventory_entries', '_inventory_filters', '_inventory_paths_cell', '_inventory', '_format_bytes', '_inventory_model_by_key', '_removal_target_from_key', '_delete_confirm_page', '_delete_result_page', '_delete_model_action', 'LMSTUDIO_MODELS_ROOT', 'LMSTUDIO_BUNDLED_MODELS_ROOT', 'OLLAMA_MODELS_ROOT', 'LMSTUDIO_WEIGHT_SUFFIXES')
