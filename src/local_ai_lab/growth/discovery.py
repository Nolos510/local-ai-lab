"""Opt-in public-metadata discovery for the ignored Growth inbox."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from local_ai_lab.growth.catalog import SAFE_ID_RE
from local_ai_lab.growth.privacy import (
    contains_sensitive_literal,
    escape_untrusted,
    safe_public_url,
)
from local_ai_lab.growth.private_state import (
    PrivateStateError,
    load_private_json,
    write_private_json_atomic,
)

DISCOVERY_SOURCES = frozenset({"codex", "claude", "github", "huggingface", "mcp"})
GITHUB_API_HOSTS = frozenset({"api.github.com"})
HUGGINGFACE_API_HOSTS = frozenset({"huggingface.co"})
RESULT_URL_HOSTS = frozenset({"github.com", "huggingface.co"})
FETCH_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 1_000_000
MAX_INBOX_ITEMS = 200
MAX_REVIEWS = 200
INBOX_ID_RE = re.compile(r"^inbox-[a-f0-9]{20}$")
REVIEW_ID_RE = re.compile(r"^review-[a-f0-9]{20}$")
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,95}$")
QUERY_RE = re.compile(r"^[A-Za-z0-9 _.,:/@+()#-]{1,80}$")


class DiscoveryError(RuntimeError):
    """Discovery failed without retaining public response bodies or exception details."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def empty_inbox() -> dict[str, Any]:
    return {"schema_version": "growth-inbox-v1", "items": [], "reviews": []}


def _timestamp(now: Callable[[], datetime] | None = None) -> str:
    value = datetime.now(UTC) if now is None else now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_version(value: object, *, sensitive_tokens: Iterable[str]) -> str | None:
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        return None
    if contains_sensitive_literal(value, sensitive_tokens=sensitive_tokens):
        return None
    return value


def _safe_popularity(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _inbox_id(source: str, identity: str, version: str | None, kind: str) -> str:
    digest = hashlib.sha256(f"{source}\0{kind}\0{identity}\0{version or ''}".encode()).hexdigest()
    return f"inbox-{digest[:20]}"


def _candidate(
    *,
    source: str,
    kind: str,
    identity: str,
    title: object,
    summary: object,
    source_url: object,
    version: object,
    popularity: object,
    observed_at: str,
    catalog_id: str | None = None,
    sensitive_tokens: Iterable[str] = (),
) -> dict[str, Any] | None:
    safe_url = safe_public_url(source_url, allowed_hosts=RESULT_URL_HOSTS)
    safe_title = escape_untrusted(title, limit=160, sensitive_tokens=sensitive_tokens)
    safe_summary = escape_untrusted(summary, sensitive_tokens=sensitive_tokens)
    safe_version = _safe_version(version, sensitive_tokens=sensitive_tokens)
    if not identity or not safe_title or safe_url is None:
        return None
    if catalog_id is not None and not SAFE_ID_RE.fullmatch(catalog_id):
        return None
    return {
        "id": _inbox_id(source, identity, safe_version, kind),
        "source": source,
        "kind": kind,
        "catalog_id": catalog_id,
        "title": safe_title,
        "summary": safe_summary,
        "source_url": safe_url,
        "version": safe_version,
        "popularity": _safe_popularity(popularity),
        "observed_at": observed_at,
        "review_state": "unreviewed",
        "approval": "none",
        "untrusted": True,
    }


def _github_entries(payload: object) -> Sequence[object]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise DiscoveryError("public metadata response was invalid")
    return payload["items"]


def _huggingface_entries(payload: object) -> Sequence[object]:
    if not isinstance(payload, list):
        raise DiscoveryError("public metadata response was invalid")
    return payload


def parse_metadata(
    source: str,
    payload: object,
    *,
    observed_at: str,
    sensitive_tokens: Iterable[str] = (),
) -> tuple[list[dict[str, Any]], int]:
    """Parse source fixtures item-by-item; malformed siblings are non-fatal."""
    if source not in DISCOVERY_SOURCES:
        raise DiscoveryError("unsupported discovery source", exit_code=2)
    entries = _huggingface_entries(payload) if source == "huggingface" else _github_entries(payload)
    items: list[dict[str, Any]] = []
    skipped = 0
    for raw in entries:
        try:
            if not isinstance(raw, dict):
                raise ValueError
            if source == "huggingface":
                identity = raw.get("id") or raw.get("modelId")
                if not isinstance(identity, str) or not MODEL_ID_RE.fullmatch(identity):
                    raise ValueError
                item = _candidate(
                    source=source,
                    kind="discovery",
                    identity=identity,
                    title=identity,
                    summary=raw.get("pipeline_tag") or raw.get("description") or "",
                    source_url=f"https://huggingface.co/{identity}",
                    version=raw.get("sha") or raw.get("lastModified"),
                    popularity=raw.get("likes") or raw.get("downloads"),
                    observed_at=observed_at,
                    sensitive_tokens=sensitive_tokens,
                )
            else:
                identity = raw.get("full_name")
                if not isinstance(identity, str) or not MODEL_ID_RE.fullmatch(identity):
                    raise ValueError
                item = _candidate(
                    source=source,
                    kind="discovery",
                    identity=identity,
                    title=raw.get("name") or identity,
                    summary=raw.get("description") or "",
                    source_url=raw.get("html_url"),
                    version=raw.get("default_branch"),
                    popularity=raw.get("stargazers_count"),
                    observed_at=observed_at,
                    sensitive_tokens=sensitive_tokens,
                )
            if item is None:
                raise ValueError
            items.append(item)
        except (TypeError, ValueError):
            skipped += 1
    return items, skipped


def _validate_fetch_url(value: str, *, allowed_hosts: frozenset[str]) -> None:
    invalid = False
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").casefold()
        port = parsed.port
    except ValueError:
        invalid = True
    if invalid:
        raise DiscoveryError("public metadata endpoint was invalid")
    if (
        parsed.scheme != "https"
        or host not in allowed_hosts
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise DiscoveryError("public metadata endpoint was invalid")


class _RestrictedRedirect(HTTPRedirectHandler):
    def __init__(self, allowed_hosts: frozenset[str]) -> None:
        self.allowed_hosts = allowed_hosts
        super().__init__()

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        _validate_fetch_url(newurl, allowed_hosts=self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _default_requester(allowed_hosts: frozenset[str]):
    opener = build_opener(ProxyHandler({}), _RestrictedRedirect(allowed_hosts))
    return opener.open


def fetch_json(
    url: str,
    *,
    allowed_hosts: frozenset[str],
    requester: Callable[..., Any] | None = None,
    timeout: float = FETCH_TIMEOUT_SECONDS,
) -> object:
    """Fetch one capped JSON response with no auth, cookies, or environment proxy."""
    _validate_fetch_url(url, allowed_hosts=allowed_hosts)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "local-ai-lab-growth/1.0 (metadata-only)",
        },
        method="GET",
    )
    open_request = _default_requester(allowed_hosts) if requester is None else requester
    response = None
    failure: DiscoveryError | None = None
    body: object = None
    try:
        response = open_request(request, timeout=timeout)
        final_url = response.geturl() if hasattr(response, "geturl") else url
        _validate_fetch_url(final_url, allowed_hosts=allowed_hosts)
        body = response.read(MAX_RESPONSE_BYTES + 1)
    except DiscoveryError as error:
        failure = error
    except Exception:  # public adapters must not retain provider-specific exception text
        failure = DiscoveryError("public metadata lookup failed")
    finally:
        if response is not None and hasattr(response, "close"):
            try:
                response.close()
            except Exception:
                if failure is None:
                    failure = DiscoveryError("public metadata lookup failed")
    if failure is not None:
        raise failure
    if not isinstance(body, bytes) or len(body) > MAX_RESPONSE_BYTES:
        raise DiscoveryError("public metadata response was invalid")
    parsed: object | None = None
    invalid_response = False
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        invalid_response = True
    if invalid_response:
        raise DiscoveryError("public metadata response was invalid")
    return parsed


def _discovery_endpoint(source: str, query: str | None) -> tuple[str, frozenset[str]]:
    if query is not None and (not QUERY_RE.fullmatch(query) or contains_sensitive_literal(query)):
        raise DiscoveryError("discovery query is invalid", exit_code=2)
    user_query = query or ""
    if source == "huggingface":
        params = {"search": user_query or "mcp", "limit": "25"}
        return f"https://huggingface.co/api/models?{urlencode(params)}", HUGGINGFACE_API_HOSTS
    prefixes = {
        "codex": "topic:codex-plugin",
        "claude": "topic:claude-code-plugin",
        "github": "topic:artificial-intelligence",
        "mcp": "topic:model-context-protocol",
    }
    if source not in prefixes:
        raise DiscoveryError("unsupported discovery source", exit_code=2)
    search = " ".join(part for part in (prefixes[source], user_query) if part)
    params = {"q": search, "sort": "stars", "order": "desc", "per_page": "25"}
    return f"https://api.github.com/search/repositories?{urlencode(params)}", GITHUB_API_HOSTS


def validate_inbox(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "items", "reviews"}:
        raise DiscoveryError("private Growth inbox has an invalid envelope")
    if payload.get("schema_version") != "growth-inbox-v1":
        raise DiscoveryError("private Growth inbox has an invalid schema version")
    items = payload.get("items")
    reviews = payload.get("reviews")
    if not isinstance(items, list) or not isinstance(reviews, list):
        raise DiscoveryError("private Growth inbox collections are invalid")
    required_item = {
        "id",
        "source",
        "kind",
        "catalog_id",
        "title",
        "summary",
        "source_url",
        "version",
        "popularity",
        "observed_at",
        "review_state",
        "approval",
        "untrusted",
    }
    item_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != required_item:
            raise DiscoveryError("private Growth inbox item is invalid")
        item_id = item.get("id")
        if (
            not isinstance(item_id, str)
            or not INBOX_ID_RE.fullmatch(item_id)
            or item_id in item_ids
        ):
            raise DiscoveryError("private Growth inbox item is invalid")
        if item.get("source") not in DISCOVERY_SOURCES or item.get("kind") not in {
            "discovery",
            "update",
        }:
            raise DiscoveryError("private Growth inbox item is invalid")
        catalog_id = item.get("catalog_id")
        if catalog_id is not None and (
            not isinstance(catalog_id, str) or not SAFE_ID_RE.fullmatch(catalog_id)
        ):
            raise DiscoveryError("private Growth inbox item is invalid")
        if not all(
            isinstance(item.get(field), str) for field in ("title", "summary", "observed_at")
        ):
            raise DiscoveryError("private Growth inbox item is invalid")
        if (
            len(item["title"]) > 160
            or len(item["summary"]) > 500
            or not re.fullmatch(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", item["observed_at"])
        ):
            raise DiscoveryError("private Growth inbox item is invalid")
        if contains_sensitive_literal(json.dumps(item, sort_keys=True)):
            raise DiscoveryError("private Growth inbox item is invalid")
        if safe_public_url(item.get("source_url"), allowed_hosts=RESULT_URL_HOSTS) is None:
            raise DiscoveryError("private Growth inbox item is invalid")
        version = item.get("version")
        if version is not None and (
            not isinstance(version, str) or not VERSION_RE.fullmatch(version)
        ):
            raise DiscoveryError("private Growth inbox item is invalid")
        if item.get("popularity") is not None and _safe_popularity(item["popularity"]) is None:
            raise DiscoveryError("private Growth inbox item is invalid")
        if (
            item.get("review_state") != "unreviewed"
            or item.get("approval") != "none"
            or item.get("untrusted") is not True
        ):
            raise DiscoveryError("private Growth inbox item is invalid")
        item_ids.add(item_id)
    required_review = {
        "id",
        "inbox_id",
        "created_at",
        "state",
        "title",
        "source",
        "source_url",
        "observed_version",
        "catalog_promotion",
        "install_approval",
    }
    review_ids: set[str] = set()
    for review in reviews:
        if not isinstance(review, dict) or set(review) != required_review:
            raise DiscoveryError("private Growth review draft is invalid")
        review_id = review.get("id")
        if (
            not isinstance(review_id, str)
            or not REVIEW_ID_RE.fullmatch(review_id)
            or review_id in review_ids
        ):
            raise DiscoveryError("private Growth review draft is invalid")
        if review.get("inbox_id") not in item_ids or review.get("state") != "draft":
            raise DiscoveryError("private Growth review draft is invalid")
        if (
            review.get("catalog_promotion") != "reviewed_repo_patch_required"
            or review.get("install_approval") != "none"
        ):
            raise DiscoveryError("private Growth review draft is invalid")
        if contains_sensitive_literal(json.dumps(review, sort_keys=True)):
            raise DiscoveryError("private Growth review draft is invalid")
        review_ids.add(review_id)
    return payload


def load_inbox(path: Path, *, repo_root: Path) -> dict[str, Any]:
    try:
        payload = load_private_json(
            path,
            repo_root=repo_root,
            filename="growth-inbox-v1.json",
            default=empty_inbox(),
        )
    except PrivateStateError as error:
        message = str(error)
    else:
        return validate_inbox(payload)
    raise DiscoveryError(message)


def write_inbox(path: Path, payload: dict[str, Any], *, repo_root: Path) -> None:
    validate_inbox(payload)
    try:
        write_private_json_atomic(
            path,
            payload,
            repo_root=repo_root,
            filename="growth-inbox-v1.json",
        )
    except PrivateStateError as error:
        message = str(error)
    else:
        return
    raise DiscoveryError(message)


def _merge_items(state: dict[str, Any], items: Sequence[dict[str, Any]]) -> None:
    by_id = {item["id"]: item for item in state["items"]}
    by_id.update((item["id"], item) for item in items)
    ordered = sorted(by_id.values(), key=lambda item: (item["observed_at"], item["id"]))
    state["items"] = ordered[-MAX_INBOX_ITEMS:]
    retained = {item["id"] for item in state["items"]}
    state["reviews"] = [review for review in state["reviews"] if review["inbox_id"] in retained]


def discover(
    *,
    source: str,
    query: str | None,
    inbox_path: Path,
    repo_root: Path,
    requester: Callable[..., Any] | None = None,
    now: Callable[[], datetime] | None = None,
    sensitive_tokens: Iterable[str] = (),
) -> dict[str, int]:
    endpoint, allowed_hosts = _discovery_endpoint(source, query)
    observed_at = _timestamp(now)
    payload = fetch_json(endpoint, allowed_hosts=allowed_hosts, requester=requester)
    items, skipped = parse_metadata(
        source,
        payload,
        observed_at=observed_at,
        sensitive_tokens=sensitive_tokens,
    )
    state = load_inbox(inbox_path, repo_root=repo_root)
    _merge_items(state, items)
    write_inbox(inbox_path, state, repo_root=repo_root)
    return {"stored": len(items), "skipped": skipped, "failures": 0}


def _github_update(
    item: dict[str, Any],
    *,
    observed_at: str,
    requester: Callable[..., Any] | None,
    sensitive_tokens: Iterable[str],
) -> dict[str, Any] | None:
    parsed = urlsplit(item.get("source_url") or "")
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.hostname != "github.com"
        or len(parts) != 2
        or not all(SAFE_ID_RE.fullmatch(part.casefold()) for part in parts)
    ):
        return None
    endpoint = f"https://api.github.com/repos/{quote(parts[0])}/{quote(parts[1])}/releases/latest"
    payload = fetch_json(endpoint, allowed_hosts=GITHUB_API_HOSTS, requester=requester)
    if not isinstance(payload, dict):
        raise DiscoveryError("public metadata response was invalid")
    version = payload.get("tag_name")
    return _candidate(
        source="github",
        kind="update",
        identity=item["id"],
        catalog_id=item["id"],
        title=f"{item['name']} update metadata",
        summary=payload.get("name") or "Public release metadata observed; review required.",
        source_url=payload.get("html_url") or item.get("source_url"),
        version=version,
        popularity=None,
        observed_at=observed_at,
        sensitive_tokens=sensitive_tokens,
    )


def _huggingface_update(
    item: dict[str, Any],
    *,
    observed_at: str,
    requester: Callable[..., Any] | None,
    sensitive_tokens: Iterable[str],
) -> dict[str, Any] | None:
    parsed = urlsplit(item.get("source_url") or "")
    identity = "/".join(part for part in parsed.path.split("/") if part)
    if parsed.hostname != "huggingface.co" or not MODEL_ID_RE.fullmatch(identity):
        return None
    endpoint = f"https://huggingface.co/api/models/{quote(identity, safe='/')}"
    payload = fetch_json(endpoint, allowed_hosts=HUGGINGFACE_API_HOSTS, requester=requester)
    if not isinstance(payload, dict):
        raise DiscoveryError("public metadata response was invalid")
    return _candidate(
        source="huggingface",
        kind="update",
        identity=item["id"],
        catalog_id=item["id"],
        title=f"{item['name']} update metadata",
        summary=payload.get("pipeline_tag") or "Public model metadata observed; review required.",
        source_url=item.get("source_url"),
        version=payload.get("sha") or payload.get("lastModified"),
        popularity=payload.get("likes") or payload.get("downloads"),
        observed_at=observed_at,
        sensitive_tokens=sensitive_tokens,
    )


def check_updates(
    *,
    catalog_items: Sequence[dict[str, Any]],
    inbox_path: Path,
    repo_root: Path,
    requester: Callable[..., Any] | None = None,
    now: Callable[[], datetime] | None = None,
    sensitive_tokens: Iterable[str] = (),
) -> dict[str, int]:
    """Collect review-only public version context; per-item failures are non-fatal."""
    observed_at = _timestamp(now)
    found: list[dict[str, Any]] = []
    failures = 0
    skipped = 0
    for item in catalog_items:
        try:
            parsed = urlsplit(item.get("source_url") or "")
            if parsed.hostname == "github.com":
                result = _github_update(
                    item,
                    observed_at=observed_at,
                    requester=requester,
                    sensitive_tokens=sensitive_tokens,
                )
            elif parsed.hostname == "huggingface.co":
                result = _huggingface_update(
                    item,
                    observed_at=observed_at,
                    requester=requester,
                    sensitive_tokens=sensitive_tokens,
                )
            else:
                skipped += 1
                continue
            if result is None:
                skipped += 1
            else:
                found.append(result)
        except DiscoveryError:
            failures += 1
    state = load_inbox(inbox_path, repo_root=repo_root)
    _merge_items(state, found)
    write_inbox(inbox_path, state, repo_root=repo_root)
    return {"stored": len(found), "skipped": skipped, "failures": failures}


def create_review_draft(
    *,
    inbox_path: Path,
    repo_root: Path,
    inbox_id: str,
    now: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    if not INBOX_ID_RE.fullmatch(inbox_id or ""):
        raise DiscoveryError("Growth inbox id is invalid", exit_code=2)
    state = load_inbox(inbox_path, repo_root=repo_root)
    item = next((entry for entry in state["items"] if entry["id"] == inbox_id), None)
    if item is None:
        raise DiscoveryError("Growth inbox item was not found", exit_code=2)
    created_at = _timestamp(now)
    digest = hashlib.sha256(f"{inbox_id}\0{created_at}".encode()).hexdigest()
    draft = {
        "id": f"review-{digest[:20]}",
        "inbox_id": inbox_id,
        "created_at": created_at,
        "state": "draft",
        "title": item["title"],
        "source": item["source"],
        "source_url": item["source_url"],
        "observed_version": item["version"],
        "catalog_promotion": "reviewed_repo_patch_required",
        "install_approval": "none",
    }
    by_inbox = {review["inbox_id"]: review for review in state["reviews"]}
    by_inbox[inbox_id] = draft
    state["reviews"] = sorted(by_inbox.values(), key=lambda review: review["id"])[-MAX_REVIEWS:]
    write_inbox(inbox_path, state, repo_root=repo_root)
    return draft


__all__ = (
    "DISCOVERY_SOURCES",
    "DiscoveryError",
    "INBOX_ID_RE",
    "check_updates",
    "create_review_draft",
    "discover",
    "empty_inbox",
    "fetch_json",
    "load_inbox",
    "parse_metadata",
    "validate_inbox",
    "write_inbox",
)
