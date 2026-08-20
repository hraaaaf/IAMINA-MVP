from __future__ import annotations

import json

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.models import LabReport
from diabetes.services.documents.portability import build_document_portability_export


class DocumentPortabilityExportTest(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="patient-export")
        self.other_patient = User.objects.create_user(username="other-patient")

    def test_export_is_patient_scoped_and_includes_retained_raw_text(self):
        report = LabReport.objects.create(
            patient=self.patient,
            document_type="lab_report",
            source_format="pdf",
            hba1c_pct=7.1,
            fasting_glucose_mgdl=126.0,
            confidence=0.91,
            clinical_notes="confirmed note",
            raw_text="synthetic retained text",
            import_batch_id="internal-batch-not-exported",
        )
        LabReport.objects.create(
            patient=self.other_patient,
            document_type="medical_report",
            source_format="image",
            raw_text="other patient secret",
        )

        exported = build_document_portability_export(self.patient)

        self.assertEqual(exported["schema_version"], "diabetes.documents.v1")
        self.assertEqual(exported["scope"], "diabetes.documents")
        self.assertFalse(exported["original_media_retained"])
        self.assertEqual(len(exported["reports"]), 1)
        exported_report = exported["reports"][0]
        self.assertEqual(exported_report["id"], report.pk)
        self.assertEqual(exported_report["structured_values"]["hba1c_pct"], 7.1)
        self.assertEqual(
            exported_report["retained_source"]["raw_text"],
            "synthetic retained text",
        )

        serialized = json.dumps(exported, sort_keys=True)
        self.assertNotIn("other patient secret", serialized)
        self.assertNotIn("internal-batch-not-exported", serialized)

    def test_export_is_json_safe_and_exposes_no_binary_or_transport_secret_fields(self):
        LabReport.objects.create(
            patient=self.patient,
            document_type="prescription",
            source_format="docx",
            raw_text="synthetic prescription text",
        )

        serialized = json.dumps(build_document_portability_export(self.patient), sort_keys=True)

        self.assertNotIn("encrypted_credential", serialized)
        self.assertNotIn("file_bytes", serialized)
        self.assertNotIn("binary", serialized)
        self.assertNotIn("import_batch_id", serialized)

    def test_empty_export_is_explicit_and_stable(self):
        exported = build_document_portability_export(self.patient)

        self.assertEqual(
            exported,
            {
                "schema_version": "diabetes.documents.v1",
                "scope": "diabetes.documents",
                "original_media_retained": False,
                "reports": [],
            },
        )
