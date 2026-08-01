from datetime import date

import pytest

from evaluation.text_live_manifest import TextProviderManifest


def _manifest(**overrides):
    values = {
        "provider": "synthetic-provider",
        "model": "synthetic-model",
        "credential_env_var": "SYNTHETIC_PROVIDER_API_KEY",
        "evidence_owner": "security-owner",
        "evidence_source": "https://example.invalid/provider-evidence",
        "verified_on": date(2026, 8, 1),
        "review_due_on": date(2026, 9, 1),
        "no_training_confirmed": True,
        "retention_confirmed": True,
        "residency_confirmed": True,
        "subprocessors_confirmed": True,
        "approved_for_synthetic_benchmark": True,
    }
    values.update(overrides)
    return TextProviderManifest(**values)


def test_valid_manifest_passes():
    _manifest().validate(today=date(2026, 8, 1))


def test_stale_evidence_fails_closed():
    with pytest.raises(ValueError, match="stale"):
        _manifest(review_due_on=date(2026, 7, 31)).validate(today=date(2026, 8, 1))


def test_missing_contractual_approval_fails_closed():
    with pytest.raises(ValueError, match="not eligible"):
        _manifest(no_training_confirmed=False).validate(today=date(2026, 8, 1))


def test_future_verification_date_is_rejected():
    with pytest.raises(ValueError, match="future"):
        _manifest(verified_on=date(2026, 8, 2)).validate(today=date(2026, 8, 1))
