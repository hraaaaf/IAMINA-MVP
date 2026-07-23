"""
Unit tests for LLMPipeline and middleware infrastructure.

T1 — LLMPipeline is an instance of BaseLLMProvider
T2 — LoggingMiddleware is called exactly once during complete()
T3 — Two middlewares execute in correct order (M1 before M2)
T4 — Exception raised by the provider propagates through the pipeline
T5 — PHIPseudonymizer.mask() strips last_name when calibrated
T6 — PHIPseudonymizer.mask() strips Moroccan CIN pattern
T7 — PHIStrippingMiddleware.process() raises PHILeakError on CIN in user prompt
"""
import pytest

from llm.base import BaseLLMProvider, LLMResponse
from llm.fallback import FallbackProvider
from llm.middleware.base import BaseLLMMiddleware
from llm.middleware.logging import LoggingMiddleware
from llm.middleware.phi_stripping import PHILeakError, PHIStrippingMiddleware
from llm.pipeline import LLMPipeline
from llm.pseudonymizer import PHIPseudonymizer

# ── Helpers ───────────────────────────────────────────────────────────────────

class _CountingMiddleware(BaseLLMMiddleware):
    """Records each invocation in self.calls."""

    def __init__(self, name: str, calls: list):
        self.name = name
        self.calls = calls

    def process(self, system, user, next_fn):
        self.calls.append(self.name)
        return next_fn(system, user)


class _RaisingProvider(BaseLLMProvider):
    """Provider that always raises ValueError."""

    def complete(self, system: str, user: str) -> LLMResponse:
        raise ValueError("test error")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_t1_pipeline_is_base_provider():
    """T1: LLMPipeline instanciated with FallbackProvider is an instance of BaseLLMProvider."""
    pipeline = LLMPipeline(FallbackProvider())
    assert isinstance(pipeline, BaseLLMProvider), (
        "LLMPipeline must inherit from BaseLLMProvider to be substitutable."
    )


def test_t2_logging_middleware_is_called():
    """T2: The middleware is called exactly once when complete() is invoked."""
    calls = []
    mock_mw = _CountingMiddleware("M", calls)
    pipeline = LLMPipeline(FallbackProvider(), [mock_mw])
    pipeline.complete("sys", "user")
    assert len(calls) == 1, f"Expected middleware called once, got {len(calls)} call(s)."


def test_t3_middleware_order():
    """T3: With middlewares [M1, M2], execution order must be M1 then M2."""
    calls: list[str] = []
    m1 = _CountingMiddleware("M1", calls)
    m2 = _CountingMiddleware("M2", calls)
    pipeline = LLMPipeline(FallbackProvider(), [m1, m2])
    pipeline.complete("sys", "user")
    assert calls == ["M1", "M2"], (
        f"Expected ['M1', 'M2'] but got {calls}. Check chain construction order."
    )


def test_t4_exception_propagates():
    """T4: An exception raised by the provider must propagate through the pipeline."""
    pipeline = LLMPipeline(_RaisingProvider(), [LoggingMiddleware()])
    with pytest.raises(ValueError, match="test error"):
        pipeline.complete("sys", "user")


# ── PHI Pseudonymizer + Middleware tests (P1.3) ───────────────────────────────

def test_t5_pseudonymizer_strips_last_name():
    """T5: PHIPseudonymizer.mask() replaces last_name when calibrate() is called with it."""
    pseudo = PHIPseudonymizer()
    pseudo.calibrate(last_name="Alaoui")
    result = pseudo.mask("Patient Alaoui needs help")
    assert "Alaoui" not in result, "last_name must be stripped from the masked text"
    assert "[REDACTED]" in result, "stripped name must be replaced with [REDACTED]"


def test_t6_pseudonymizer_strips_cin_pattern():
    """T6: PHIPseudonymizer.mask() strips Moroccan CIN patterns regardless of calibration."""
    pseudo = PHIPseudonymizer()
    result = pseudo.mask("CIN: AB12345 recorded")
    assert "AB12345" not in result, "Moroccan CIN must be stripped from the masked text"
    assert "[REDACTED]" in result, "stripped CIN must be replaced with [REDACTED]"


def test_t7_phi_stripping_middleware_raises_on_cin():
    """T7: PHIStrippingMiddleware.process() raises PHILeakError when CIN is in the user prompt."""
    middleware = PHIStrippingMiddleware()
    mock_next_called = []

    def mock_next(system, user):
        mock_next_called.append(True)
        return LLMResponse(content="response", provider="mock")

    with pytest.raises(PHILeakError):
        middleware.process("system prompt", "user CIN AB12345", mock_next)

    assert not mock_next_called, "next_fn must NOT be called when PHI is detected"
