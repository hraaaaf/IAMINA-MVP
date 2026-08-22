from __future__ import annotations

from dataclasses import FrozenInstanceError

from django.test import SimpleTestCase

from core.contracts.clinical_fact import (
    LOINC_SYSTEM,
    UCUM_SYSTEM,
    CanonicalClinicalFact,
    ClinicalCoding,
    ClinicalFactDecision,
    ClinicalFactProvenance,
    ClinicalFactSource,
)


class CanonicalClinicalFactContractTest(SimpleTestCase):
    def test_quantitative_fact_is_patient_linked_and_ucum_coded(self):
        fact = CanonicalClinicalFact(
            subject_ref="patient:42",
            concept="glucose",
            value=126,
            unit="mg/dL",
            unit_system=UCUM_SYSTEM,
            effective_at="2026-08-22T08:15:00+01:00",
            source_type=ClinicalFactSource.DOCUMENT,
            source_ref="lab:glucose:blood:abc123",
            confidence=1.0,
            decision=ClinicalFactDecision.ACCEPTED,
            codings=(
                ClinicalCoding(
                    system=LOINC_SYSTEM,
                    code="2339-0",
                    display="Glucose [Mass/volume] in Blood",
                ),
            ),
        )

        self.assertEqual(fact.subject_ref, "patient:42")
        self.assertEqual(fact.unit_system, UCUM_SYSTEM)
        self.assertEqual(fact.codings[0].system, LOINC_SYSTEM)
        self.assertEqual(fact.effective_at, "2026-08-22T08:15:00+01:00")

    def test_unit_does_not_claim_ucum_without_explicit_system(self):
        fact = CanonicalClinicalFact(
            subject_ref="patient:1",
            concept="custom_measurement",
            value=12,
            unit="custom-unit",
            source_type=ClinicalFactSource.API,
            source_ref="api:custom:1",
        )

        self.assertEqual(fact.unit, "custom-unit")
        self.assertIsNone(fact.unit_system)

    def test_attributes_are_immutable(self):
        fact = CanonicalClinicalFact(
            subject_ref="patient:1",
            concept="glucose",
            value=100,
            unit="mg/dL",
            source_type=ClinicalFactSource.MANUAL,
            source_ref="log_entry:1",
            attributes={"context": "fasting"},
        )

        with self.assertRaises(TypeError):
            fact.attributes["context"] = "post_meal"

        with self.assertRaises(FrozenInstanceError):
            fact.concept = "hba1c"

    def test_provenance_must_match_fact_source(self):
        provenance = ClinicalFactProvenance(
            source_ref="document:one",
            adapter="test",
            adapter_version="1",
        )

        with self.assertRaisesRegex(ValueError, "source_ref conflicts"):
            CanonicalClinicalFact(
                subject_ref="patient:1",
                concept="glucose",
                value=100,
                unit="mg/dL",
                source_type=ClinicalFactSource.DOCUMENT,
                source_ref="document:two",
                provenance=provenance,
            )

    def test_invalid_confidence_and_digest_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "confidence"):
            CanonicalClinicalFact(
                subject_ref="patient:1",
                concept="glucose",
                value=100,
                unit="mg/dL",
                source_type=ClinicalFactSource.API,
                source_ref="api:1",
                confidence=1.1,
            )

        with self.assertRaisesRegex(ValueError, "source_sha256"):
            ClinicalFactProvenance(
                source_ref="document:1",
                adapter="test",
                adapter_version="1",
                source_sha256="not-a-digest",
            )
