"""W01 opt-in synthetic integration with existing API and erasure hook."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import override_settings

from diabetes.api.v1.documents import confirm_import, ingest_document
from diabetes.apps import _purge_pending_documents
from diabetes.models import PendingDocumentExtraction
from diabetes.services.documents.schema import PulperOutput


class _Upload:
    name = "synthetic.pdf"
    content_type = "application/pdf"
    size = 4

    def read(self, size=-1):
        return b"test"


@pytest.mark.django_db
@override_settings(DEBUG=True, W01_PG_PENDING_SYNTHETIC_ONLY=True)
def test_api_stages_and_confirms_only_with_sql_not_redis():
    patient = User.objects.create_user(username="synthetic-pg-api")
    request = SimpleNamespace(auth=patient)
    output = PulperOutput(raw_text="DO_NOT_STORE_SOURCE_TEXT")

    with (
        patch("diabetes.api.v1.documents.ingest", return_value=output),
        patch("diabetes.api.v1.documents.cache") as redis_cache,
        patch("diabetes.api.v1.documents._do_persist") as persistence,
    ):
        persistence.return_value = SimpleNamespace(ok=True)
        status, preview = ingest_document.__wrapped__(request, _Upload(), confirm=False)
        assert status == 200
        assert PendingDocumentExtraction.objects.filter(patient=patient).count() == 1
        assert confirm_import(request, preview.batch_id).ok
        assert not PendingDocumentExtraction.objects.filter(patient=patient).exists()
        assert not confirm_import(request, preview.batch_id).ok
        persistence.assert_called_once()
        redis_cache.set.assert_not_called()
        redis_cache.add.assert_not_called()
        redis_cache.get.assert_not_called()


@pytest.mark.django_db
@override_settings(DEBUG=True, W01_PG_PENDING_SYNTHETIC_ONLY=True)
def test_account_deletion_hook_purges_sql_not_redis():
    patient = User.objects.create_user(username="synthetic-pg-erasure")
    request = SimpleNamespace(auth=patient)
    with (
        patch("diabetes.api.v1.documents.ingest", return_value=PulperOutput()),
        patch("media.documents.pending_cache.purge_patient_pending_extractions") as redis,
    ):
        status, preview = ingest_document.__wrapped__(request, _Upload(), confirm=False)
        assert status == 200
        assert PendingDocumentExtraction.objects.filter(patient=patient).exists()
        _purge_pending_documents(patient.pk, "")
        redis.assert_not_called()
        assert not PendingDocumentExtraction.objects.filter(patient=patient).exists()
