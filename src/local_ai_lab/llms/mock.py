class MockChatProvider:
    """Deterministic local provider for tests and offline pipeline checks."""

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        del prompt, system_prompt
        return "Mock local answer. A real answer requires Ollama or LM Studio."
