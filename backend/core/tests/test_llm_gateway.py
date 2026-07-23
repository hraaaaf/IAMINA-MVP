"""
Tests for core/llm_gateway.py — narrate() gateway function.

All provider calls run inside an explicitly authorized patient egress scope. The
separate ``test_ai_egress`` suite owns the default-deny/no-consent assertions.
"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.ai_egress import TEXT, ai_egress_scope
from core.contracts.companion_identity import CompanionIdentity
from core.contracts.domain_context import DomainContext
from core.contracts.patient_context import ModulePatientContext
from core.models import BasePatientProfile
from llm.base import LLMResponse


@pytest.fixture
def patient_ctx(db):
    user = User.objects.create_user(username="llm-gateway-patient")
    BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 1, 1),
        ai_consent_given_at=timezone.now(),
    )
    return ModulePatientContext(
        patient_id=user.id,
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


def _authorized_text_scope(patient_ctx):
    return ai_egress_scope(patient_ctx.patient_id, "clinical_summary", TEXT)


@pytest.mark.django_db
def test_narrate_returns_string(patient_ctx, domain_ctx, companion_id):
    """narrate() returns a plain string when policy and provider both authorize it."""
    fake_response = LLMResponse(content="Voici votre résumé.", provider="mock")
    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.model_name = "mock"

    with _authorized_text_scope(patient_ctx):
        with patch("core.llm_gateway.get_llm", return_value=mock_provider):
            from core.llm_gateway import narrate

            result = narrate(patient_ctx, domain_ctx, companion_id, "fr")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.django_db
def test_phi_stripping_middleware_in_pipeline(patient_ctx, domain_ctx, companion_id):
    """PHIStrippingMiddleware remains installed after the egress authorization gate."""
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

    with _authorized_text_scope(patient_ctx):
        with patch("core.llm_gateway.get_llm", return_value=mock_provider):
            with patch("core.llm_gateway.LLMPipeline.__init__", capturing_init):
                from core.llm_gateway import narrate

                narrate(patient_ctx, domain_ctx, companion_id, "fr")

    assert any(
        isinstance(middleware, PHIStrippingMiddleware)
        for middleware in captured_middlewares
    ), "PHIStrippingMiddleware must be in the LLMPipeline middlewares"


@pytest.mark.django_db
def test_mask_called_before_llm(patient_ctx, domain_ctx, companion_id):
    """PHIPseudonymizer.mask() runs before the provider receives either prompt."""
    fake_response = LLMResponse(content="réponse", provider="mock")
    mock_provider = MagicMock()
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
        assert mask_call_count >= 2, (
            "mask() must be called before LLM complete(), "
            f"but was called {mask_call_count} times"
        )
        complete_call_count += 1
        return fake_response

    mock_provider.complete.side_effect = tracking_complete

    with _authorized_text_scope(patient_ctx):
        with patch("core.llm_gateway.get_llm", return_value=mock_provider):
            with patch("llm.pseudonymizer.PHIPseudonymizer.mask", tracking_mask):
                from core.llm_gateway import narrate

                narrate(patient_ctx, domain_ctx, companion_id, "fr")

    assert mask_call_count >= 2, f"Expected mask() called >= 2 times, got {mask_call_count}"
    assert complete_call_count == 1, "LLM complete() must be called exactly once"
