"""Base class for LLM pipeline middlewares. next_fn calls the remaining chain."""
from abc import ABC, abstractmethod
from typing import Callable

from llm.base import LLMResponse


class BaseLLMMiddleware(ABC):
    """
    Base class for LLM pipeline middlewares. next_fn calls the remaining chain.

    Implement process() to intercept calls to the LLM pipeline.
    The next_fn argument is a callable[[str, str], LLMResponse] that
    invokes the rest of the middleware chain (and ultimately the provider).
    """

    @abstractmethod
    def process(
        self,
        system: str,
        user: str,
        next_fn: Callable[[str, str], LLMResponse],
    ) -> LLMResponse:
        """
        Process a completion request.

        Args:
            system: System prompt string.
            user: User prompt string.
            next_fn: Callable that continues the chain. Signature: (system, user) -> LLMResponse.

        Returns:
            LLMResponse from the chain (possibly decorated).
        """
