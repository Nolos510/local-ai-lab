from typing import Protocol


class ChatProvider(Protocol):
    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        """Generate a response from a prompt."""
