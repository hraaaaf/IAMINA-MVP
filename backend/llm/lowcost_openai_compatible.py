import logging
import os
from typing import Iterator

from django.conf import settings

from .base import BaseLLMProvider, LLMResponse, LLMUsage
from .errors import normalize_provider_exception

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 15.0
_DEFAULT_MAX_OUTPUT_TOKENS = 160
_GPT_OSS_MAX_OUTPUT_TOKENS = 256

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


def _configured_value(prefix: str, suffix: str) -> str:
    setting_name = f"{prefix}_{suffix}"
    configured = getattr(settings, setting_name, "") or ""
    return configured or os.environ.get(setting_name, "") or ""


class OpenAICompatibleLowCostProvider(BaseLLMProvider):
    """Bounded adapter for explicitly configured OpenAI-compatible endpoints."""

    provider_id = "openai-compatible"
    settings_prefix = ""

    def __init__(
        self,
        model: str | None = None,
        *,
        provider_id: str | None = None,
        settings_prefix: str | None = None,
        default_base_url: str = "",
        default_model: str = "",
        timeout_seconds: float = _TIMEOUT_SECONDS,
        processor_policy_key: str | None = None,
    ):
        resolved_provider_id = provider_id or self.provider_id
        prefix = settings_prefix or self.settings_prefix
        api_key = _configured_value(prefix, "API_KEY")
        base_url = _configured_value(prefix, "BASE_URL") or default_base_url or ""
        resolved_model = (
            model
            or _configured_value(prefix, "MODEL")
            or default_model
            or ""
        )

        if not api_key or not base_url or not resolved_model:
            raise RuntimeError(
                f"{resolved_provider_id}: explicit API key, base URL and model are required"
            )
        if OpenAI is None:
            raise RuntimeError("openai package is required for compatible providers")
        if timeout_seconds <= 0:
            raise RuntimeError("OpenAI-compatible provider timeout must be positive")

        self.provider_id = resolved_provider_id
        self.provider_policy_key = processor_policy_key or resolved_provider_id
        self.settings_prefix = prefix
        self.model = resolved_model
        self.timeout_seconds = timeout_seconds
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=self.timeout_seconds,
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

    def _request_tuning(self) -> dict[str, str | int]:
        """Keep reasoning headroom bounded and isolated to GPT-OSS on Groq."""
        if self.provider_id == "groq" and self.model.startswith("openai/gpt-oss-"):
            return {
                "reasoning_effort": "low",
                "max_completion_tokens": _GPT_OSS_MAX_OUTPUT_TOKENS,
            }
        return {"max_tokens": _DEFAULT_MAX_OUTPUT_TOKENS}

    def complete(self, system: str, user: str) -> LLMResponse:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._messages(system, user),
                timeout=self.timeout_seconds,
                **self._request_tuning(),
            )
        except Exception as exc:
            raise normalize_provider_exception(exc, self.provider_id) from exc
        return LLMResponse(
            content=response.choices[0].message.content or "",
            provider=self.model,
            usage=_usage_from_response(response),
        )

    def stream(self, system: str, user: str) -> Iterator[str]:
        try:
            with self.client.chat.completions.stream(
                model=self.model,
                messages=self._messages(system, user),
                timeout=self.timeout_seconds,
                **self._request_tuning(),
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as exc:
            raise normalize_provider_exception(exc, self.provider_id) from exc


class DeepSeekProvider(OpenAICompatibleLowCostProvider):
    """Compatibility wrapper; runtime routing is registry-driven."""

    provider_id = "deepseek"
    settings_prefix = "DEEPSEEK"


class QwenProvider(OpenAICompatibleLowCostProvider):
    """Compatibility wrapper; runtime routing is registry-driven."""

    provider_id = "qwen"
    settings_prefix = "QWEN"
