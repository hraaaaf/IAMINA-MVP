import pytest

from companion.protected_shadow_campaign import (
    ProtectedShadowCampaignProtocol,
    summarize_protected_shadow_campaign,
)


def _event(status: str) -> dict[str, str]:
    return {
        "event": "protected_narration_shadow",
        "status": status,
        "provider": "groq",
        "family": "clinician_prep",
    }


def test_campaign_summary_counts_only_content_free_statuses():
    protocol = ProtectedShadowCampaignProtocol(
        campaign_id="internal-shadow-001",
        max_turns=6,
        locales=("fr", "ar-MA"),
    )
    summary = summarize_protected_shadow_campaign(
        protocol,
        [
            _event("blocked"),
            _event("accepted"),
            _event("rejected"),
            _event("error"),
            _event("accepted"),
        ],
    )

    assert summary.observed_turns == 5
    assert summary.blocked == 1
    assert summary.accepted == 2
    assert summary.rejected == 1
    assert summary.error == 1
    assert summary.provider_attempted_turns == 4


def test_campaign_rejects_any_extra_telemetry_field():
    protocol = ProtectedShadowCampaignProtocol(
        campaign_id="internal-shadow-001",
        max_turns=1,
        locales=("fr",),
    )
    event = _event("blocked")
    event["patient_id"] = "forbidden"

    with pytest.raises(ValueError, match="non-allowlisted"):
        summarize_protected_shadow_campaign(protocol, [event])


def test_campaign_is_hard_bounded():
    protocol = ProtectedShadowCampaignProtocol(
        campaign_id="internal-shadow-001",
        max_turns=2,
        locales=("fr",),
    )

    with pytest.raises(ValueError, match="max_turns"):
        summarize_protected_shadow_campaign(
            protocol,
            [_event("blocked"), _event("blocked"), _event("blocked")],
        )


def test_campaign_phase_is_single_family_single_provider():
    with pytest.raises(ValueError, match="clinician_prep"):
        ProtectedShadowCampaignProtocol(
            campaign_id="internal-shadow-001",
            max_turns=5,
            locales=("fr",),
            family="monitoring_interpretation",
        )

    with pytest.raises(ValueError, match="groq"):
        ProtectedShadowCampaignProtocol(
            campaign_id="internal-shadow-001",
            max_turns=5,
            locales=("fr",),
            provider="other",
        )
