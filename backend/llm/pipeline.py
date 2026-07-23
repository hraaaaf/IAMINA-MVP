"""
LLMPipeline — Decorator wrapper around BaseLLMProvider.

Composes a list of BaseLLMMiddleware instances into a call chain.
stream() and think() delegate directly to the inner provider (no middleware in v1).

Usage:
    pipeline = LLMPipeline(get_llm(), [LoggingMiddleware()])
    response = pipeline.complete(system, user)

The middleware chain for complete() is built so that M1 is called first,
then M2, ..., then the inner provider — i.e. execution order is M1 → M2 → inner.
"""
from typing import Iterator

from llm.base import BaseLLMProvider, LLMResponse
from llm.middleware.base import BaseLLMMiddleware


class LLMPipeline(BaseLLMProvider):
    """
    Pipeline decorator over a BaseLLMProvider.

    Wraps complete() with an ordered chain of middlewares.
    stream() and think() bypass middlewares and delegate directly to inner.
    """

    def __init__(
        self,
        inner: BaseLLMProvider,
        middlewares: list[BaseLLMMiddleware] | None = None,
    ) -> None:
        self._inner = inner
        self._middlewares = list(middlewares or [])

    @property
    def model_name(self) -> str:
        return getattr(self._inner, "model_name", "pipeline")

    def complete(self, system: str, user: str) -> LLMResponse:
        """
        Run the middleware chain, then the inner provider.

        Middleware execution order: first middleware in list runs first.
        Chain construction uses default-arg capture to avoid closure-by-reference bug.
        """
        chain = self._inner.complete
        for middleware in reversed(self._middlewares):
            prev = chain
            # IMPORTANT: mw=middleware, nxt=prev captures current values by value,
            # not by reference. Without default args, all closures would capture
            # the last values of middleware/prev after the loop ends.
            def chain(s, u, mw=middleware, nxt=prev):
                return mw.process(s, u, nxt)
        return chain(system, user)

    def stream(self, system: str, user: str) -> Iterator[str]:
        """Delegates directly to inner provider — no middleware in pipeline v1."""
        return self._inner.stream(system, user)

    def think(self, system: str, user: str) -> tuple[str, str]:
        """Delegates directly to inner provider — no middleware in pipeline v1."""
        return self._inner.think(system, user)
