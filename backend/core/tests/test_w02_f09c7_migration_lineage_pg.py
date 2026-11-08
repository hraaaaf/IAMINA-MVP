"""W02 C7 runtime migration ledger blocker on disposable Django PG16 only.

No Neon connection. Intentionally inserts a fake W01/D2 collision only inside
a rolled-back PostgreSQL transaction and proves the C7 runtime gate rejects.
"""
import pytest
from django.db import transaction
from django.db.migrations.recorder import MigrationRecorder

from core.web_refresh_c7_atomic_candidate import _compatible_runtime_lineage

pytestmark = pytest.mark.django_db(transaction=True)


def test_c7_source_lineage_is_valid_in_disposable_pg16():
    assert _compatible_runtime_lineage() is True


@pytest.mark.parametrize("conflicting", [
    "0020_erasure_attempt",
    "0021_erasure_attempt_claim_states",
    "0022_d2_preview_consent_receipt",
    "0023_d2_in_app_notice",
])
def test_c7_rejects_unrepresented_w01_d2_migrations(conflicting):
    assert _compatible_runtime_lineage() is True
    with transaction.atomic():
        MigrationRecorder.Migration.objects.create(app="core", name=conflicting)
        assert _compatible_runtime_lineage() is False
        transaction.set_rollback(True)
    assert _compatible_runtime_lineage() is True


def test_c7_rejects_missing_ledger_parent_without_committing():
    with transaction.atomic():
        MigrationRecorder.Migration.objects.filter(
            app="core", name="0019_auth_abuse_bucket",
        ).delete()
        assert _compatible_runtime_lineage() is False
        transaction.set_rollback(True)
    assert _compatible_runtime_lineage() is True
