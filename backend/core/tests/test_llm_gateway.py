"""
Tests for core/llm_gateway.py — narrate() gateway function.

Three unit tests (all mocked — no real LLM calls):
  T1: narrate() returns a string.
  T2: PHIStrippingMiddleware is in the pipeline middlewares.
  T3: pseudonymizer.mask() is called at least twice before LLM response.
"""
from unittest.mock import MagicMock, call, patch

import pytest

from core.contracts.companion_identity import CompanionIdentity
from core.contracts.domain_context import DomainContext
from core.contracts.patient_context import ModulePatientContext
from llm.base import LLMResponse

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def patient_ctx():
    return ModulePatientContext(
        patient_id=1,
        language="fr",
        region="MA",
        consent_flags={"ai_analysis": True},
    )


@pytest.fixture
def domain_ctx():
    return DomainContext(
        kpi_summary={"tir_pct": 68.2, "gmi": 7.1},
        detected_patterns=["dawn_phenomenon"],
        insights=["Patient shows consistent dawn phenomenon over 7 days."],
        pivot_text="Patient glucose stable with mild dawn effect.",
        language="fr",
    )


@pytest.fixture
def companion_id():
    return CompanionIdentity(
        companion_name="IAmina",
        domain_description="diabetes management",
        unit="mg/dL",
    )


# ── T1: narrate() returns a string ────────────────────────────────────────────

@pytest.mark.django_db
def test_narrate_returns_string(patient_ctx, domain_ctx, companion_id):
    """narrate() must return a plain str even when the provider is mocked."""
    fake_response = LLMResponse(content="Voici votre résumé.", provider="mock")

    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.model_name = "mock"

    with patch("core.llm_gateway.get_llm", return_value=mock_provider):
        from core.llm_gateway import narrate
        result = narrate(patient_ctx, domain_ctx, companion_id, "fr")

    assert isinstance(result, str)
    assert len(result) > 0


# ── T2: PHIStrippingMiddleware is in the pipeline ─────────────────────────────

@pytest.mark.django_db
def test_phi_stripping_middleware_in_pipeline(patient_ctx, domain_ctx, companion_id):
    """PHIStrippingMiddleware must be included in the LLMPipeline middlewares list."""
    from llm.middleware.phi_stripping import PHIStrippingMiddleware

    captured_middlewares = []
    fake_response = LLMResponse(content="ok", provider="mock")

    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.model_name = "mock"

    original_pipeline_init = __import__(
        "llm.pipeline", fromlist=["LLMPipeline"]
    ).LLMPipeline.__init__

    def capturing_init(self, inner, middlewares=None):
        captured_middlewares.extend(middlewares or [])
        original_pipeline_init(self, inner, middlewares)

    with patch("core.llm_gateway.get_llm", return_value=mock_provider):
        with patch("core.llm_gateway.LLMPipeline.__init__", capturing_init):
            from core.llm_gateway import narrate
            try:
                narrate(patient_ctx, domain_ctx, companion_id, "fr")
            except Exception:
                pass  # pipeline may fail without full provider — we only need captured_middlewares

    assert any(
        isinstance(m, PHIStrippingMiddleware) for m in captured_middlewares
    ), "PHIStrippingMiddleware must be in the LLMPipeline middlewares"


# ── T3: pseudonymizer.mask() called at least twice before LLM ─────────────────

@pytest.mark.django_db
def test_mask_called_before_llm(patient_ctx, domain_ctx, companion_id):
    """PHIPseudonymizer.mask() must be called at least twice (system + user prompts)."""
    fake_response = LLMResponse(content="réponse", provider="mock")

    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.model_name = "mock"

    mask_call_count = 0
    complete_call_count = 0

    original_mask = __import__(
        "llm.pseudonymizer", fromlist=["PHIPseudonymizer"]
    ).PHIPseudonymizer.mask

    def tracking_mask(self, text):
        nonlocal mask_call_count
        mask_call_count += 1
        return original_mask(self, text)

    def tracking_complete(system, user):
        nonlocal complete_call_count
        # At point of LLM call, mask must already have been called >= 2 times
        assert mask_call_count >= 2, (
            f"mask() must be called before LLM complete(), but was called {mask_call_count} times"
        )
        complete_call_count += 1
        return fake_response

    mock_provider.complete.side_effect = tracking_complete

    with patch("core.llm_gateway.get_llm", return_value=mock_provider):
        with patch("llm.pseudonymizer.PHIPseudonymizer.mask", tracking_mask):
            from core.llm_gateway import narrate
            narrate(patient_ctx, domain_ctx, companion_id, "fr")

    assert mask_call_count >= 2, f"Expected mask() called >= 2 times, got {mask_call_count}"
    assert complete_call_count == 1, "LLM complete() must be called exactly once"
