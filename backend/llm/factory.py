"""
LLM Factory — provider resolution with Gemini rate-guard and failover chain.

Priority order (when LLM_PROVIDER = "gemini"):
  1. Gemini (guarded — cap at 18/day)
  2. Kimi   (if KIMI_API_KEY is set)
  3. FallbackProvider (static templates, always available)

Explicit overrides (LLM_PROVIDER = "kimi" | "claude") bypass the chain.
Every network-capable provider returned by this module is decorated with the
central text payload contract before it can perform egress.
"""
import logging
from collections.abc import Iterator
from typing import Any

from django.conf import settings

from core.ai_egress import authorize_text_payload

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


def _get_fallback() -> BaseLLMProvider:
    from .fallback import FallbackProvider
    return FallbackProvider()


def _get_quota_exhausted() -> BaseLLMProvider:
    from .fallback import QuotaExhaustedProvider
    return QuotaExhaustedProvider()


def _get_kimi() -> BaseLLMProvider | None:
    """Returns KimiProvider if KIMI_API_KEY is configured, else None."""
    kimi_key = getattr(settings, "KIMI_API_KEY", "") or ""
    if not kimi_key:
        return None
    try:
        from .kimi import KimiProvider
        return KimiProvider()
    except Exception:
        logger.warning("KimiProvider init failed — skipping.")
        return None


def _enforce_text_payload_policy(provider: BaseLLMProvider) -> BaseLLMProvider:
    """Decorate one provider instance without changing its concrete type.

    Keeping the original concrete instance preserves rate guards, failover checks,
    provider-name reporting and existing interface tests. Authorization happens
    before the original complete/stream/think method can touch the network.
    """
    if getattr(provider, "_iamina_text_payload_policy", False):
        return provider

    original_complete = provider.complete
    original_stream = provider.stream
    original_think = provider.think

    def guarded_complete(system: str, user: str):
        payload = authorize_text_payload(
            {"system_prompt": system, "user_prompt": user}
        )
        return original_complete(payload.system_prompt, payload.user_prompt)

    def guarded_stream(system: str, user: str) -> Iterator[str]:
        payload = authorize_text_payload(
            {"system_prompt": system, "user_prompt": user}
        )
        yield from original_stream(payload.system_prompt, payload.user_prompt)

    def guarded_think(system: str, user: str) -> tuple[str, str]:
        payload = authorize_text_payload(
            {"system_prompt": system, "user_prompt": user}
        )
        return original_think(payload.system_prompt, payload.user_prompt)

    provider.complete = guarded_complete  # type: ignore[method-assign]
    provider.stream = guarded_stream  # type: ignore[method-assign]
    provider.think = guarded_think  # type: ignore[method-assign]
    setattr(provider, "_iamina_text_payload_policy", True)
    return provider


def _build_gemini_with_failover() -> BaseLLMProvider:
    """Guarded Gemini → Kimi → FallbackProvider chain."""
    from .gemini import GeminiProvider
    from .rate_guard import GuardedGeminiProvider, should_use_gemini

    # Fast path: already at cap, skip Gemini instantiation entirely
    if not should_use_gemini():
        kimi = _get_kimi()
        if kimi:
            logger.info("LLM factory: Gemini cap hit — using Kimi.")
            return _enforce_text_payload_policy(kimi)
        logger.warning("LLM factory: Gemini daily cap hit, no paid fallback — surfacing quota message.")
        return _get_quota_exhausted()

    return _enforce_text_payload_policy(GuardedGeminiProvider(GeminiProvider()))


def get_ai_provider_name() -> str:
    """
    Returns the name of the currently active LLM provider.
    Used by the summary endpoint to surface degraded-mode status to the client.
    """
    provider = get_llm()
    cls = type(provider).__name__
    _map = {
        "GeminiProvider":         "gemini",
        "GuardedGeminiProvider":  "gemini",
        "KimiProvider":           "kimi",
        "ClaudeProvider":         "claude",
        "QuotaExhaustedProvider": "quota-exhausted",
        "FallbackProvider":       "fallback",
    }
    return _map.get(cls, cls.lower())


def get_llm() -> BaseLLMProvider:
    """
    Resolve the active LLM provider.
    LLM_PROVIDER in settings overrides the default chain.
    """
    provider = getattr(settings, "LLM_PROVIDER", "gemini")
    model = getattr(settings, "LLM_MODEL", None)

    if provider == "gemini":
        return _build_gemini_with_failover()

    if provider == "kimi":
        from .kimi import KimiProvider
        resolved = KimiProvider(model=model) if model else KimiProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "claude":
        from .claude import ClaudeProvider
        resolved = ClaudeProvider(model=model) if model else ClaudeProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "fallback":
        return _get_fallback()

    logger.error("Unknown LLM_PROVIDER '%s' — using FallbackProvider.", provider)
    return _get_fallback()
