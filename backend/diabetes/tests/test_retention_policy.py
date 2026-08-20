from __future__ import annotations

import json
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from core.retention import RetentionClass, RetentionPolicy
from diabetes.api.v1.documents import _PENDING_TTL
from diabetes.models import LabReport
from diabetes.retention import (
    LAB_REPORT_RAW_TEXT_POLICY,
    LAB_REPORT_STRUCTURED_POLICY,
)
from media.documents.retention import PENDING_EXTRACTION_POLICY


class RetentionPolicyContractTest(TestCase):
    def test_transient_policy_requires_bounded_ttl(self):
        with self.assertRaises(ValueError):
            RetentionPolicy(
                storage_key="synthetic.transient",
                retention_class=RetentionClass.TRANSIENT_EXTRACTION,
                policy_basis="synthetic test",
            )

    def test_human_gated_destructive_ttl_requires_approval_reference(self):
        with self.assertRaises(ValueError):
            RetentionPolicy(
                storage_key="synthetic.governed",
                retention_class=RetentionClass.GOVERNED_EVIDENCE,
                policy_basis="synthetic governed evidence",
                destructive_ttl_seconds=86400,
                human_gate_required=True,
            )

    def test_pending_extraction_policy_matches_runtime_cache_ttl(self):
        self.assertEqual(PENDING_EXTRACTION_POLICY.destructive_ttl_seconds, _PENDING_TTL)
        self.assertEqual(
            PENDING_EXTRACTION_POLICY.retention_class,
            RetentionClass.TRANSIENT_EXTRACTION,
        )

    def test_raw_text_has_no_destructive_ttl_before_human_gate(self):
        self.assertEqual(
            LAB_REPORT_RAW_TEXT_POLICY.retention_class,
            RetentionClass.GOVERNED_EVIDENCE,
        )
        self.assertTrue(LAB_REPORT_RAW_TEXT_POLICY.human_gate_required)
        self.assertIsNone(LAB_REPORT_RAW_TEXT_POLICY.destructive_ttl_seconds)
        self.assertIsNone(LAB_REPORT_RAW_TEXT_POLICY.approval_reference)

    def test_structured_facts_have_separate_lifecycle(self):
        self.assertEqual(
            LAB_REPORT_STRUCTURED_POLICY.retention_class,
            RetentionClass.STRUCTURED_VERIFIED_FACTS,
        )
        self.assertTrue(LAB_REPORT_STRUCTURED_POLICY.human_gate_required)
        self.assertIsNone(LAB_REPORT_STRUCTURED_POLICY.destructive_ttl_seconds)


class RetentionInventoryCommandTest(TestCase):
    def test_inventory_is_aggregate_only_and_non_destructive(self):
        patient = User.objects.create_user(
            username="synthetic-retention-user",
            email="synthetic-retention@example.test",
        )
        LabReport.objects.create(
            patient=patient,
            raw_text="SYNTHETIC_PRIVATE_RAW_TEXT",
            document_type="lab_report",
            source_format="pdf",
        )

        out = StringIO()
        call_command("retention_inventory", "--json", stdout=out)
        rendered = out.getvalue()
        payload = json.loads(rendered)

        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["persistent_raw_text"]["object_count"], 1)
        self.assertEqual(
            payload["persistent_raw_text"]["character_count"],
            len("SYNTHETIC_PRIVATE_RAW_TEXT"),
        )
        self.assertNotIn("SYNTHETIC_PRIVATE_RAW_TEXT", rendered)
        self.assertNotIn("synthetic-retention-user", rendered)
        self.assertNotIn("synthetic-retention@example.test", rendered)
        self.assertTrue(LabReport.objects.filter(patient=patient).exists())
