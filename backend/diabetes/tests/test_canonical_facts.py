from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from django.test import SimpleTestCase

from core.contracts.clinical_fact import (
    UCUM_SYSTEM,
    ClinicalFactDecision,
    ClinicalFactSource,
)
from core.contracts.document_extraction import (
    DocumentExtraction,
    ExtractedField,
    ExtractedRecord,
    ExtractionDecision,
    FieldProvenance,
)
from diabetes.services.canonical_facts import (
    from_cgm_reading,
    from_document_extraction,
    from_log_entry,
)


class CanonicalFactAdaptersTest(SimpleTestCase):
    def test_manual_and_import_log_entries_share_the_same_glucose_contract(self):
        when = datetime(2026, 8, 22, 8, 15, tzinfo=timezone.utc)
        manual = SimpleNamespace(
            patient_id=7,
            source="manual",
            pk=10,
            client_uuid=None,
            blood_sugar=126,
            effective_time=when,
            glycemic_context="fasting",
            meal_type="",
        )
        imported = SimpleNamespace(
            patient_id=7,
            source="import",
            pk=11,
            client_uuid=None,
            blood_sugar=126,
            effective_time=when,
            glycemic_context="fasting",
            meal_type="",
        )

        manual_fact = from_log_entry(manual)
        import_fact = from_log_entry(imported)

        self.assertEqual(manual_fact.concept, "glucose")
        self.assertEqual(import_fact.concept, "glucose")
        self.assertEqual(manual_fact.value, import_fact.value)
        self.assertEqual(manual_fact.unit, "mg/dL")
        self.assertEqual(manual_fact.unit_system, UCUM_SYSTEM)
        self.assertEqual(manual_fact.source_type, ClinicalFactSource.MANUAL)
        self.assertEqual(import_fact.source_type, ClinicalFactSource.IMPORT)
        self.assertEqual(manual_fact.subject_ref, "patient:7")

    def test_cgm_reading_maps_without_clinical_value_reinterpretation(self):
        reading = SimpleNamespace(
            patient_id=7,
            source="linx",
            dedupe_key="abc",
            glucose_mg_dl=142,
            recorded_at=datetime(2026, 8, 22, 8, 20, tzinfo=timezone.utc),
            trend="flat",
            device="sensor-1",
        )

        fact = from_cgm_reading(reading)

        self.assertEqual(fact.value, 142)
        self.assertEqual(fact.source_type, ClinicalFactSource.CGM)
        self.assertEqual(fact.source_ref, "cgm:linx:abc")
        self.assertEqual(fact.attributes["provider"], "linx")
        self.assertTrue(fact.provenance.evidence_verified)

    def test_document_extraction_maps_lab_glucose_and_preserves_provenance(self):
        digest = "a" * 64
        provenance = FieldProvenance(
            source_sha256=digest,
            source_ref="doc:sha256:field:glucose",
            extractor="pulper",
            extractor_version="2",
            schema_version="1",
            extractor_model="vision-v1",
            parser_model="parser-v2",
            prompt_version="pulper-v3",
            evidence_verified=True,
        )
        extraction = DocumentExtraction(
            document_type="lab_report",
            source_format="pdf",
            confidence=0.96,
            fields=(
                ExtractedField(
                    code="report_date",
                    value="2026-08-22",
                    decision=ExtractionDecision.ACCEPTED,
                ),
                ExtractedField(
                    code="fasting_glucose_mgdl",
                    value=126,
                    unit="mg/dL",
                    confidence=0.98,
                    decision=ExtractionDecision.ACCEPTED,
                    provenance=provenance,
                ),
            ),
        )

        (fact,) = from_document_extraction(extraction, patient_id=7, source_ref="doc:sha256")

        self.assertEqual(fact.subject_ref, "patient:7")
        self.assertEqual(fact.concept, "glucose")
        self.assertEqual(fact.value, 126)
        self.assertEqual(fact.effective_at, "2026-08-22")
        self.assertEqual(fact.decision, ClinicalFactDecision.ACCEPTED)
        self.assertEqual(fact.provenance.source_sha256, digest)
        self.assertTrue(fact.provenance.evidence_verified)
        self.assertEqual(fact.provenance.extractor, "pulper")
        self.assertEqual(fact.provenance.extractor_version, "2")
        self.assertEqual(fact.provenance.schema_version, "1")
        self.assertEqual(fact.provenance.extractor_model, "vision-v1")
        self.assertEqual(fact.provenance.parser_model, "parser-v2")
        self.assertEqual(fact.provenance.prompt_version, "pulper-v3")
        self.assertEqual(fact.codings, ())

    def test_review_required_report_date_downgrades_lab_fact(self):
        extraction = DocumentExtraction(
            document_type="lab_report",
            source_format="pdf",
            confidence=0.9,
            fields=(
                ExtractedField(
                    code="report_date",
                    value="2026-08-22",
                    decision=ExtractionDecision.REVIEW_REQUIRED,
                ),
                ExtractedField(
                    code="fasting_glucose_mgdl",
                    value=126,
                    unit="mg/dL",
                    decision=ExtractionDecision.ACCEPTED,
                ),
            ),
        )

        (fact,) = from_document_extraction(extraction, patient_id=7)

        self.assertEqual(fact.effective_at, "2026-08-22")
        self.assertEqual(fact.decision, ClinicalFactDecision.REVIEW_REQUIRED)

    def test_document_glucose_record_keeps_effective_time_and_context(self):
        extraction = DocumentExtraction(
            document_type="glucose_log",
            source_format="csv",
            confidence=1.0,
            records=(
                ExtractedRecord(
                    record_type="glucose_reading",
                    fields=(
                        ExtractedField(
                            code="timestamp",
                            value="2026-08-22T08:15:00+01:00",
                            decision=ExtractionDecision.ACCEPTED,
                        ),
                        ExtractedField(
                            code="value_mgdl",
                            value=126,
                            unit="mg/dL",
                            decision=ExtractionDecision.ACCEPTED,
                        ),
                        ExtractedField(
                            code="context",
                            value="fasting",
                            decision=ExtractionDecision.ACCEPTED,
                        ),
                    ),
                ),
            ),
        )

        (fact,) = from_document_extraction(extraction, patient_id=9, source_ref="import:csv:1")

        self.assertEqual(fact.effective_at, "2026-08-22T08:15:00+01:00")
        self.assertEqual(fact.context, "fasting")
        self.assertEqual(fact.source_type, ClinicalFactSource.DOCUMENT)

    def test_review_required_glucose_context_downgrades_record_fact(self):
        extraction = DocumentExtraction(
            document_type="glucose_log",
            source_format="csv",
            confidence=1.0,
            records=(
                ExtractedRecord(
                    record_type="glucose_reading",
                    fields=(
                        ExtractedField(
                            code="value_mgdl",
                            value=126,
                            unit="mg/dL",
                            decision=ExtractionDecision.ACCEPTED,
                        ),
                        ExtractedField(
                            code="context",
                            value="fasting",
                            decision=ExtractionDecision.REVIEW_REQUIRED,
                        ),
                    ),
                ),
            ),
        )

        (fact,) = from_document_extraction(extraction, patient_id=9)

        self.assertEqual(fact.context, "fasting")
        self.assertEqual(fact.decision, ClinicalFactDecision.REVIEW_REQUIRED)

    def test_rejected_document_metadata_is_not_promoted_into_fact_context(self):
        extraction = DocumentExtraction(
            document_type="glucose_log",
            source_format="csv",
            confidence=0.8,
            records=(
                ExtractedRecord(
                    record_type="glucose_reading",
                    fields=(
                        ExtractedField(
                            code="timestamp",
                            value="2026-08-22T08:15:00+01:00",
                            decision=ExtractionDecision.REJECTED,
                        ),
                        ExtractedField(
                            code="value_mgdl",
                            value=126,
                            unit="mg/dL",
                            decision=ExtractionDecision.REVIEW_REQUIRED,
                        ),
                        ExtractedField(
                            code="context",
                            value="fasting",
                            decision=ExtractionDecision.REJECTED,
                        ),
                    ),
                ),
            ),
        )

        (fact,) = from_document_extraction(extraction, patient_id=9, source_ref="import:csv:2")

        self.assertIsNone(fact.effective_at)
        self.assertIsNone(fact.context)
        self.assertEqual(fact.decision, ClinicalFactDecision.REVIEW_REQUIRED)
