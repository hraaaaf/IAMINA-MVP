from typing import Iterator

from .base import BaseLLMProvider, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    """Stub for Claude provider."""

    def __init__(self, model: str = "claude-3-5-sonnet"):
        self.model = model

    def complete(self, system: str, user: str) -> LLMResponse:
        return LLMResponse(content="Claude stub", provider=self.model)
