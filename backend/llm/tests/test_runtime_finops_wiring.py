import json
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.ai_egress import ai_egress_scope
from core.ai_operation_identity import ai_operation_request_scope
from core.models import (
    AIBudgetAccount,
    AIBudgetReservationRecord,
    AIProviderOperationAttempt,
    AIUserThrottleWindow,
    BasePatientProfile,
)
from llm.base import BaseLLMProvider, LLMResponse, LLMUsage
from llm.budget import BudgetExceeded
from llm.factory import _enforce_text_payload_policy
from llm.provider_guard import ProviderCircuitOpen
from llm.runtime_finops import RuntimeFinOpsConfigurationError
from llm.usage_telemetry import usage_workload_scope
from llm.user_abuse_throttle import UserAbuseThrottleExceeded


class SyntheticProvider(BaseLLMProvider):
    model_name = "synthetic-model"
    max_output_tokens = 20

    def __init__(self, outcomes=None):
        self.calls = 0
        self.stream_calls = 0
        self.think_calls = 0
        self.outcomes = list(outcomes or [])

    def complete(self, system: str, user: str) -> LLMResponse:
        self.calls += 1
        if self.outcomes:
            outcome = self.outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        return _success_response()

    def stream(self, system: str, user: str):
        self.stream_calls += 1
        yield "network"

    def think(self, system: str, user: str) -> tuple[str, str]:
        self.think_calls += 1
        return "hidden", "network"


class HTTPStatusError(RuntimeError):
    def __init__(self, status_code: int):
        super().__init__(f"synthetic HTTP {status_code}")
        self.status_code = status_code


@pytest.fixture
def consenting_patient(db):
    user = User.objects.create_user(username="finops-wiring-patient")
    BasePatientProfile.objects.update_or_create(
        patient=user,
        defaults={
            "date_of_birth": date(1990, 1, 1),
            "ai_consent_given_at": timezone.now(),
        },
    )
    return user


def _success_response(provider: str = "synthetic-model") -> LLMResponse:
    return LLMResponse(
        content="ok",
        provider=provider,
        usage=LLMUsage(
            input_tokens=4,
            output_tokens=2,
            cached_input_tokens=0,
            total_tokens=6,
        ),
    )


def _runtime_config(
    *,
    provider: str = "synthetic",
    model: str = "synthetic-model",
    workload_hard: int = 1_000,
    workload_soft: int = 800,
    failure_threshold: int = 2,
    review_due_on: date | None = None,
    user_max_requests: int = 100,
    user_window_seconds: int = 60,
) -> str:
    today = date.today()
    due = review_due_on or (today + timedelta(days=30))
    return json.dumps(
        {
            "global_budget": {
                "hard_limit_microusd": 10_000,
                "soft_alert_threshold_microusd": 9_000,
            },
            "provider_budgets": [
                {
                    "provider": provider,
                    "hard_limit_microusd": 5_000,
                    "soft_alert_threshold_microusd": 4_000,
                }
            ],
            "workload_budgets": [
                {
                    "provider": provider,
                    "workload": "conversation",
                    "hard_limit_microusd": workload_hard,
                    "soft_alert_threshold_microusd": min(
                        workload_soft,
                        workload_hard,
                    ),
                }
            ],
            "prices": [
                {
                    "provider": provider,
                    "model": model,
                    "currency": "USD",
                    "input_microusd_per_million": 1_000_000,
                    "cached_input_microusd_per_million": 500_000,
                    "output_microusd_per_million": 2_000_000,
                    "evidence_reference": "synthetic-controlled-price",
                    "verified_on": (today - timedelta(days=1)).isoformat(),
                    "review_due_on": due.isoformat(),
                }
            ],
            "call_limits": [
                {
                    "provider": provider,
                    "model": model,
                    "workload": "conversation",
                    "max_input_tokens": 1_000,
                    "max_output_tokens": 20,
                }
            ],
            "provider_failure_policies": [
                {
                    "provider": provider,
                    "max_attempts_per_operation": 2,
                    "failure_threshold": failure_threshold,
                    "circuit_cooldown_seconds": 60,
                    "in_flight_lease_seconds": 30,
                }
            ],
            "user_throttle": {
                "window_seconds": user_window_seconds,
                "max_requests": user_max_requests,
            },
            "max_single_reservation_microusd": 2_000,
        }
    )


def _configure(monkeypatch, **kwargs):
    monkeypatch.setenv("AI_FINOPS_RUNTIME_CONFIG_JSON", _runtime_config(**kwargs))
    monkeypatch.setenv(
        "AI_FINOPS_HMAC_KEY",
        "synthetic-runtime-hmac-key-material-32-bytes-plus",
    )


def _external_guard(provider, monkeypatch, *, provider_name="synthetic"):
    monkeypatch.setattr(
        "llm.factory._provider_policy_name",
        lambda _: provider_name,
    )
    monkeypatch.setattr(
        "llm.factory.authorize_processor_policy",
        lambda *args, **kwargs: SimpleNamespace(external_egress=True),
    )
    return _enforce_text_payload_policy(provider)


def _complete(
    guarded,
    patient,
    *,
    idempotency_key="request-1",
):
    with (
        ai_operation_request_scope(idempotency_key),
        ai_egress_scope(patient.id, "companion_chat", "text"),
        usage_workload_scope("conversation"),
    ):
        return guarded.complete("system", "bonjour")


@pytest.mark.django_db(transaction=True)
def test_external_provider_missing_finops_config_makes_zero_calls(
    consenting_patient,
    monkeypatch,
):
    monkeypatch.delenv("AI_FINOPS_RUNTIME_CONFIG_JSON", raising=False)
    monkeypatch.delenv("AI_FINOPS_HMAC_KEY", raising=False)
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with pytest.raises(RuntimeFinOpsConfigurationError, match="required"):
        _complete(guarded, consenting_patient)

    assert provider.calls == 0


@pytest.mark.django_db(transaction=True)
def test_stale_price_blocks_before_external_provider_call(
    consenting_patient,
    monkeypatch,
):
    _configure(
        monkeypatch,
        review_due_on=date.today() - timedelta(days=1),
    )
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with pytest.raises(Exception) as caught:
        _complete(guarded, consenting_patient)

    assert type(caught.value).__name__ == "PricingUnavailable"
    assert provider.calls == 0


@pytest.mark.django_db(transaction=True)
def test_non_object_call_limit_config_fails_closed_before_provider(
    consenting_patient,
    monkeypatch,
):
    config = json.loads(_runtime_config())
    config["call_limits"].append("malformed-entry")
    monkeypatch.setenv("AI_FINOPS_RUNTIME_CONFIG_JSON", json.dumps(config))
    monkeypatch.setenv(
        "AI_FINOPS_HMAC_KEY",
        "synthetic-runtime-hmac-key-material-32-bytes-plus",
    )
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with pytest.raises(RuntimeFinOpsConfigurationError, match="call_limit must be an object"):
        _complete(guarded, consenting_patient)

    assert provider.calls == 0


@pytest.mark.django_db(transaction=True)
def test_controlled_external_complete_settles_persistent_hierarchy(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch)
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    response = _complete(guarded, consenting_patient)

    assert response.content == "ok"
    assert provider.calls == 1
    month = timezone.now().strftime("%Y-%m")
    assert AIBudgetAccount.objects.get(
        subject_key="finops:global",
        month_key=month,
    ).committed_microusd == 8
    assert AIBudgetAccount.objects.get(
        subject_key="finops:provider:synthetic",
        month_key=month,
    ).committed_microusd == 8
    assert AIBudgetAccount.objects.get(
        subject_key="finops:workload:synthetic:conversation",
        month_key=month,
    ).committed_microusd == 8


@pytest.mark.django_db(transaction=True)
def test_user_throttle_blocks_paid_external_calls_and_persists_only_hmac(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch, user_max_requests=2, user_window_seconds=3600)
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    _complete(guarded, consenting_patient, idempotency_key="throttle-1")
    _complete(guarded, consenting_patient, idempotency_key="throttle-2")
    with pytest.raises(UserAbuseThrottleExceeded):
        _complete(guarded, consenting_patient, idempotency_key="throttle-3")

    assert provider.calls == 2
    row = AIUserThrottleWindow.objects.get()
    assert row.request_count == 2
    assert row.subject_key.startswith("hmac256:")
    assert len(row.subject_key) == 72
    assert "patient" not in row.subject_key


@pytest.mark.django_db(transaction=True)
def test_hard_budget_denial_rewinds_attempt_and_makes_zero_provider_calls(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch, workload_hard=10, workload_soft=5)
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with pytest.raises(BudgetExceeded):
        _complete(guarded, consenting_patient)

    assert provider.calls == 0
    attempt = AIProviderOperationAttempt.objects.get(provider="synthetic")
    assert attempt.attempt_count == 0
    assert attempt.active_attempt_number is None


@pytest.mark.django_db(transaction=True)
def test_same_idempotency_retry_after_timeout_reuses_budget_reservation(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch, failure_threshold=2)
    provider = SyntheticProvider(
        [TimeoutError("private timeout detail"), _success_response()]
    )
    guarded = _external_guard(provider, monkeypatch)

    with pytest.raises(Exception) as caught:
        _complete(guarded, consenting_patient, idempotency_key="same-retry")
    assert type(caught.value).__name__ == "LLMProviderTimeout"

    reservations_before = set(
        AIBudgetReservationRecord.objects.values_list("reservation_id", flat=True)
    )
    committed_before = AIBudgetAccount.objects.get(
        subject_key="finops:global",
    ).committed_microusd
    assert committed_before > 8

    response = _complete(
        guarded,
        consenting_patient,
        idempotency_key="same-retry",
    )

    assert response.content == "ok"
    assert provider.calls == 2
    assert set(
        AIBudgetReservationRecord.objects.values_list("reservation_id", flat=True)
    ) == reservations_before
    assert AIBudgetAccount.objects.get(
        subject_key="finops:global",
    ).committed_microusd == 8


@pytest.mark.django_db(transaction=True)
def test_open_circuit_blocks_next_operation_before_provider(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch, failure_threshold=1)
    provider = SyntheticProvider([TimeoutError("timeout")])
    guarded = _external_guard(provider, monkeypatch)

    with pytest.raises(Exception):
        _complete(guarded, consenting_patient, idempotency_key="first")

    with pytest.raises(ProviderCircuitOpen):
        _complete(guarded, consenting_patient, idempotency_key="second")

    assert provider.calls == 1


@pytest.mark.django_db(transaction=True)
def test_unclassified_workload_blocks_external_provider_before_config_or_network(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch)
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with (
        ai_operation_request_scope("request-1"),
        ai_egress_scope(consenting_patient.id, "companion_chat", "text"),
    ):
        with pytest.raises(RuntimeFinOpsConfigurationError, match="workload"):
            guarded.complete("system", "bonjour")

    assert provider.calls == 0


@pytest.mark.django_db
def test_external_stream_and_think_are_fail_closed(
    consenting_patient,
    monkeypatch,
):
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with ai_egress_scope(consenting_patient.id, "companion_chat", "text"):
        with pytest.raises(RuntimeFinOpsConfigurationError, match="streaming"):
            next(guarded.stream("system", "bonjour"))
        with pytest.raises(RuntimeFinOpsConfigurationError, match="thinking"):
            guarded.think("system", "bonjour")

    assert provider.stream_calls == 0
    assert provider.think_calls == 0


@pytest.mark.django_db
def test_local_fallback_remains_available_without_finops_config(
    consenting_patient,
    monkeypatch,
):
    monkeypatch.delenv("AI_FINOPS_RUNTIME_CONFIG_JSON", raising=False)
    monkeypatch.delenv("AI_FINOPS_HMAC_KEY", raising=False)

    from llm.fallback import FallbackProvider

    guarded = _enforce_text_payload_policy(FallbackProvider())
    with ai_egress_scope(consenting_patient.id, "companion_chat", "text"):
        response = guarded.complete("system", "bonjour")

    assert response.provider == "fallback-v1"
    assert not AIUserThrottleWindow.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_gemini_429_is_recorded_before_local_quota_response(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch, provider="gemini")
    provider = SyntheticProvider([HTTPStatusError(429)])
    guarded = _external_guard(provider, monkeypatch, provider_name="gemini")
    mark_cap = MagicMock()
    monkeypatch.setattr("llm.rate_guard._mark_cap_reached", mark_cap)

    response = _complete(guarded, consenting_patient)

    assert response.provider == "quota-exhausted"
    assert provider.calls == 1
    mark_cap.assert_called_once_with()
    attempt = AIProviderOperationAttempt.objects.get(provider="gemini")
    assert attempt.last_error_code == "provider_quota_exceeded"
    assert AIBudgetAccount.objects.get(
        subject_key="finops:provider:gemini",
    ).committed_microusd > 0


@pytest.mark.django_db(transaction=True)
def test_persisted_keys_never_contain_raw_client_or_patient_identity(
    consenting_patient,
    monkeypatch,
):
    _configure(monkeypatch)
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)
    raw_key = "opaque-client-retry-42"

    _complete(guarded, consenting_patient, idempotency_key=raw_key)

    persisted = [
        value
        for value in AIBudgetReservationRecord.objects.values_list(
            "idempotency_key",
            flat=True,
        )
        if value
    ]
    persisted += list(
        AIProviderOperationAttempt.objects.values_list(
            "operation_key",
            flat=True,
        )
    )
    persisted += list(AIUserThrottleWindow.objects.values_list("subject_key", flat=True))
    assert persisted
    assert all(value.startswith("hmac256:") for value in persisted)
    assert all(raw_key not in value for value in persisted)
    assert all("patient=" not in value for value in persisted)
    assert all("request=" not in value for value in persisted)


@pytest.mark.django_db(transaction=True)
def test_soft_budget_alert_is_privacy_safe(
    consenting_patient,
    monkeypatch,
    caplog,
):
    config = json.loads(_runtime_config())
    config["global_budget"]["soft_alert_threshold_microusd"] = 1
    config["provider_budgets"][0]["soft_alert_threshold_microusd"] = 1
    config["workload_budgets"][0]["soft_alert_threshold_microusd"] = 1
    monkeypatch.setenv("AI_FINOPS_RUNTIME_CONFIG_JSON", json.dumps(config))
    monkeypatch.setenv(
        "AI_FINOPS_HMAC_KEY",
        "synthetic-runtime-hmac-key-material-32-bytes-plus",
    )
    provider = SyntheticProvider()
    guarded = _external_guard(provider, monkeypatch)

    with caplog.at_level("WARNING", logger="iamina.cost"):
        _complete(
            guarded,
            consenting_patient,
            idempotency_key="private-client-key",
        )

    messages = [record.getMessage() for record in caplog.records]
    alert = next(message for message in messages if "soft_budget_alert" in message)
    assert "provider=synthetic" in alert
    assert "workload=conversation" in alert
    assert "private-client-key" not in alert
    assert f"patient={consenting_patient.id}" not in alert
