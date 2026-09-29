from companion.protected_shadow_campaign import ProtectedShadowCampaignSummary
from companion.protected_shadow_promotion import (
    ProtectedShadowPromotionEvidence,
    assess_protected_shadow_promotion,
)


def _summary(**overrides):
    values = {
        "observed_turns": 4,
        "disabled": 0,
        "blocked": 0,
        "accepted": 4,
        "rejected": 0,
        "error": 0,
    }
    values.update(overrides)
    return ProtectedShadowCampaignSummary(**values)


def _evidence(**overrides):
    values = {
        "processor_governance_approved": True,
        "payload_boundary_verified": True,
        "adversarial_gate_green": True,
        "kill_switch_verified": True,
        "deterministic_fallback_verified": True,
        "clinical_authority_unchanged": True,
        "campaign_summary": _summary(),
    }
    values.update(overrides)
    return ProtectedShadowPromotionEvidence(**values)


def test_promotion_gate_accepts_only_complete_clean_evidence():
    decision = assess_protected_shadow_promotion(_evidence())

    assert decision.promotable is True
    assert decision.blockers == ()


def test_current_governance_state_blocks_promotion():
    decision = assess_protected_shadow_promotion(
        _evidence(processor_governance_approved=False)
    )

    assert decision.promotable is False
    assert decision.blockers == ("processor_governance_not_approved",)


def test_campaign_errors_rejections_and_blocked_turns_fail_closed():
    decision = assess_protected_shadow_promotion(
        _evidence(
            campaign_summary=_summary(
                accepted=1,
                blocked=1,
                rejected=1,
                error=1,
            )
        )
    )

    assert decision.promotable is False
    assert decision.blockers == (
        "campaign_contains_blocked_turns",
        "campaign_contains_errors",
        "campaign_contains_unresolved_rejections",
        "campaign_not_fully_accepted",
    )


def test_empty_campaign_cannot_promote():
    decision = assess_protected_shadow_promotion(
        _evidence(campaign_summary=_summary(observed_turns=0, accepted=0))
    )

    assert decision.promotable is False
    assert decision.blockers == ("campaign_has_no_observations",)


def test_every_safety_prerequisite_is_independently_required():
    fields = (
        ("payload_boundary_verified", "payload_boundary_not_verified"),
        ("adversarial_gate_green", "adversarial_gate_not_green"),
        ("kill_switch_verified", "kill_switch_not_verified"),
        ("deterministic_fallback_verified", "deterministic_fallback_not_verified"),
        ("clinical_authority_unchanged", "clinical_authority_changed"),
    )

    for field, blocker in fields:
        decision = assess_protected_shadow_promotion(_evidence(**{field: False}))
        assert decision.promotable is False
        assert blocker in decision.blockers
