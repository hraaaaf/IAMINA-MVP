"""
LLM Factory — provider resolution with fail-closed processor and FinOps guards.

Network providers are never selected implicitly from API-key presence. Explicit
selection still requires patient egress authorization, an approved processor
policy and complete persistent FinOps configuration before any paid text call.
"""
from __future__ import annotations

import importlib
import logging
from collections.abc import Callable, Iterator
from typing import TypeVar

from django.conf import settings
from django.utils import timezone

from core.ai_egress import TEXT, assert_ai_egress_allowed, authorize_text_payload
from core.ai_operation_identity import next_operation_reference
from core.ai_processor_policy import authorize_processor_policy

from .base import BaseLLMProvider
from .errors import (
    LLMProviderError,
    LLMProviderQuotaExceeded,
    normalize_provider_exception,
)
from .runtime_finops import RuntimeFinOpsConfigurationError
from .usage_telemetry import current_usage_workload

logger = logging.getLogger(__name__)
_T = TypeVar("_T")


def _get_fallback() -> BaseLLMProvider:
    from .fallback import FallbackProvider

    return FallbackProvider()


def _get_quota_exhausted() -> BaseLLMProvider:
    from .fallback import QuotaExhaustedProvider

    return QuotaExhaustedProvider()


def _provider_policy_name(provider: BaseLLMProvider) -> str:
    explicit = getattr(provider, "provider_policy_key", None)
    if isinstance(explicit, str) and explicit.strip():
        return explicit

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


def _provider_model_name(provider: BaseLLMProvider) -> str:
    for attribute in ("model_name", "model"):
        value = getattr(provider, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise RuntimeFinOpsConfigurationError(
        "external paid provider must expose a stable model name"
    )


def _provider_output_ceiling(provider: BaseLLMProvider) -> int:
    value = getattr(provider, "max_output_tokens", None)
    if value is None:
        module = importlib.import_module(type(provider).__module__)
        value = getattr(module, "_MAX_OUTPUT_TOKENS", None)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RuntimeFinOpsConfigurationError(
            "external paid provider must expose a positive output token ceiling"
        )
    return value


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


def _execute_external_complete(
    *,
    provider: BaseLLMProvider,
    provider_name: str,
    payload,
    original_complete,
):
    from .runtime_finops_config import load_runtime_text_binding

    workload = current_usage_workload()
    if workload == "unclassified":
        raise RuntimeFinOpsConfigurationError(
            "external paid AI requires an explicit governed workload"
        )

    context = assert_ai_egress_allowed(TEXT)
    operation_reference = next_operation_reference(
        patient_id=context.patient_id,
        purpose=context.purpose,
    )
    model = _provider_model_name(provider)
    output_ceiling = _provider_output_ceiling(provider)
    binding = load_runtime_text_binding(
        provider=provider_name,
        model=model,
        workload=workload,
    )
    if output_ceiling > binding.max_output_tokens:
        raise RuntimeFinOpsConfigurationError(
            "configured output reservation ceiling is below provider runtime ceiling"
        )

    input_upper_bound = max(
        1,
        len(payload.system_prompt.encode("utf-8"))
        + len(payload.user_prompt.encode("utf-8")),
    )
    if input_upper_bound > binding.max_input_tokens:
        raise RuntimeFinOpsConfigurationError(
            "authorized prompt exceeds configured conservative input ceiling"
        )

    now = timezone.now()
    try:
        response = binding.enforcer.execute_complete(
            provider=provider_name,
            model=model,
            workload=workload,
            operation_reference=operation_reference,
            month_key=now.strftime("%Y-%m"),
            now=now,
            max_input_tokens=input_upper_bound,
            max_output_tokens=output_ceiling,
            call=lambda: original_complete(
                payload.system_prompt,
                payload.user_prompt,
            ),
        )
    except LLMProviderQuotaExceeded:
        if provider_name != "gemini":
            raise
        from .rate_guard import _mark_cap_reached

        _mark_cap_reached()
        logger.warning(
            "Gemini quota failure recorded by persistent FinOps guard; "
            "serving local quota response."
        )
        return _get_quota_exhausted().complete(
            payload.system_prompt,
            payload.user_prompt,
        )

    if provider_name == "gemini":
        from .rate_guard import record_gemini_call

        record_gemini_call()
    return response


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
        policy = authorize_processor_policy(provider_name, payload.purpose, TEXT)
        return payload, policy

    def guarded_complete(system: str, user: str):
        payload, policy = _authorize(system, user)
        if not policy.external_egress:
            return _execute_provider_call(
                provider_name,
                "complete",
                lambda: original_complete(
                    payload.system_prompt,
                    payload.user_prompt,
                ),
            )
        return _execute_external_complete(
            provider=provider,
            provider_name=provider_name,
            payload=payload,
            original_complete=original_complete,
        )

    def guarded_stream(system: str, user: str) -> Iterator[str]:
        payload, policy = _authorize(system, user)
        if policy.external_egress:
            raise RuntimeFinOpsConfigurationError(
                "paid external streaming is blocked until usage reconciliation is governed"
            )

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
        payload, policy = _authorize(system, user)
        if policy.external_egress:
            raise RuntimeFinOpsConfigurationError(
                "paid external thinking is blocked until usage reconciliation is governed"
            )
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
    from .rate_guard import should_use_gemini

    if not should_use_gemini():
        logger.warning(
            "LLM factory: Gemini daily cap hit — using local quota response; "
            "implicit network failover is disabled."
        )
        return _enforce_text_payload_policy(_get_quota_exhausted())

    return _enforce_text_payload_policy(GeminiProvider())


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

    if provider in {"deepseek", "qwen", "groq"}:
        from .provider_registry import build_openai_compatible_provider

        resolved = build_openai_compatible_provider(provider, model=model)
        return _enforce_text_payload_policy(resolved)

    if provider == "claude":
        from .claude import ClaudeProvider

        resolved = ClaudeProvider(model=model) if model else ClaudeProvider()
        return _enforce_text_payload_policy(resolved)

    if provider == "fallback":
        return _enforce_text_payload_policy(_get_fallback())

    logger.error("Unknown LLM_PROVIDER '%s' — using FallbackProvider.", provider)
    return _enforce_text_payload_policy(_get_fallback())
