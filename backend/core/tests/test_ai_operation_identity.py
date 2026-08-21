import pytest

from core.ai_operation_identity import (
    AIOperationIdentityDenied,
    ai_operation_request_scope,
    next_operation_reference,
)


def test_client_idempotency_key_is_stable_without_retaining_raw_value():
    raw = "retry-key-123"
    with ai_operation_request_scope(raw):
        first = next_operation_reference(patient_id=7, purpose="companion_chat")
    with ai_operation_request_scope(raw):
        retried = next_operation_reference(patient_id=7, purpose="companion_chat")

    assert first == retried
    assert raw not in first
    assert "client-sha256:" in first


def test_patient_purpose_and_call_index_partition_operation_identity():
    with ai_operation_request_scope("same-key"):
        first = next_operation_reference(patient_id=7, purpose="companion_chat")
        second = next_operation_reference(patient_id=7, purpose="companion_chat")
    with ai_operation_request_scope("same-key"):
        other_patient = next_operation_reference(
            patient_id=8,
            purpose="companion_chat",
        )
    with ai_operation_request_scope("same-key"):
        other_purpose = next_operation_reference(
            patient_id=7,
            purpose="clinical_summary",
        )

    assert first != second
    assert first != other_patient
    assert first != other_purpose


def test_missing_client_key_gets_unique_server_nonce():
    with ai_operation_request_scope(None):
        first = next_operation_reference(patient_id=7, purpose="companion_chat")
    with ai_operation_request_scope(None):
        second = next_operation_reference(patient_id=7, purpose="companion_chat")

    assert first != second
    assert "server-nonce:" in first


@pytest.mark.parametrize(
    "unsafe",
    [
        "contains spaces",
        "mail@example.test",
        "../path",
        "x" * 129,
    ],
)
def test_unsafe_client_idempotency_key_is_rejected(unsafe):
    with pytest.raises(AIOperationIdentityDenied):
        with ai_operation_request_scope(unsafe):
            pass


def test_operation_reference_requires_request_scope():
    with pytest.raises(AIOperationIdentityDenied, match="outside request identity"):
        next_operation_reference(patient_id=7, purpose="companion_chat")
