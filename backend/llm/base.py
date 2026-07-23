from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass
class LLMResponse:
    content: str
    provider: str
    from_cache: bool = False


class BaseLLMProvider(ABC):

    @abstractmethod
    def complete(self, system: str, user: str) -> LLMResponse:
        """Single-turn completion. JSON output expected."""
        pass

    def stream(self, system: str, user: str) -> Iterator[str]:
        """
        Streaming completion (SSE).
        Default: falls back to complete() for providers that don't stream natively.
        """
        yield self.complete(system, user).content

    def think(self, system: str, user: str) -> tuple[str, str]:
        """
        Returns (thinking, response).
        thinking: raisonnement interne caché (jamais affiché)
        response: réponse finale à montrer
        Default: pas de thinking, appel complete() classique.
        """
        result = self.complete(system, user)
        return "", result.content
