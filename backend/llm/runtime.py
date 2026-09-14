"""Central runtime boundary for non-text external provider operations."""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TypeVar

from core.ai_egress import assert_ai_egress_allowed
from core.ai_processor_policy import authorize_processor_policy

from .circuit_breaker import (
    assert_provider_available,
    record_provider_failure,
    record_provider_success,
)
from .errors import (
    LLMProviderError,
    LLMProviderTimeout,
    normalize_provider_exception,
)

logger = logging.getLogger(__name__)
_T = TypeVar("_T")
DEFAULT_MULTIMODAL_TIMEOUT_SECONDS = 20.0


def execute_external_provider_call(
    provider: str,
    modality: str,
    operation: str,
    call: Callable[[], _T],
    *,
    timeout_seconds: float = DEFAULT_MULTIMODAL_TIMEOUT_SECONDS,
) -> _T:
    """Authorize and execute one bounded external provider operation.

    Consent/scope and processor policy are checked before the callable starts.
    Vendor exceptions are normalized so raw SDK messages never cross this boundary.
    Repeated retryable provider failures share the same provider-scoped circuit
    breaker used by text calls, so audio/image paths also fail fast while a
    provider is known unhealthy.
    """
    context = assert_ai_egress_allowed(modality)
    authorize_processor_policy(provider, context.purpose, modality)
    assert_provider_available(provider)

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="iamina-provider")
    future = executor.submit(call)
    try:
        result = future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        future.cancel()
        normalized = LLMProviderTimeout(provider)
        record_provider_failure(provider, normalized)
        raise normalized from None
    except LLMProviderError as exc:
        record_provider_failure(provider, exc)
        raise
    except Exception as exc:
        normalized = normalize_provider_exception(exc, provider)
        record_provider_failure(provider, normalized)
        logger.warning(
            "External provider operation failed: provider=%s operation=%s code=%s retryable=%s",
            provider,
            operation,
            normalized.code,
            normalized.retryable,
        )
        raise normalized from None
    else:
        record_provider_success(provider)
        return result
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
