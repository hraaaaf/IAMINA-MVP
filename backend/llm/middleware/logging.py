"""
LoggingMiddleware — logs LLM call metadata at DEBUG level only.

# NEVER log system/user/response.content — prompt lengths and provider-reported
# token counts only.
"""
import logging
import time
from typing import Callable

from llm.base import LLMResponse
from llm.middleware.base import BaseLLMMiddleware

logger = logging.getLogger(__name__)


def _token_fields(response: LLMResponse) -> tuple[int | None, int | None, int | None, int | None]:
    usage = response.usage
    if usage is None:
        return None, None, None, None
    return (
        usage.input_tokens,
        usage.output_tokens,
        usage.cached_input_tokens,
        usage.total_tokens,
    )


class LoggingMiddleware(BaseLLMMiddleware):
    """Log non-sensitive LLM call metadata at DEBUG level.

    No prompt content, response content, patient identifier or guessed token
    count is logged. Token values are emitted only when reported by the provider.
    """

    def process(
        self,
        system: str,
        user: str,
        next_fn: Callable[[str, str], LLMResponse],
    ) -> LLMResponse:
        t0 = time.monotonic()
        response = next_fn(system, user)
        latency_ms = (time.monotonic() - t0) * 1000
        input_tokens, output_tokens, cached_input_tokens, total_tokens = _token_fields(response)
        logger.debug(
            "llm.pipeline: provider=%s prompt_len=%d latency_ms=%.1f "
            "input_tokens=%s output_tokens=%s cached_input_tokens=%s total_tokens=%s",
            response.provider,
            len(system) + len(user),
            latency_ms,
            input_tokens,
            output_tokens,
            cached_input_tokens,
            total_tokens,
        )
        return response
