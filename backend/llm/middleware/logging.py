"""
LoggingMiddleware — logs LLM call metadata at DEBUG level only.

# NEVER log system/user/response.content — prompt lengths ONLY.
Logs: provider, prompt_len (len(system) + len(user)), latency_ms.
"""
import logging
import time
from typing import Callable

from llm.base import LLMResponse
from llm.middleware.base import BaseLLMMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseLLMMiddleware):
    """
    Middleware that logs LLM call metadata at DEBUG level.

    Fields logged (DEBUG only — never INFO or above to avoid prod spam):
      - provider: str (from LLMResponse.provider)
      - prompt_len: int (len(system) + len(user))
      - latency_ms: float

    NEVER logs system prompt content, user prompt content, or response content.
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
        # NEVER log system/user/response.content — prompt lengths ONLY
        logger.debug(
            "llm.pipeline: provider=%s prompt_len=%d latency_ms=%.1f",
            response.provider,
            len(system) + len(user),
            latency_ms,
        )
        return response
