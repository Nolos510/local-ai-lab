class MockChatProvider:
    """Deterministic local provider for tests and offline pipeline checks."""

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        del system_prompt
        excerpt = " ".join(prompt.split())[:280]
        return (
            "Mock local answer. A real answer requires Ollama or LM Studio. "
            f"Prompt excerpt: {excerpt}"
        )
