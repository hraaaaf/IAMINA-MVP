from datetime import date

import pytest

from core.emergency_operating_mode import (
    EmergencyOperatingPolicy,
    MONITORED_HUMAN,
    PILOT_EMERGENCY_POLICY,
    SELF_CARE_ONLY,
    append_emergency_disclosure,
    decorate_emergency_payload,
    emergency_disclosure,
)


def test_pilot_defaults_to_explicit_self_care_only_mode():
    PILOT_EMERGENCY_POLICY.validate(today=date(2026, 8, 2))
    assert PILOT_EMERGENCY_POLICY.mode == SELF_CARE_ONLY
    assert PILOT_EMERGENCY_POLICY.human_monitoring is False


def test_self_care_mode_cannot_claim_monitoring():
    policy = EmergencyOperatingPolicy(
        mode=SELF_CARE_ONLY,
        policy_owner="safety",
        effective_on=date(2026, 8, 1),
        review_due_on=date(2026, 9, 1),
        human_monitoring=True,
    )
    with pytest.raises(ValueError, match="cannot claim"):
        policy.validate(today=date(2026, 8, 2))


def test_monitored_mode_requires_complete_operational_evidence():
    policy = EmergencyOperatingPolicy(
        mode=MONITORED_HUMAN,
        policy_owner="safety",
        effective_on=date(2026, 8, 1),
        review_due_on=date(2026, 9, 1),
        human_monitoring=True,
    )
    with pytest.raises(ValueError, match="lacks operational evidence"):
        policy.validate(today=date(2026, 8, 2))


def test_payload_discloses_no_monitoring_and_adds_machine_metadata():
    result = decorate_emergency_payload(
        {"reply": "Contactez les urgences.", "is_emergency": True},
        language="fr",
    )
    assert emergency_disclosure("fr") in result["reply"]
    assert result["emergency_operating_mode"] == SELF_CARE_ONLY
    assert result["human_monitoring"] is False


def test_disclosure_is_idempotent():
    once = append_emergency_disclosure("Urgence.", "en")
    twice = append_emergency_disclosure(once, "en")
    assert once == twice


@pytest.mark.parametrize("language", ("fr", "en", "ar", "ar-MA"))
def test_all_supported_disclosures_deny_automatic_human_monitoring(language):
    disclosure = emergency_disclosure(language)
    assert disclosure.strip()
    assert len(disclosure) > 40
