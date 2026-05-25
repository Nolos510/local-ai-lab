from typing import Protocol
from urllib.parse import urlsplit, urlunsplit


class ChatProviderError(RuntimeError):
    """Base error for local chat provider failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class ChatProviderConnectionError(ChatProviderError):
    """Raised when a provider endpoint cannot be reached."""


class ChatProviderHTTPError(ChatProviderError):
    """Raised when a provider endpoint returns an HTTP error."""


class ChatProviderResponseError(ChatProviderError):
    """Raised when a provider returns an invalid response payload."""


class ChatProvider(Protocol):
    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        """Generate a response from a prompt."""


def sanitize_provider_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme or not parts.hostname:
        return "configured URL"
    netloc = parts.hostname
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, "", "", ""))
