"""
LLM Factory — provider resolution with Gemini rate-guard and failover chain.

Priority order (when LLM_PROVIDER = "gemini"):
  1. Gemini (guarded — cap at 18/day)
  2. Kimi   (if KIMI_API_KEY is set)
  3. FallbackProvider (static templates, always available)

Explicit overrides may select kimi, claude, deepseek or qwen. Every
network-capable provider returned by this module is decorated with the central
text payload contract and processor policy before it can perform egress.
"""
import logging
from collections.abc import Callable, Iterator
from typing import TypeVar

from django.conf import settings

from core.ai_egress import authorize_text_payload
from core.ai_processor_policy import authorize_processor_policy

from .base import BaseLLMProvider
from .errors import LLMProviderError, normalize_provider_exception

logger = logging.getLogger(__name__)
_T = TypeVar("_T")


def _get_fallback() -> BaseLLMProvider:
    from .fallback import FallbackProvider

    return FallbackProvider()


def _get_quota_exhausted() -> BaseLLMProvider:
    from .fallback import QuotaExhaustedProvider

    return QuotaExhaustedProvider()


def _get_kimi() -> BaseLLMProvider | None:
    kimi_key = getattr(settings, "KIMI_API_KEY", "") or ""
    if not kimi_key:
        return None
    try:
        from .kimi import KimiProvider

        return KimiProvider()
    except Exception:
        logger.warning("KimiProvider init failed — skipping.")
        return None


def _provider_policy_name(provider: BaseLLMProvider) -> str:
    cls = type(provider).__name__
    mapping = {
        "GeminiProvider": "gemini",
        "GuardedGeminiProvider": "gemini",
        "KimiProvider": "kimi",
        "ClaudeProvider": "claude",
        "DeepSeekProvider": "deepseek",
        "QwenProvider": "qwen",
        "QuotaExhaustedProvider": "quota-exhausted",
        "FallbackProvider": "fallback",
    }
    return mapping.get(cls, cls.lower())


def _execute_provider_call(
    provider_name: str,
    operation: str,
    call: Callable[[], _T],
) -> _T:
    try:
        return call()
    except LLMProviderError:
        raise
    except Exception as exc:
        normalized = normalize_provider_exception(exc, provider_name)
        logger.warning(
            "AI provider operation failed: provider=%s operation=%s code=%s retryable=%s",
            provider_name,
            operation,
            normalized.code,
            normalized.retryable,
        )
        raise normalized from None


def _enforce_text_payload_policy(provider: BaseLLMProvider) -> BaseLLMProvider:
    if getattr(provider, "_iamina_text_payload_policy", False) is True:
        return provider

    original_complete = provider.complete
    original_stream = provider.stream
    original_think = provider.think
    provider_name = _provider_policy_name(provider)

    def _authorize(system: str, user: str):
        payload = authorize_text_payload(
            {"system_prompt": system, "user_prompt": user}
        )
        authorize_processor_policy(provider_name, payload.purpose, "text")
        return payload

    def guarded_complete(system: str, user: str):
        payload = _authorize(system, user)
        return _execute_provider_call(
            provider_name,
            "complete",
            lambda: original_complete(payload.system_prompt, payload.user_prompt),
        )

    def guarded_stream(system: str, user: str) -> Iterator[str]:
        payload = _authorize(system, user)
        stream = original_stream(payload.system_prompt, payload.user_prompt)
        try:
            yield from stream
        except GeneratorExit:
            raise
        except LLMProviderError:
            raise
        except Exception as exc:
            normalized = normalize_provider_exception(exc, provider_name)
            logger.warning(
                "AI provider operation failed: provider=%s operation=stream code=%s retryable=%s",
                provider_name,
                normalized.code,
                normalized.retryable,
            )
            raise normalized from None
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()

    def guarded_think(system: str, user: str) -> tuple[str, str]:
        payload = _authorize(system, user)
        return _execute_provider_call(
            provider_name,
            "think",
            lambda: original_think(payload.system_prompt, payload.user_prompt),
        )

    provider.complete = guarded_complete  # type: ignore[method-assign]
    provider.stream = guarded_stream  # type: ignore[method-assign]
    provider.think = guarded_think  # type: ignore[method-assign]
    setattr(provider, "_iamina_text_payload_policy", True)
    return provider


def _build_gemini_with_failover() -> BaseLLMProvider:
    from .gemini import GeminiProvider
    from .rate_guard import GuardedGeminiProvider, should_use_gemini

    if not should_use_gemini():
        kimi = _get_kimi()
        if kimi:
            logger.info("LLM factory: Gemini cap hit — using Kimi.")
            return _enforce_text_payload_policy(kimi)
        logger.warning(
            "LLM factory: Gemini daily cap hit, no paid fallback — surfacing quota message."
        )
        return _enforce_text_payload_policy(_get_quota_exhausted())

    return _enforce_text_payload_policy(GuardedGeminiProvider(GeminiProvider()))


def get_ai_provider_name() -> str:
    return _provider_policy_name(get_llm())


def get_llm() -> BaseLLMProvider:
    provider = getattr(settings, "LLM_PROVIDER", "gemini")
    model = getattr(settings, "LLM_MODEL", None)

    if provider == "gemini":
        return _build_gemini_with_failover()

    if provider == "kimi":
        from .kimi import KimiProvider

        resolved = KimiProvider(model=model) if model else KimiProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "deepseek":
        from .lowcost_openai_compatible import DeepSeekProvider

        resolved = DeepSeekProvider(model=model) if model else DeepSeekProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "qwen":
        from .lowcost_openai_compatible import QwenProvider

        resolved = QwenProvider(model=model) if model else QwenProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "claude":
        from .claude import ClaudeProvider

        resolved = ClaudeProvider(model=model) if model else ClaudeProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "fallback":
        return _enforce_text_payload_policy(_get_fallback())

    logger.error("Unknown LLM_PROVIDER '%s' — using FallbackProvider.", provider)
    return _enforce_text_payload_policy(_get_fallback())
