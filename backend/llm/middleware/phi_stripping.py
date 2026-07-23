"""
PHIStrippingMiddleware — blocks LLM calls when PHI patterns are detected in prompts.

Raises PHILeakError before forwarding to the provider if a Moroccan CIN,
date-of-birth (dd/mm/yyyy or yyyy-mm-dd), or other configured PHI pattern is found.
"""
import logging
import re
from typing import Callable

from llm.base import LLMResponse
from llm.middleware.base import BaseLLMMiddleware

logger = logging.getLogger(__name__)


class PHILeakError(Exception):
    """Raised when a PHI pattern is detected in an LLM prompt before forwarding."""


class PHIStrippingMiddleware(BaseLLMMiddleware):
    """
    Middleware that raises PHILeakError if a PHI pattern is found in the prompt.

    Patterns checked:
      - Moroccan CIN (e.g. AB12345, A123456)
      - Date of birth in dd/mm/yyyy format
      - Date of birth in yyyy-mm-dd format
    """

    _PATTERNS = [
        r'\b[A-Z]{1,2}[0-9]{5,6}\b',   # Moroccan CIN (e.g. AB12345)
        r'\b\d{2}/\d{2}/\d{4}\b',        # DOB dd/mm/yyyy
        r'\b\d{4}-\d{2}-\d{2}\b',        # DOB yyyy-mm-dd
    ]

    def process(
        self,
        system: str,
        user: str,
        next_fn: Callable[[str, str], LLMResponse],
    ) -> LLMResponse:
        for pat in self._PATTERNS:
            if re.search(pat, system) or re.search(pat, user):
                logger.error(
                    "PHIStrippingMiddleware: PHI pattern detected — blocking LLM call. pattern=%s",
                    pat,
                )
                raise PHILeakError(f"PHI pattern detected in LLM prompt: {pat}")
        return next_fn(system, user)
