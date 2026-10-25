"""Tests for W01 synthetic PostgreSQL staging candidate only.

They do NOT certify patient production retention or Neon PITR erasure.
"""
from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone

from diabetes.models import PendingDocumentExtraction
from diabetes.services.documents.schema import (
    FieldEvidence, GlucoseReading, LabValues, PulperOutput,
)
from diabetes.services.documents.w01_postgres_pending import (
    confirm_once, prune_expired, purge_patient, stage_pending,
)

SPIKE = {"W01_PG_PENDING_SYNTHETIC_ONLY": True, "DEBUG": True}


@pytest.mark.django_db
@override_settings(**SPIKE)
def test_stage_and_confirm_preserve_clinical_value_and_evidence_but_drop_raw_text():
    user = User.objects.create_user(username="synthetic-pg-stage")
    output = PulperOutput(
        document_type="lab_report",
        raw_text="RAW_DOCUMENT_SENTINEL_DO_NOT_STAGE",
        source_sha256="a" * 64,
        glucose_readings=[
            GlucoseReading(
                value_mgdl=109.0,
                timestamp="2026-10-25T09:00:00+00:00",
                evidence={"value_mgdl": FieldEvidence(raw_value="109", verified=True)},
            )
        ],
        lab_values=LabValues(hba1c_pct=6.1),
    )
    batch = stage_pending(user.id, output)
    row = PendingDocumentExtraction.objects.get(batch_id=batch)
    assert row.payload["raw_text"] == ""
    assert "RAW_DOCUMENT_SENTINEL_DO_NOT_STAGE" not in str(row.payload)
    assert row.expires_at > timezone.now()
    seen = []
    def persist(value, patient, batch_id):
        seen.append((value, patient.id, batch_id))
        return SimpleNamespace(ok=True)
    result = confirm_once(user, batch, persist)
    assert result.ok
    assert len(seen) == 1
    assert seen[0][0].glucose_readings[0].evidence["value_mgdl"].verified is True
    assert seen[0][0].lab_values.hba1c_pct == 6.1
    assert seen[0][0].raw_text == ""
    assert PendingDocumentExtraction.objects.count() == 0
    assert confirm_once(user, batch, persist) is None
    assert len(seen) == 1


@pytest.mark.django_db
@override_settings(**SPIKE)
def test_patient_isolation_and_cascade_after_erasure():
    a = User.objects.create_user(username="synthetic-pg-A")
    b = User.objects.create_user(username="synthetic-pg-B")
    batch = stage_pending(a.id, PulperOutput())
    callback = Mock(return_value=SimpleNamespace(ok=True))
    assert confirm_once(b, batch, callback) is None
    callback.assert_not_called()
    assert PendingDocumentExtraction.objects.filter(patient=a).exists()
    assert purge_patient(b.id) == 0
    a.delete()
    assert PendingDocumentExtraction.objects.count() == 0


@pytest.mark.django_db
@override_settings(**SPIKE)
def test_expiration_rejects_confirm_and_prunes_expired_rows():
    patient = User.objects.create_user(username="synthetic-pg-expired")
    batch = stage_pending(patient.id, PulperOutput())
    PendingDocumentExtraction.objects.filter(batch_id=batch).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    callback = Mock()
    assert confirm_once(patient, batch, callback) is None
    callback.assert_not_called()
    assert prune_expired() == 1
    assert PendingDocumentExtraction.objects.count() == 0


@pytest.mark.django_db
@override_settings(**SPIKE)
def test_callback_failure_rolls_back_consumption():
    patient = User.objects.create_user(username="synthetic-pg-rollback")
    batch = stage_pending(patient.id, PulperOutput())
    with pytest.raises(RuntimeError, match="synthetic fault"):
        confirm_once(
            patient, batch, Mock(side_effect=RuntimeError("synthetic fault"))
        )
    assert PendingDocumentExtraction.objects.filter(batch_id=batch).exists()


@pytest.mark.django_db
@override_settings(**SPIKE)
def test_purge_only_matches_one_patient():
    a = User.objects.create_user(username="synthetic-pg-purge-A")
    b = User.objects.create_user(username="synthetic-pg-purge-B")
    stage_pending(a.id, PulperOutput())
    stage_pending(b.id, PulperOutput())
    assert purge_patient(a.id) == 1
    assert PendingDocumentExtraction.objects.filter(patient=a).count() == 0
    assert PendingDocumentExtraction.objects.filter(patient=b).count() == 1


@pytest.mark.django_db
@override_settings(W01_PG_PENDING_SYNTHETIC_ONLY=True, DEBUG=False)
def test_postgres_staging_refuses_any_non_debug_runtime():
    patient = User.objects.create_user(username="synthetic-pg-prod-guard")
    with pytest.raises(PermissionError, match="disabled"):
        stage_pending(patient.id, PulperOutput())
    assert PendingDocumentExtraction.objects.count() == 0


@pytest.mark.django_db
@override_settings(W01_PG_PENDING_SYNTHETIC_ONLY=False, DEBUG=True)
def test_staging_is_off_by_default():
    patient = User.objects.create_user(username="synthetic-pg-off")
    with pytest.raises(PermissionError):
        stage_pending(patient.id, PulperOutput())
