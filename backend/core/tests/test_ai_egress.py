"""P0 tests for the central patient AI egress authorization boundary."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.ai_egress import (
    AUDIO,
    IMAGE,
    TEXT,
    AIConsentRequired,
    AIEgressDenied,
    ai_egress_scope,
    assert_ai_egress_allowed,
    patient_ai_egress_scope,
)
from core.models import BasePatientProfile


@pytest.fixture
def patient(db):
    user = User.objects.create_user(username="egress-patient")
    BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 1, 1),
    )
    return user


def test_no_scope_is_default_deny(db):
    with pytest.raises(AIEgressDenied, match="outside an authorized egress scope"):
        assert_ai_egress_allowed(TEXT)


def test_scope_is_lazy_and_does_not_block_deterministic_paths(patient):
    # Merely declaring that a route *may* use AI must not require consent. This
    # lets deterministic emergency/no-prescription paths return without egress.
    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        pass


def test_real_egress_requires_server_side_consent(patient):
    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        with pytest.raises(AIConsentRequired, match="Explicit patient AI consent"):
            assert_ai_egress_allowed(TEXT)


def test_real_egress_allowed_after_explicit_consent(patient):
    profile = patient.base_profile
    profile.ai_consent_given_at = timezone.now()
    profile.save(update_fields=["ai_consent_given_at"])

    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        context = assert_ai_egress_allowed(TEXT)

    assert context.patient_id == patient.id
    assert context.purpose == "companion_chat"


def test_modality_cannot_escape_declared_purpose(patient):
    profile = patient.base_profile
    profile.ai_consent_given_at = timezone.now()
    profile.save(update_fields=["ai_consent_given_at"])

    with ai_egress_scope(patient.id, "companion_chat", TEXT):
        with pytest.raises(AIEgressDenied, match="not authorized"):
            assert_ai_egress_allowed(IMAGE)


def test_unknown_purpose_is_denied_before_runtime(patient):
    with pytest.raises(AIEgressDenied, match="Unknown AI egress purpose"):
        with ai_egress_scope(patient.id, "unregistered-purpose", TEXT):
            pass


def test_gateway_blocks_provider_call_without_authorized_scope(db):
    provider = MagicMock()
    with patch("core.llm_gateway.get_llm", return_value=provider):
        from core.llm_gateway import GatewayLLM

        gateway = GatewayLLM()
        with pytest.raises(AIEgressDenied):
            gateway.complete("system", "user")

    provider.complete.assert_not_called()


def test_endpoint_decorator_only_declares_scope_until_egress(patient):
    request = SimpleNamespace(user=patient, auth=patient)

    @patient_ai_egress_scope("voice_chat", AUDIO, TEXT)
    def endpoint(req):
        # No assertion = no external model operation = no consent needed.
        return req.user.id

    assert endpoint(request) == patient.id
