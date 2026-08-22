import ast
from pathlib import Path
from unittest import TestCase

import core.contracts.document_extraction as document_contract
from diabetes.services.documents.neutral_adapter import from_neutral, to_neutral
from diabetes.services.documents.schema import (
    GlucoseReading,
    LabValues,
    MedicationEntry,
    PulperOutput,
)


class NeutralDocumentContractTest(TestCase):
    def test_core_contract_does_not_import_diabetes(self):
        source = Path(document_contract.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

        self.assertFalse(
            any(name == "diabetes" or name.startswith("diabetes.") for name in imported_modules)
        )

    def test_contract_exposes_explicit_lifecycle_states(self):
        self.assertEqual(
            [stage.value for stage in document_contract.ExtractionStage],
            ["extracted", "normalized", "validated", "decided", "persisted"],
        )

        extraction = document_contract.DocumentExtraction(
            document_type="generic_report",
            source_format="pdf",
            confidence=0.8,
        )
        self.assertEqual(extraction.stage, document_contract.ExtractionStage.EXTRACTED)

        persisted = document_contract.DocumentExtraction(
            document_type="generic_report",
            source_format="pdf",
            confidence=0.8,
            stage=document_contract.ExtractionStage.PERSISTED,
        )
        self.assertEqual(persisted.stage, document_contract.ExtractionStage.PERSISTED)

    def test_field_decision_is_explicit_and_legacy_verified_remains_compatible(self):
        candidate = document_contract.ExtractedField(code="generic_measure", value=12)
        self.assertEqual(
            candidate.decision,
            document_contract.ExtractionDecision.REVIEW_REQUIRED,
        )
        self.assertFalse(candidate.verified)

        legacy_verified = document_contract.ExtractedField(
            code="generic_measure",
            value=12,
            verified=True,
        )
        self.assertEqual(
            legacy_verified.decision,
            document_contract.ExtractionDecision.ACCEPTED,
        )

        accepted_unverified = document_contract.ExtractedField(
            code="generic_measure",
            value=12,
            decision=document_contract.ExtractionDecision.ACCEPTED,
            decision_reason="deterministic validator accepted candidate",
        )
        self.assertFalse(accepted_unverified.verified)

        with self.assertRaisesRegex(ValueError, "verified field cannot be rejected"):
            document_contract.ExtractedField(
                code="generic_measure",
                value=12,
                verified=True,
                decision=document_contract.ExtractionDecision.REJECTED,
            )

    def test_diabetes_output_round_trips_through_neutral_contract(self):
        original = PulperOutput(
            document_type="lab_report",
            source_format="pdf",
            confidence=0.91,
            glucose_readings=[
                GlucoseReading(
                    value_mgdl=126.0,
                    timestamp="2026-08-20T08:00:00",
                    context="fasting",
                    original_value=7.0,
                    original_unit="mmol/L",
                )
            ],
            lab_values=LabValues(
                hba1c_pct=6.8,
                fasting_glucose_mgdl=126.0,
                total_cholesterol_mgdl=180.0,
                hdl_mgdl=55.0,
                ldl_mgdl=100.0,
                triglycerides_mgdl=110.0,
                creatinine_umol=80.0,
                report_date="2026-08-19",
            ),
            medications=[
                MedicationEntry(
                    name="SyntheticMed",
                    dose="500 mg",
                    frequency="twice_daily",
                    drug_type="oral",
                )
            ],
            clinical_notes="Synthetic fixture only.",
            raw_text="Synthetic source text.",
            warnings=["synthetic warning"],
            errors=["synthetic error"],
        )

        neutral = to_neutral(original)
        restored = from_neutral(neutral)

        self.assertEqual(restored, original)
        self.assertEqual(neutral.stage, document_contract.ExtractionStage.EXTRACTED)
        self.assertTrue(
            all(
                field.decision is document_contract.ExtractionDecision.REVIEW_REQUIRED
                for field in neutral.fields
            )
        )

    def test_neutral_contract_is_not_diabetes_shaped(self):
        annotation_text = repr(document_contract.DocumentExtraction.__annotations__)
        self.assertNotIn("glucose", annotation_text.lower())
        self.assertNotIn("hba1c", annotation_text.lower())
        self.assertNotIn("insulin", annotation_text.lower())
