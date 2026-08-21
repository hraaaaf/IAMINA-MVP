from datetime import UTC, date, datetime, timedelta

import pytest

from core.models import AIProviderOperationAttempt
from llm.base import LLMResponse, LLMUsage
from llm.budget import BudgetExceeded
from llm.errors import (
    LLMProviderQuotaExceeded,
    LLMProviderTimeout,
    LLMProviderUnavailable,
)
from llm.hierarchical_budget import (
    BudgetThreshold,
    HierarchicalBudgetController,
    HierarchicalBudgetPolicy,
    derive_opaque_budget_operation_key,
)
from llm.persistent_budget import PersistentBudgetLedger
from llm.pricing import PricingRegistry, PricingUnavailable, TextTokenPrice
from llm.provider_guard import PersistentProviderFailureGuard, ProviderFailurePolicy
from llm.runtime_finops import PaidTextRuntimeEnforcer

pytestmark = pytest.mark.django_db(transaction=True)
_KEY_MATERIAL = b"frug8d-runtime-operation-key-material-32bytes-plus"
_NOW = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


class _SyntheticHTTPError(RuntimeError):
    def __init__(self, status_code: int):
        super().__init__("synthetic provider error")
        self.status_code = status_code


def _price(*, review_due_on: date = date(2026, 9, 19)) -> TextTokenPrice:
    return TextTokenPrice(
        provider="groq",
        model="synthetic-model",
        currency="USD",
        input_microusd_per_million=1_000_000,
        cached_input_microusd_per_million=500_000,
        output_microusd_per_million=2_000_000,
        evidence_reference="synthetic-controlled-price",
        verified_on=date(2026, 8, 20),
        review_due_on=review_due_on,
    )


def _policy(*, workload_hard_limit: int = 1_000) -> HierarchicalBudgetPolicy:
    return HierarchicalBudgetPolicy(
        global_budget=BudgetThreshold(
            hard_limit_microusd=10_000,
            soft_alert_threshold_microusd=9_000,
        ),
        provider_budgets={
            "groq": BudgetThreshold(
                hard_limit_microusd=5_000,
                soft_alert_threshold_microusd=4_000,
            )
        },
        workload_budgets={
            ("groq", "conversation"): BudgetThreshold(
                hard_limit_microusd=workload_hard_limit,
                soft_alert_threshold_microusd=min(900, workload_hard_limit),
            )
        },
        max_single_reservation_microusd=2_000,
    )


def _enforcer(
    *,
    workload_hard_limit: int = 1_000,
    review_due_on: date = date(2026, 9, 19),
) -> tuple[PaidTextRuntimeEnforcer, PersistentBudgetLedger]:
    ledger = PersistentBudgetLedger()
    budget = HierarchicalBudgetController(
        policy=_policy(workload_hard_limit=workload_hard_limit),
        ledger=ledger,
    )
    guard = PersistentProviderFailureGuard(
        ProviderFailurePolicy(
            max_attempts_per_operation=2,
            failure_threshold=2,
            circuit_cooldown_seconds=60,
            in_flight_lease_seconds=30,
        )
    )
    return (
        PaidTextRuntimeEnforcer(
            budget=budget,
            pricing=PricingRegistry((_price(review_due_on=review_due_on),)),
            provider_guard=guard,
            operation_key_material=_KEY_MATERIAL,
        ),
        ledger,
    )


def _operation_key(reference: str) -> str:
    return derive_opaque_budget_operation_key(
        key_material=_KEY_MATERIAL,
        operation_reference=(
            "provider=groq|model=synthetic-model|workload=conversation|"
            f"operation={reference}"
        ),
    )


def _execute(enforcer: PaidTextRuntimeEnforcer, reference: str, call, *, now=_NOW):
    return enforcer.execute_complete(
        provider="groq",
        model="synthetic-model",
        workload="conversation",
        operation_reference=reference,
        month_key="2026-08",
        now=now,
        max_input_tokens=100,
        max_output_tokens=20,
        call=call,
    )


def test_success_settles_from_provider_reported_usage_only():
    enforcer, ledger = _enforcer()
    calls = 0

    def call():
        nonlocal calls
        calls += 1
        return LLMResponse(
            content="ok",
            provider="groq",
            usage=LLMUsage(
                input_tokens=10,
                output_tokens=5,
                cached_input_tokens=0,
                total_tokens=15,
            ),
        )

    response = _execute(enforcer, "request-1", call)

    assert response.content == "ok"
    assert calls == 1
    assert ledger.committed_microusd("finops:global", "2026-08") == 20
    state = AIProviderOperationAttempt.objects.get(
        provider="groq",
        operation_key=_operation_key("request-1"),
    )
    assert state.attempt_count == 1
    assert state.completed_at is not None


def test_budget_denial_rewinds_attempt_before_provider_call():
    enforcer, ledger = _enforcer(workload_hard_limit=100)
    calls = 0

    def call():
        nonlocal calls
        calls += 1
        return LLMResponse(content="never", provider="groq")

    with pytest.raises(BudgetExceeded, match="workload"):
        _execute(enforcer, "request-budget-denied", call)

    assert calls == 0
    assert ledger.committed_microusd("finops:global", "2026-08") == 0
    state = AIProviderOperationAttempt.objects.get(
        provider="groq",
        operation_key=_operation_key("request-budget-denied"),
    )
    assert state.attempt_count == 0
    assert state.active_attempt_number is None
    assert state.in_flight_until is None


def test_stale_pricing_fails_before_attempt_budget_or_provider():
    enforcer, ledger = _enforcer(review_due_on=date(2026, 8, 20))
    calls = 0

    def call():
        nonlocal calls
        calls += 1
        return LLMResponse(content="never", provider="groq")

    with pytest.raises(PricingUnavailable, match="stale"):
        _execute(enforcer, "request-stale-price", call)

    assert calls == 0
    assert ledger.committed_microusd("finops:global", "2026-08") == 0
    assert not AIProviderOperationAttempt.objects.filter(provider="groq").exists()


def test_provider_timeout_keeps_worst_case_reservation_for_reconciliation():
    enforcer, ledger = _enforcer()
    calls = 0

    def call():
        nonlocal calls
        calls += 1
        raise TimeoutError("synthetic provider timeout")

    with pytest.raises(LLMProviderTimeout):
        _execute(enforcer, "request-timeout", call)

    assert calls == 1
    assert ledger.committed_microusd("finops:global", "2026-08") == 140
    state = AIProviderOperationAttempt.objects.get(
        provider="groq",
        operation_key=_operation_key("request-timeout"),
    )
    assert state.attempt_count == 1
    assert state.last_error_code == "provider_timeout"
    assert state.completed_at is None


@pytest.mark.parametrize(
    ("status_code", "expected_error", "expected_code"),
    (
        (429, LLMProviderQuotaExceeded, "provider_quota_exceeded"),
        (503, LLMProviderUnavailable, "provider_unavailable"),
    ),
)
def test_http_failures_keep_worst_case_reservation_and_stable_code(
    status_code,
    expected_error,
    expected_code,
):
    enforcer, ledger = _enforcer()
    reference = f"request-http-{status_code}"

    with pytest.raises(expected_error):
        _execute(
            enforcer,
            reference,
            lambda: (_ for _ in ()).throw(_SyntheticHTTPError(status_code)),
        )

    assert ledger.committed_microusd("finops:global", "2026-08") == 140
    state = AIProviderOperationAttempt.objects.get(
        provider="groq",
        operation_key=_operation_key(reference),
    )
    assert state.last_error_code == expected_code
    assert state.completed_at is None


def test_retry_reuses_same_budget_bundle_instead_of_double_reserving():
    enforcer, ledger = _enforcer()
    calls = 0

    def timeout_call():
        nonlocal calls
        calls += 1
        raise TimeoutError("synthetic provider timeout")

    with pytest.raises(LLMProviderTimeout):
        _execute(enforcer, "request-retry", timeout_call)
    assert ledger.committed_microusd("finops:global", "2026-08") == 140

    def success_call():
        nonlocal calls
        calls += 1
        return LLMResponse(
            content="ok",
            provider="groq",
            usage=LLMUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        )

    response = _execute(
        enforcer,
        "request-retry",
        success_call,
        now=_NOW + timedelta(seconds=1),
    )

    assert response.content == "ok"
    assert calls == 2
    assert ledger.committed_microusd("finops:global", "2026-08") == 20
    state = AIProviderOperationAttempt.objects.get(
        provider="groq",
        operation_key=_operation_key("request-retry"),
    )
    assert state.attempt_count == 2
    assert state.completed_at is not None


def test_missing_provider_usage_keeps_conservative_reservation():
    enforcer, ledger = _enforcer()

    response = _execute(
        enforcer,
        "request-missing-usage",
        lambda: LLMResponse(content="ok", provider="groq", usage=None),
    )

    assert response.content == "ok"
    assert ledger.committed_microusd("finops:global", "2026-08") == 140
