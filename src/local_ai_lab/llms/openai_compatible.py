import httpx

from local_ai_lab.llms.base import (
    ChatProviderConnectionError,
    ChatProviderHTTPError,
    ChatProviderResponseError,
    sanitize_provider_url,
)


class OpenAICompatibleChatProvider:
    def __init__(self, *, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.2,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise ChatProviderHTTPError(
                self._error_message(f"HTTP {exc.response.status_code}")
            ) from exc
        except httpx.RequestError as exc:
            raise ChatProviderConnectionError(self._error_message("connection failed")) from exc
        except ValueError as exc:
            raise ChatProviderResponseError(self._error_message("invalid JSON response")) from exc

        if not isinstance(payload, dict):
            raise ChatProviderResponseError(self._error_message("unexpected response payload"))
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ChatProviderResponseError(self._error_message("empty choices in response"))
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ChatProviderResponseError(self._error_message("unexpected response payload"))
        message = first_choice.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ChatProviderResponseError(self._error_message("unexpected response payload"))
        content = message["content"].strip()
        if not content:
            raise ChatProviderResponseError(self._error_message("empty message content"))
        return content

    def _error_message(self, reason: str) -> str:
        return (
            f"LM Studio/OpenAI-compatible provider failed: {reason}. "
            f"Endpoint: {sanitize_provider_url(self.base_url)}. "
            f"Configured model: {self.model}. "
            "Verify the LM Studio local server is running. "
            "Run `uv run local-ai-lab doctor`."
        )
