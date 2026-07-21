"""Privacy-narrow helpers shared by Growth discovery and mutation flows."""

from __future__ import annotations

import html
import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit

MAX_UNTRUSTED_TEXT = 500
PRIVATE_PATH_RE = re.compile(r"(?:/users/|/home/|[a-z]:\\\\users\\\\)", re.IGNORECASE)
SECRET_LITERAL_RE = re.compile(
    r"(?:^|[^A-Za-z0-9])(?:sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{12,}|"
    r"github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{8,}|"
    r"AKIA[A-Z0-9]{12,}|(?:api[_-]?key|access[_-]?token|authorization)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def contains_sensitive_literal(
    value: object,
    *,
    sensitive_tokens: Iterable[str] = (),
) -> bool:
    """Return true without echoing a value that is unsafe to persist or render."""
    text = str(value or "")
    folded = text.casefold()
    return bool(
        PRIVATE_PATH_RE.search(text)
        or SECRET_LITERAL_RE.search(text)
        or any(
            token.casefold() in folded
            for token in sensitive_tokens
            if isinstance(token, str) and len(token) >= 3
        )
    )


def escape_untrusted(
    value: object,
    *,
    limit: int = MAX_UNTRUSTED_TEXT,
    sensitive_tokens: Iterable[str] = (),
) -> str:
    """Normalize, cap, redact, and HTML-escape public metadata before persistence."""
    if not isinstance(value, str):
        return ""
    text = CONTROL_RE.sub("", ANSI_RE.sub("", value)).strip()
    if not text:
        return ""
    if contains_sensitive_literal(text, sensitive_tokens=sensitive_tokens):
        return "[redacted untrusted metadata]"
    encoded = text.encode("utf-8", errors="ignore")[: max(0, limit)]
    text = encoded.decode("utf-8", errors="ignore")
    return html.escape(text, quote=True)[: max(0, limit)]


def safe_public_url(value: object, *, allowed_hosts: frozenset[str] | None = None) -> str | None:
    """Return a credential-free HTTPS URL without query or fragment, or ``None``."""
    if not isinstance(value, str) or contains_sensitive_literal(value):
        return None
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").casefold()
        if (
            parsed.scheme != "https"
            or not host
            or parsed.username is not None
            or parsed.password is not None
            or (allowed_hosts is not None and host not in allowed_hosts)
        ):
            return None
        port = parsed.port
    except ValueError:
        return None
    if port not in (None, 443):
        return None
    return urlunsplit(("https", parsed.netloc, parsed.path or "/", "", ""))


def safe_failure(message: str) -> RuntimeError:
    """Build a fixed-message exception; callers must never include raw exception text."""
    return RuntimeError(message)


__all__ = (
    "MAX_UNTRUSTED_TEXT",
    "contains_sensitive_literal",
    "escape_untrusted",
    "safe_failure",
    "safe_public_url",
)
