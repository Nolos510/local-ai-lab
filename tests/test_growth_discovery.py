from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from local_ai_lab.growth.discovery import (
    MAX_RESPONSE_BYTES,
    DiscoveryError,
    check_updates,
    create_review_draft,
    discover,
    fetch_json,
    load_inbox,
    parse_metadata,
)


class FakeResponse:
    def __init__(self, payload: object, url: str) -> None:
        self.body = json.dumps(payload).encode()
        self.url = url

    def read(self, amount: int) -> bytes:
        return self.body[:amount]

    def geturl(self) -> str:
        return self.url

    def close(self) -> None:
        return None


def fixed_now() -> datetime:
    return datetime(2026, 7, 21, 19, 0, tzinfo=UTC)


@pytest.mark.parametrize("source", ["codex", "claude", "github", "mcp"])
def test_github_shaped_discovery_fixtures_parse_per_item_and_escape(source: str) -> None:
    items, skipped = parse_metadata(
        source,
        {
            "items": [
                {
                    "full_name": "official/safe-plugin",
                    "name": "<safe-plugin>",
                    "description": "<script>alert(1)</script>",
                    "html_url": "https://github.com/official/safe-plugin?token=ignored",
                    "default_branch": "main",
                    "stargazers_count": 999999,
                },
                {"name": "malformed"},
            ]
        },
        observed_at="2026-07-21T19:00:00Z",
    )
    assert skipped == 1
    assert len(items) == 1
    assert items[0]["title"] == "&lt;safe-plugin&gt;"
    assert "<script>" not in items[0]["summary"]
    assert items[0]["source_url"] == "https://github.com/official/safe-plugin"
    assert items[0]["popularity"] == 999999
    assert items[0]["review_state"] == "unreviewed"
    assert items[0]["approval"] == "none"


def test_huggingface_fixture_parses_without_promoting_popularity() -> None:
    items, skipped = parse_metadata(
        "huggingface",
        [
            {
                "id": "owner/model-name",
                "pipeline_tag": "text-generation",
                "sha": "abc123",
                "likes": 1_000_000,
            },
            "/Users/alice/private",
        ],
        observed_at="2026-07-21T19:00:00Z",
    )
    assert skipped == 1
    assert items[0]["source_url"] == "https://huggingface.co/owner/model-name"
    assert items[0]["popularity"] == 1_000_000
    assert items[0]["approval"] == "none"


def test_discover_writes_only_capped_escaped_ignored_state(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    inbox = repo / ".local-ai-lab" / "growth-inbox-v1.json"
    secret = "sk-super-private-value"

    def requester(request, *, timeout):
        assert timeout > 0
        assert "Authorization" not in request.headers
        assert set(request.headers) == {"Accept", "User-agent"}
        payload = {
            "items": [
                {
                    "full_name": "official/good",
                    "name": "good",
                    "description": f"</p><script>{secret}</script>",
                    "html_url": "https://github.com/official/good",
                    "default_branch": "main",
                    "stargazers_count": 5,
                }
            ]
        }
        return FakeResponse(payload, request.full_url)

    result = discover(
        source="github",
        query="safe query",
        inbox_path=inbox,
        repo_root=repo,
        requester=requester,
        now=fixed_now,
    )
    assert result == {"stored": 1, "skipped": 0, "failures": 0}
    stored = inbox.read_text(encoding="utf-8")
    assert secret not in stored
    assert "/Users/" not in stored
    assert "<script>" not in stored
    assert "[redacted untrusted metadata]" in stored
    assert inbox.stat().st_mode & 0o777 == 0o600
    assert inbox.parent.stat().st_mode & 0o777 == 0o700


def test_metadata_fetch_rejects_oversized_or_redirected_responses_without_leaking() -> None:
    allowed = frozenset({"api.github.com"})

    def oversized(request, *, timeout):
        assert timeout > 0
        return FakeResponse("x" * (MAX_RESPONSE_BYTES + 1), request.full_url)

    with pytest.raises(DiscoveryError) as oversized_exc:
        fetch_json(
            "https://api.github.com/search/repositories?q=safe",
            allowed_hosts=allowed,
            requester=oversized,
        )
    assert "invalid" in str(oversized_exc.value)

    def redirected(_request, *, timeout):
        assert timeout > 0
        return FakeResponse(
            {"secret": "sk-never-render-this"},
            "https://evil.example/Users/alice/private",
        )

    with pytest.raises(DiscoveryError) as redirect_exc:
        fetch_json(
            "https://api.github.com/search/repositories?q=safe",
            allowed_hosts=allowed,
            requester=redirected,
        )
    message = str(redirect_exc.value)
    assert "evil.example" not in message
    assert "alice" not in message
    assert "sk-never" not in message


def test_update_lookup_failures_are_per_item_nonfatal_and_catalog_is_unchanged(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    inbox = repo / ".local-ai-lab" / "growth-inbox-v1.json"
    catalogs = [
        {
            "id": "ext-good",
            "name": "Good",
            "source_url": "https://github.com/official/good",
        },
        {
            "id": "ext-bad",
            "name": "Bad",
            "source_url": "https://github.com/official/bad",
        },
        {"id": "ext-none", "name": "None", "source_url": None},
    ]
    before = json.dumps(catalogs, sort_keys=True)

    def requester(request, *, timeout):
        assert timeout > 0
        if urlsplit(request.full_url).path.endswith("/bad/releases/latest"):
            raise OSError("raw /Users/alice sk-private")
        return FakeResponse(
            {
                "tag_name": "v1.2.3",
                "name": "<b>release</b>",
                "html_url": "https://github.com/official/good/releases/tag/v1.2.3",
            },
            request.full_url,
        )

    result = check_updates(
        catalog_items=catalogs,
        inbox_path=inbox,
        repo_root=repo,
        requester=requester,
        now=fixed_now,
    )
    assert result == {"stored": 1, "skipped": 1, "failures": 1}
    assert json.dumps(catalogs, sort_keys=True) == before
    state = load_inbox(inbox, repo_root=repo)
    assert state["items"][0]["catalog_id"] == "ext-good"
    serialized = json.dumps(state)
    assert "alice" not in serialized
    assert "sk-private" not in serialized
    assert "<b>" not in serialized


def test_review_creates_ignored_draft_and_never_grants_install_authority(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    inbox = repo / ".local-ai-lab" / "growth-inbox-v1.json"

    def requester(request, *, timeout):
        return FakeResponse(
            {
                "items": [
                    {
                        "full_name": "official/review-me",
                        "name": "review-me",
                        "description": "review context",
                        "html_url": "https://github.com/official/review-me",
                        "default_branch": "main",
                        "stargazers_count": 10,
                    }
                ]
            },
            request.full_url,
        )

    discover(
        source="codex",
        query=None,
        inbox_path=inbox,
        repo_root=repo,
        requester=requester,
        now=fixed_now,
    )
    inbox_id = load_inbox(inbox, repo_root=repo)["items"][0]["id"]
    draft = create_review_draft(
        inbox_path=inbox,
        repo_root=repo,
        inbox_id=inbox_id,
        now=fixed_now,
    )
    assert draft["state"] == "draft"
    assert draft["catalog_promotion"] == "reviewed_repo_patch_required"
    assert draft["install_approval"] == "none"
    assert not (repo / "data" / "growth_registry").exists()
