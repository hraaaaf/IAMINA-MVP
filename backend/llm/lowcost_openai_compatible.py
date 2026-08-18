import logging
from typing import Iterator

from django.conf import settings

from .base import BaseLLMProvider, LLMResponse, LLMUsage

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 15.0
_MAX_OUTPUT_TOKENS = 160

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]


def _usage_from_response(response) -> LLMUsage | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    details = getattr(usage, "prompt_tokens_details", None)
    cached = (
        getattr(details, "cached_tokens", None)
        if details is not None
        else None
    )
    return LLMUsage(
        input_tokens=getattr(usage, "prompt_tokens", None),
        output_tokens=getattr(usage, "completion_tokens", None),
        cached_input_tokens=cached,
        total_tokens=getattr(usage, "total_tokens", None),
    )


class OpenAICompatibleLowCostProvider(BaseLLMProvider):
    """Bounded adapter for explicitly configured OpenAI-compatible endpoints."""

    provider_id = "openai-compatible"
    settings_prefix = ""

    def __init__(self, model: str | None = None):
        prefix = self.settings_prefix
        api_key = getattr(settings, f"{prefix}_API_KEY", "") or ""
        base_url = getattr(settings, f"{prefix}_BASE_URL", "") or ""
        resolved_model = model or getattr(settings, f"{prefix}_MODEL", "") or ""

        if not api_key or not base_url or not resolved_model:
            raise RuntimeError(
                f"{self.provider_id}: explicit API key, base URL and model are required"
            )
        if OpenAI is None:
            raise RuntimeError("openai package is required for compatible providers")

        self.model = resolved_model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=_TIMEOUT_SECONDS,
            max_retries=0,
        )

    @property
    def model_name(self) -> str:
        return self.model

    def _messages(self, system: str, user: str) -> list[dict]:
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def complete(self, system: str, user: str) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(system, user),
            max_tokens=_MAX_OUTPUT_TOKENS,
            timeout=_TIMEOUT_SECONDS,
        )
        return LLMResponse(
            content=response.choices[0].message.content or "",
            provider=self.model,
            usage=_usage_from_response(response),
        )

    def stream(self, system: str, user: str) -> Iterator[str]:
        with self.client.chat.completions.stream(
            model=self.model,
            messages=self._messages(system, user),
            max_tokens=_MAX_OUTPUT_TOKENS,
            timeout=_TIMEOUT_SECONDS,
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text


class DeepSeekProvider(OpenAICompatibleLowCostProvider):
    provider_id = "deepseek"
    settings_prefix = "DEEPSEEK"


class QwenProvider(OpenAICompatibleLowCostProvider):
    provider_id = "qwen"
    settings_prefix = "QWEN"
