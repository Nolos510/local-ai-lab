"""Explicit, metadata-only upstream checks for radar candidates."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

BENCHMARK_RUN_RE = re.compile(r"(?:^|\|)\s*benchmark_run_id\s*=\s*([^|]+)")
PUBLIC_USER_AGENT = "local-ai-lab-radar/1.0 (metadata-only)"


def fetch_json(url: str, *, timeout: float = 10.0) -> Any:
    """Fetch public JSON metadata without credentials or download behavior."""
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": PUBLIC_USER_AGENT,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _candidate_source(row: dict[str, str]) -> tuple[str, str, str] | None:
    model_url = str(row.get("model_page_url") or "").strip()
    github_url = str(row.get("github_url") or "").strip()
    for candidate_url in (model_url, github_url):
        if not candidate_url:
            continue
        parsed = urlparse(candidate_url)
        host = (parsed.hostname or "").lower()
        parts = [part for part in parsed.path.split("/") if part]
        if host in {"huggingface.co", "www.huggingface.co"} and len(parts) >= 2:
            repo_id = f"{parts[0]}/{parts[1]}"
            return "huggingface", candidate_url, repo_id
        if host in {"github.com", "www.github.com"} and len(parts) >= 2:
            repo_id = f"{parts[0]}/{parts[1].removesuffix('.git')}"
            return "github", candidate_url, repo_id
    return None


def _lookup_metadata(
    source_type: str,
    repo_id: str,
    *,
    timeout: float,
) -> dict[str, str]:
    encoded_repo = "/".join(quote(part, safe="") for part in repo_id.split("/"))
    if source_type == "huggingface":
        payload = fetch_json(
            f"https://huggingface.co/api/models/{encoded_repo}",
            timeout=timeout,
        )
        if not isinstance(payload, dict):
            raise ValueError("Hugging Face metadata response was not an object")
        revision = str(payload.get("sha") or "").strip()
        modified_at = str(payload.get("lastModified") or "").strip()
    else:
        repo = fetch_json(
            f"https://api.github.com/repos/{encoded_repo}",
            timeout=timeout,
        )
        if not isinstance(repo, dict):
            raise ValueError("GitHub repository metadata response was not an object")
        branch = str(repo.get("default_branch") or "").strip()
        if not branch:
            raise ValueError("GitHub metadata omitted the default branch")
        commit = fetch_json(
            f"https://api.github.com/repos/{encoded_repo}/commits/{quote(branch, safe='')}",
            timeout=timeout,
        )
        if not isinstance(commit, dict):
            raise ValueError("GitHub commit metadata response was not an object")
        revision = str(commit.get("sha") or "").strip()
        modified_at = str(repo.get("pushed_at") or "").strip()
    if not revision and not modified_at:
        raise ValueError("upstream metadata omitted both revision and modification time")
    return {"revision": revision, "modified_at": modified_at}


def _load_state(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1, "candidates": {}}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read upstream state: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), dict):
        raise ValueError("upstream state must contain a candidates object")
    payload["version"] = 1
    return payload


def _write_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(state, indent=2, sort_keys=True) + "\n"
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(serialized)
            temporary_name = handle.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            with suppress(FileNotFoundError):
                Path(temporary_name).unlink()


def _benchmark_run_id(run_notes: object) -> str:
    match = BENCHMARK_RUN_RE.search(str(run_notes or ""))
    return match.group(1).strip() if match else ""


def _has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        is not None
    )


def evaluation_markers(db_path: Path) -> dict[str, dict[str, object]]:
    """Return live graduation and a stable evaluation fingerprint per run id."""
    if not db_path.exists():
        return {}
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            if not _has_table(conn, "model_runs"):
                return {}
            confirmed_by_run: dict[int, int] = {}
            if _has_table(conn, "eval_scores"):
                columns = {
                    row["name"] for row in conn.execute("PRAGMA table_info(eval_scores)")
                }
                if "score_status" in columns:
                    score_rows = conn.execute(
                        "SELECT id, run_id FROM eval_scores WHERE score_status = 'confirmed'"
                    )
                else:
                    score_rows = conn.execute("SELECT id, run_id FROM eval_scores")
                confirmed_by_run = {
                    int(row["run_id"]): int(row["id"]) for row in score_rows
                }
            decisions_by_model: dict[int, int] = {}
            if _has_table(conn, "decisions"):
                for row in conn.execute(
                    "SELECT id, model_id FROM decisions ORDER BY id ASC"
                ):
                    decisions_by_model[int(row["model_id"])] = int(row["id"])

            markers: dict[str, dict[str, object]] = {}
            for row in conn.execute(
                "SELECT id, model_id, run_notes FROM model_runs ORDER BY id ASC"
            ):
                benchmark_id = _benchmark_run_id(row["run_notes"])
                if not benchmark_id:
                    continue
                run_id = int(row["id"])
                model_id = int(row["model_id"])
                score_id = confirmed_by_run.get(run_id)
                decision_id = decisions_by_model.get(model_id)
                graduated = score_id is not None or decision_id is not None
                markers[benchmark_id] = {
                    "graduated": graduated,
                    "fingerprint": (
                        f"run:{run_id}|score:{score_id or 0}|decision:{decision_id or 0}"
                    ),
                }
            return markers
    except sqlite3.Error as exc:
        raise ValueError(f"could not read dashboard evaluation state: {exc}") from exc


def _merge_candidates(
    registry_rows: list[dict[str, str]],
    overlay_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in registry_rows]
    by_id = {row.get("candidate_id", ""): index for index, row in enumerate(rows)}
    for overlay in overlay_rows:
        candidate_id = overlay.get("candidate_id", "")
        if candidate_id and candidate_id in by_id:
            merged = dict(rows[by_id[candidate_id]])
            merged.update({key: value for key, value in overlay.items() if value})
            rows[by_id[candidate_id]] = merged
        else:
            rows.append(dict(overlay))
    return rows


def _meaningfully_changed(record: dict[str, object], metadata: dict[str, str]) -> bool:
    return any(
        str(record.get(key) or "") != str(metadata.get(key) or "")
        for key in ("revision", "modified_at")
    )


def check_updates(
    *,
    candidates: list[dict[str, str]],
    state_path: Path,
    db_path: Path,
    timeout: float,
) -> dict[str, object]:
    state = _load_state(state_path)
    candidate_states = state["candidates"]
    assert isinstance(candidate_states, dict)
    markers = evaluation_markers(db_path)
    checked_at = datetime.now(UTC).isoformat()
    checked = 0
    baselined = 0
    changed = 0
    regraduated = 0
    skipped = 0
    failures: list[dict[str, str]] = []

    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        source = _candidate_source(candidate)
        if not candidate_id or source is None:
            skipped += 1
            continue
        source_type, source_url, repo_id = source
        try:
            metadata = _lookup_metadata(source_type, repo_id, timeout=timeout)
        except Exception as exc:  # Per-candidate metadata failures are intentionally non-fatal.
            failures.append({"candidate_id": candidate_id, "reason": str(exc)})
            continue

        checked += 1
        marker = markers.get(str(candidate.get("benchmark_run_id") or ""), {})
        graduated = bool(marker.get("graduated"))
        fingerprint = str(marker.get("fingerprint") or "")
        existing = candidate_states.get(candidate_id)
        record = dict(existing) if isinstance(existing, dict) else {}
        same_source = (
            record.get("source_type") == source_type
            and record.get("source_url") == source_url
        )

        if not record or not same_source:
            record = {
                "source_type": source_type,
                "source_url": source_url,
                **metadata,
                "update_pending": False,
                "checked_at": checked_at,
            }
            baselined += 1
        else:
            if (
                record.get("update_pending")
                and graduated
                and record.get("evaluation_fingerprint_at_update")
                and record.get("evaluation_fingerprint_at_update") != fingerprint
            ):
                record["update_pending"] = False
                record["cleared_reason"] = "re_evaluated"
                record["cleared_at"] = checked_at
                regraduated += 1

            if _meaningfully_changed(record, metadata):
                record["previous_revision"] = str(record.get("revision") or "")
                record["previous_modified_at"] = str(record.get("modified_at") or "")
                record.update(metadata)
                record["update_pending"] = graduated
                record["evaluation_fingerprint_at_update"] = fingerprint
                record.pop("dismissed_at", None)
                record.pop("cleared_at", None)
                record.pop("cleared_reason", None)
                changed += 1
            record["checked_at"] = checked_at
        candidate_states[candidate_id] = record

    state["version"] = 1
    state["checked_at"] = checked_at
    _write_state(state_path, state)
    return {
        "checked": checked,
        "baselined": baselined,
        "changed": changed,
        "regraduated": regraduated,
        "skipped": skipped,
        "failures": failures,
        "state_path": state_path,
    }


def command_check_updates(args, read_candidates) -> int:
    if not args.lookup:
        print("Network lookup: disabled (pass --lookup for public metadata only).")
        print("No upstream state was read or written.")
        return 0
    try:
        candidates = _merge_candidates(
            read_candidates(args.registry),
            read_candidates(args.local_inventory),
        )
        result = check_updates(
            candidates=candidates,
            state_path=args.state,
            db_path=args.db,
            timeout=args.timeout,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    print("Network lookup: enabled (public metadata only; no tokens or downloads).")
    print(f"Checked: {result['checked']}")
    print(f"Baselined: {result['baselined']}")
    print(f"Changed: {result['changed']}")
    print(f"Re-graduated: {result['regraduated']}")
    print(f"Skipped (no supported URL): {result['skipped']}")
    failures = result["failures"]
    assert isinstance(failures, list)
    print(f"Failures: {len(failures)}")
    for failure in failures:
        print(f"  {failure['candidate_id']}: {failure['reason']}")
    print(f"State: {result['state_path']}")
    return 0
