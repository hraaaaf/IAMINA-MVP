import logging
from typing import Iterator

from django.conf import settings

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

_KIMI_TIMEOUT_SECONDS = 15.0

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]


class KimiProvider(BaseLLMProvider):
    """
    Kimi K2 via OpenAI-compatible API.
    Activate: set LLM_PROVIDER=kimi + KIMI_API_KEY + KIMI_BASE_URL in .env.
    GDPR note: only use with a self-hosted or EU-located endpoint.
    """

    def __init__(self, model: str = "kimi-k2"):
        if OpenAI is None:
            logger.error("KimiProvider: `openai` package missing. Run: pip install openai")
            self.client = None
        else:
            self.client = OpenAI(
                base_url=getattr(settings, "KIMI_BASE_URL", ""),
                api_key=getattr(settings, "KIMI_API_KEY", "dummy"),
                timeout=_KIMI_TIMEOUT_SECONDS,
                max_retries=0,
            )
        self.model = model

    @property
    def model_name(self) -> str:
        return self.model

    def _messages(self, system: str, user: str) -> list[dict]:
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def complete(self, system: str, user: str) -> LLMResponse:
        if not self.client:
            raise RuntimeError("KimiProvider: client not initialized.")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(system, user),
            timeout=_KIMI_TIMEOUT_SECONDS,
        )
        return LLMResponse(
            content=response.choices[0].message.content or "",
            provider=self.model,
        )

    def stream(self, system: str, user: str) -> Iterator[str]:
        """Stream through an OpenAI-compatible client with a bounded timeout."""
        if not self.client:
            raise RuntimeError("KimiProvider: client not initialized.")
        with self.client.chat.completions.stream(
            model=self.model,
            messages=self._messages(system, user),
            timeout=_KIMI_TIMEOUT_SECONDS,
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text
