import hashlib
import json
import pickle
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from core.contracts.document_extraction import ExtractedField, ExtractionDecision, FieldProvenance
from diabetes.models import LabReport
from diabetes.services.documents.neutral_adapter import from_neutral, to_neutral
from diabetes.services.documents.pulper import ingest
from diabetes.services.documents.store import persist
from media.documents.security import DocumentInspection

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class FieldProvenanceContractTest(SimpleTestCase):
    def test_verified_evidence_does_not_mean_clinical_acceptance(self):
        provenance = FieldProvenance(
            source_sha256="A" * 64,
            source_ref="text:L0002",
            extractor="media.docx",
            extractor_version="1",
            schema_version="pulper-output-v2",
            parser_model="gemini-2.5-flash",
            prompt_version="pulper-parse-v2-provenance",
            evidence_verified=True,
        )
        field = ExtractedField(
            code="generic_measure",
            value=7.2,
            raw_value="7.2%",
            provenance=provenance,
        )

        self.assertEqual(provenance.source_sha256, "a" * 64)
        self.assertEqual(field.source_ref, "text:L0002")
        self.assertFalse(field.verified)
        self.assertEqual(field.decision, ExtractionDecision.REVIEW_REQUIRED)

    def test_invalid_source_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_sha256"):
            FieldProvenance(
                source_sha256="z" * 64,
                source_ref="text:L0001",
                extractor="media.docx",
                extractor_version="1",
                schema_version="pulper-output-v2",
            )


class PulperTextProvenanceTest(SimpleTestCase):
    def _ingest_docx(self, llm_payload: dict, raw_text: str):
        llm = SimpleNamespace(
            complete=lambda *_args, **_kwargs: SimpleNamespace(
                content=json.dumps(llm_payload),
                provider="gemini-2.5-flash",
            )
        )
        with (
            patch(
                "diabetes.services.documents.pulper.inspect_document",
                return_value=DocumentInspection(kind="docx", mime_type=_DOCX_MIME),
            ),
            patch(
                "diabetes.services.documents.pulper.extract_docx",
                return_value=raw_text,
            ),
            patch("diabetes.services.documents.pulper.assert_ai_egress_allowed"),
            patch("llm.factory.get_llm", return_value=llm),
        ):
            return ingest(b"synthetic-docx", "report.docx", _DOCX_MIME)

    def test_llm_evidence_is_kept_only_when_it_matches_the_cited_line(self):
        output = self._ingest_docx(
            {
                "document_type": "lab_report",
                "confidence": 0.92,
                "lab_values": {"hba1c_pct": 7.2},
                "glucose_readings": [],
                "medications": [],
                "clinical_notes": "",
                "evidence": {
                    "lab_values.hba1c_pct": {"r": "L0002", "v": "7.2%"}
                },
            },
            "Lab report\nHbA1c 7.2%\n",
        )

        evidence = output.lab_values.evidence["hba1c_pct"]
        self.assertEqual(
            output.source_sha256,
            hashlib.sha256(b"synthetic-docx").hexdigest(),
        )
        self.assertEqual(output.extractor, "media.docx")
        self.assertEqual(output.extractor_version, "2")
        self.assertEqual(output.parser_model, "gemini-2.5-flash")
        self.assertEqual(
            output.prompt_version,
            "pulper-parse-v4-sparse-output",
        )
        self.assertEqual(evidence.raw_value, "7.2%")
        self.assertEqual(evidence.source_ref, "text:L0002")
        self.assertTrue(evidence.verified)

    def test_hallucinated_evidence_is_discarded_without_leaking_raw_value(self):
        output = self._ingest_docx(
            {
                "document_type": "lab_report",
                "confidence": 0.92,
                "lab_values": {"hba1c_pct": 7.2},
                "glucose_readings": [],
                "medications": [],
                "clinical_notes": "",
                "evidence": {
                    "lab_values.hba1c_pct": {"r": "L0002", "v": "9.9%"}
                },
            },
            "Lab report\nHbA1c 7.2%\n",
        )

        self.assertNotIn("hba1c_pct", output.lab_values.evidence)
        self.assertTrue(any("provenance" in item.lower() for item in output.warnings))
        self.assertNotIn("9.9%", "\n".join(output.warnings))

    def test_shield_rejection_also_removes_field_evidence(self):
        output = self._ingest_docx(
            {
                "document_type": "lab_report",
                "confidence": 0.92,
                "lab_values": {"hba1c_pct": 99.0},
                "glucose_readings": [],
                "medications": [],
                "clinical_notes": "",
                "evidence": {
                    "lab_values.hba1c_pct": {"r": "L0002", "v": "99.0%"}
                },
            },
            "Lab report\nHbA1c 99.0%\n",
        )

        self.assertIsNone(output.lab_values.hba1c_pct)
        self.assertNotIn("hba1c_pct", output.lab_values.evidence)


class PulperSpreadsheetProvenanceTest(SimpleTestCase):
    CSV = (
        "timestamp,glucose\n"
        "2026-08-20T08:15:00+01:00,126\n"
    )

    def test_spreadsheet_provenance_uses_exact_source_row_and_column(self):
        payload = self.CSV.encode()
        output = ingest(payload, "readings.csv", "text/csv")
        reading = output.glucose_readings[0]

        self.assertEqual(
            output.source_sha256,
            hashlib.sha256(payload).hexdigest(),
        )
        self.assertEqual(output.extractor, "diabetes.spreadsheet")
        self.assertEqual(output.extractor_version, "2")
        self.assertIsNone(output.parser_model)

        glucose_evidence = reading.evidence["value_mgdl"]
        self.assertEqual(glucose_evidence.raw_value, "126")
        self.assertEqual(glucose_evidence.source_ref, "row:2;column:glucose")
        self.assertTrue(glucose_evidence.verified)

        timestamp_evidence = reading.evidence["timestamp"]
        self.assertEqual(
            timestamp_evidence.raw_value,
            "2026-08-20T08:15:00+01:00",
        )
        self.assertEqual(
            timestamp_evidence.source_ref,
            "row:2;column:timestamp",
        )

    def test_provenance_survives_neutral_round_trip_without_auto_acceptance(self):
        output = ingest(self.CSV.encode(), "readings.csv", "text/csv")
        neutral = to_neutral(output)
        value_field = next(
            field
            for field in neutral.records[0].fields
            if field.code == "value_mgdl"
        )

        self.assertEqual(value_field.raw_value, "126")
        self.assertEqual(value_field.source_ref, "row:2;column:glucose")
        self.assertIsNotNone(value_field.provenance)
        self.assertTrue(value_field.provenance.evidence_verified)
        self.assertFalse(value_field.verified)
        self.assertEqual(
            value_field.decision,
            ExtractionDecision.REVIEW_REQUIRED,
        )
        self.assertEqual(from_neutral(neutral), output)

    def test_pulper_output_provenance_is_cache_serializable(self):
        output = ingest(self.CSV.encode(), "readings.csv", "text/csv")
        # Trusted in-test round-trip only; no untrusted bytes are deserialized here.
        restored = pickle.loads(pickle.dumps(output))  # nosec B301
        self.assertEqual(restored, output)


class PulperProvenancePersistenceTest(TestCase):
    def test_provenance_survives_persistence_without_copying_full_raw_text(self):
        payload = (
            "timestamp,glucose\n"
            "2026-08-20T08:15:00+01:00,126\n"
        ).encode()
        output = ingest(payload, "readings.csv", "text/csv")
        patient = User.objects.create_user(username="pulper-provenance-patient")

        result = persist(output, patient, "provenance-batch")
        self.assertTrue(result.ok, result.errors)

        report = LabReport.objects.get(pk=result.lab_report_id)
        provenance = report.extraction_provenance
        self.assertEqual(
            provenance["source_sha256"],
            hashlib.sha256(payload).hexdigest(),
        )
        self.assertEqual(provenance["extractor"], "diabetes.spreadsheet")
        self.assertNotIn("raw_text", provenance)
        self.assertEqual(report.raw_text, "")

        glucose_record = provenance["records"][0]
        self.assertEqual(glucose_record["record_type"], "glucose_reading")
        value_evidence = glucose_record["fields"]["value_mgdl"]
        self.assertEqual(value_evidence["normalized_value"], 126.0)
        self.assertEqual(value_evidence["raw_value"], "126")
        self.assertEqual(value_evidence["source_ref"], "row:2;column:glucose")
        self.assertTrue(value_evidence["evidence_verified"])
