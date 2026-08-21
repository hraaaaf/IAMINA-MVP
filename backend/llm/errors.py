"""Stable, non-sensitive failures emitted by the IAmina provider boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class LLMProviderError(RuntimeError):
    """Base error safe to map to a stable API response.

    Raw SDK exception messages must not cross the provider boundary because they
    may contain request metadata or vendor-specific implementation details.
    """

    provider: str
    code: str
    retryable: bool
    safe_message: str

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.safe_message)


class LLMProviderTimeout(LLMProviderError):
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            code="provider_timeout",
            retryable=True,
            safe_message="The AI service did not respond in time.",
        )


class LLMProviderUnavailable(LLMProviderError):
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            code="provider_unavailable",
            retryable=True,
            safe_message="The AI service is temporarily unavailable.",
        )


class LLMProviderQuotaExceeded(LLMProviderError):
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            code="provider_quota_exceeded",
            retryable=False,
            safe_message="The AI service quota is currently exhausted.",
        )


class LLMProviderMalformedResponse(LLMProviderError):
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            code="provider_malformed_response",
            retryable=True,
            safe_message="The AI service returned an invalid response.",
        )


class LLMProviderInternalFailure(LLMProviderError):
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            code="provider_internal_failure",
            retryable=False,
            safe_message="The AI request could not be completed safely.",
        )


def normalize_provider_exception(exc: Exception, provider: str) -> LLMProviderError:
    """Convert SDK-specific exceptions into the stable IAmina taxonomy."""
    if isinstance(exc, LLMProviderError):
        return exc
    if isinstance(exc, TimeoutError):
        return LLMProviderTimeout(provider)
    if isinstance(exc, ConnectionError):
        return LLMProviderUnavailable(provider)

    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return LLMProviderQuotaExceeded(provider)
    if isinstance(status_code, int) and 500 <= status_code <= 599:
        return LLMProviderUnavailable(provider)

    class_name = type(exc).__name__.lower()
    if "timeout" in class_name:
        return LLMProviderTimeout(provider)
    if any(token in class_name for token in ("connection", "unavailable", "serviceunavailable")):
        return LLMProviderUnavailable(provider)
    if any(token in class_name for token in ("ratelimit", "quota", "resourceexhausted")):
        return LLMProviderQuotaExceeded(provider)

    return LLMProviderInternalFailure(provider)
