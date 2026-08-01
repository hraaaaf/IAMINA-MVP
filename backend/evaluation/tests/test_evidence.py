from datetime import date

from evaluation.evidence import ProviderEvidence


def _evidence(**overrides):
    values = {
        "provider": "synthetic-provider",
        "model": "model-v1",
        "modality": "text",
        "source_owner": "legal",
        "source_reference": "contract-v1",
        "verified_on": date(2026, 8, 1),
        "review_due_on": date(2026, 11, 1),
        "data_regions": ("eu",),
        "retention_days": 0,
        "training_use": False,
        "no_retention_available": True,
        "subprocessors_known": True,
    }
    values.update(overrides)
    return ProviderEvidence(**values)


def test_complete_current_evidence_is_not_disqualified():
    assert _evidence().disqualifications(today=date(2026, 8, 2)) == ()


def test_unknown_or_unapproved_privacy_facts_fail_closed():
    reasons = _evidence(
        data_regions=(),
        training_use=None,
        no_retention_available=None,
        subprocessors_known=False,
    ).disqualifications(today=date(2026, 8, 2))
    assert set(reasons) == {
        "data_region_unknown",
        "training_use_not_excluded",
        "no_retention_not_confirmed",
        "subprocessors_unknown",
    }


def test_stale_evidence_is_disqualified():
    reasons = _evidence(review_due_on=date(2026, 7, 31)).disqualifications(
        today=date(2026, 8, 2)
    )
    assert reasons == ("evidence_stale",)
