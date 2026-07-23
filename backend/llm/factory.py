"""
LLM Factory — provider resolution with Gemini rate-guard and failover chain.

Priority order (when LLM_PROVIDER = "gemini"):
  1. Gemini (guarded — cap at 18/day)
  2. Kimi   (if KIMI_API_KEY is set)
  3. FallbackProvider (static templates, always available)

Explicit overrides (LLM_PROVIDER = "kimi" | "claude") bypass the chain.
"""
import logging

from django.conf import settings

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


def _build_gemini_with_failover() -> BaseLLMProvider:
    """Guarded Gemini → Kimi → FallbackProvider chain."""
    from .gemini import GeminiProvider
    from .rate_guard import GuardedGeminiProvider, should_use_gemini

    # Fast path: already at cap, skip Gemini instantiation entirely
    if not should_use_gemini():
        kimi = _get_kimi()
        if kimi:
            logger.info("LLM factory: Gemini cap hit — using Kimi.")
            return kimi
        logger.warning("LLM factory: Gemini daily cap hit, no paid fallback — surfacing quota message.")
        return _get_quota_exhausted()

    return GuardedGeminiProvider(GeminiProvider())


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
        return KimiProvider(model=model) if model else KimiProvider()

    if provider == "claude":
        from .claude import ClaudeProvider
        return ClaudeProvider(model=model) if model else ClaudeProvider()

    if provider == "fallback":
        return _get_fallback()

    logger.error("Unknown LLM_PROVIDER '%s' — using FallbackProvider.", provider)
    return _get_fallback()
