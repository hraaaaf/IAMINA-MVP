from __future__ import annotations

import json
from io import StringIO
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from diabetes.management.commands.retention_reconcile import build_reconciliation
from diabetes.models import LabReport


class RetentionReconciliationTest(TestCase):
    def test_default_reconciliation_is_non_destructive_and_redacts_content(self):
        patient = User.objects.create_user(username="retention-reconcile")
        LabReport.objects.create(
            patient=patient,
            document_type="lab_report",
            source_format="pdf",
            raw_text="SYNTHETIC_PRIVATE_RAW_TEXT",
        )

        out = StringIO()
        call_command("retention_reconcile", "--json", stdout=out)
        rendered = out.getvalue()
        payload = json.loads(rendered)

        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["persistent_raw_text_objects"], 1)
        self.assertEqual(payload["db_orphan_objects"], 0)
        self.assertFalse(payload["destructive_raw_text_purge_enabled"])
        self.assertEqual(payload["unapproved_destructive_policies"], 0)
        self.assertFalse(payload["cache_scan_performed"])
        self.assertIsNone(payload["cache_orphan_patient_scopes"])
        self.assertNotIn("SYNTHETIC_PRIVATE_RAW_TEXT", rendered)
        self.assertNotIn("retention-reconcile", rendered)
        self.assertTrue(LabReport.objects.filter(patient=patient).exists())

    def test_cache_scan_reports_orphan_scope_count_without_ids_or_values(self):
        patient = User.objects.create_user(username="retention-cache")
        redis = MagicMock()
        existing_key = f"amina:1:pulper:pending:{patient.id}:batch-a"
        orphan_key = "amina:1:pulper:pending:999999:batch-b"
        redis.scan_iter.return_value = iter([existing_key.encode(), orphan_key.encode()])

        with (
            patch(
                "diabetes.management.commands.retention_reconcile.get_redis_connection",
                return_value=redis,
            ),
            patch(
                "diabetes.management.commands.retention_reconcile.cache.make_key",
                return_value="amina:1:pulper:pending:*",
            ),
        ):
            payload = build_reconciliation(include_cache=True)

        self.assertTrue(payload["cache_scan_performed"])
        self.assertEqual(payload["cache_orphan_patient_scopes"], 1)
        rendered = json.dumps(payload, sort_keys=True)
        self.assertNotIn(existing_key, rendered)
        self.assertNotIn(orphan_key, rendered)
        self.assertNotIn("999999", rendered)
        redis.scan_iter.assert_called_once_with(match="amina:1:pulper:pending:*", count=100)
