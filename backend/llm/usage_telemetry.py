"""Privacy-safe cost/usage telemetry for governed AI workloads.

Events contain counts and routing metadata only. Patient identifiers, prompts,
responses, document text and exception messages are deliberately excluded.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from llm.base import LLMResponse

logger = logging.getLogger("iamina.cost")

_ALLOWED_WORKLOADS = frozenset(
    {
        "conversation",
        "summary",
        "writing",
        "proactive",
        "ocr",
        "vision",
        "stt",
        "tts",
        "evaluation",
        "unclassified",
    }
)
_ALLOWED_MEDIA_ACTIONS = frozenset({"uploaded", "retained", "deleted", "downloaded"})
_CURRENT_WORKLOAD: ContextVar[str] = ContextVar(
    "iamina_cost_workload",
    default="unclassified",
)


@contextmanager
def usage_workload_scope(workload: str) -> Iterator[str]:
    """Attach one non-sensitive workload class to nested provider telemetry."""
    if workload not in _ALLOWED_WORKLOADS or workload == "unclassified":
        raise ValueError(f"unsupported cost workload: {workload}")
    token = _CURRENT_WORKLOAD.set(workload)
    try:
        yield workload
    finally:
        _CURRENT_WORKLOAD.reset(token)


def current_usage_workload() -> str:
    return _CURRENT_WORKLOAD.get()


def _emit(event: dict[str, object]) -> None:
    logger.info(
        "cost_telemetry %s",
        json.dumps(event, sort_keys=True, separators=(",", ":")),
    )


def record_llm_success(
    response: LLMResponse,
    *,
    prompt_chars: int,
    latency_ms: float,
) -> None:
    """Record provider-reported LLM usage without recording any content."""
    usage = response.usage
    _emit(
        {
            "event": "llm_usage",
            "status": "success",
            "workload": current_usage_workload(),
            "provider_route": response.provider,
            "from_cache": bool(response.from_cache),
            "prompt_chars": max(prompt_chars, 0),
            "response_chars": len(response.content),
            "latency_ms": round(max(latency_ms, 0.0), 1),
            "input_tokens": usage.input_tokens if usage else None,
            "output_tokens": usage.output_tokens if usage else None,
            "cached_input_tokens": usage.cached_input_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
        }
    )


def record_llm_failure(
    *,
    prompt_chars: int,
    latency_ms: float,
    error_type: str,
) -> None:
    """Record a failed call without logging provider payload or exception text."""
    _emit(
        {
            "event": "llm_usage",
            "status": "error",
            "workload": current_usage_workload(),
            "prompt_chars": max(prompt_chars, 0),
            "latency_ms": round(max(latency_ms, 0.0), 1),
            "error_type": error_type,
        }
    )


def record_metered_usage(
    *,
    modality: str,
    unit: str,
    quantity: int,
    provider_route: str,
    latency_ms: float | None = None,
    status: str = "success",
    error_type: str | None = None,
) -> None:
    """Record OCR/audio/image metering without media content or patient identity."""
    if modality not in {"ocr", "vision", "stt", "tts"}:
        raise ValueError(f"unsupported metered modality: {modality}")
    if not unit.strip() or quantity < 0 or not provider_route.strip():
        raise ValueError("unit/provider_route are required and quantity cannot be negative")
    if status not in {"success", "error"}:
        raise ValueError("status must be success or error")
    event: dict[str, object] = {
        "event": "metered_usage",
        "status": status,
        "workload": current_usage_workload(),
        "modality": modality,
        "unit": unit,
        "quantity": quantity,
        "provider_route": provider_route,
    }
    if latency_ms is not None:
        event["latency_ms"] = round(max(latency_ms, 0.0), 1)
    if error_type is not None:
        event["error_type"] = error_type
    _emit(event)


def record_media_bytes(*, action: str, byte_count: int, retention_class: str) -> None:
    """Record raw-media byte lifecycle without object keys, names or hashes."""
    if action not in _ALLOWED_MEDIA_ACTIONS:
        raise ValueError(f"unsupported media action: {action}")
    if byte_count < 0:
        raise ValueError("byte_count cannot be negative")
    if not retention_class.strip():
        raise ValueError("retention_class is required")
    _emit(
        {
            "event": "media_bytes",
            "action": action,
            "workload": current_usage_workload(),
            "bytes": byte_count,
            "retention_class": retention_class,
        }
    )
