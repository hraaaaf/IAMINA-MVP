from unittest import TestCase

from core.contracts.document_extraction import (
    DocumentExtraction,
    ExtractedField,
    ExtractedRecord,
)
from diabetes.services.documents.neutral_adapter import from_neutral


class NeutralDocumentAdapterFixtureTest(TestCase):
    def test_neutral_fixture_is_consumed_by_diabetes_adapter(self):
        fixture = DocumentExtraction(
            document_type="lab_report",
            source_format="pdf",
            confidence=0.88,
            fields=(
                ExtractedField(code="hba1c_pct", value=6.4, unit="%", confidence=0.88),
                ExtractedField(
                    code="clinical_notes",
                    value="Synthetic neutral fixture.",
                    confidence=0.88,
                ),
            ),
            records=(
                ExtractedRecord(
                    record_type="glucose_reading",
                    fields=(
                        ExtractedField(
                            code="value_mgdl",
                            value=118.0,
                            unit="mg/dL",
                            confidence=0.88,
                        ),
                        ExtractedField(
                            code="context",
                            value="fasting",
                            confidence=0.88,
                        ),
                    ),
                ),
                ExtractedRecord(
                    record_type="medication",
                    fields=(
                        ExtractedField(code="name", value="SyntheticMed", confidence=0.88),
                        ExtractedField(code="dose", value="500 mg", confidence=0.88),
                    ),
                ),
            ),
            warnings=("synthetic warning",),
            errors=(),
            extracted_text="Synthetic neutral source text.",
        )

        adapted = from_neutral(fixture)

        self.assertEqual(adapted.document_type, "lab_report")
        self.assertEqual(adapted.source_format, "pdf")
        self.assertEqual(adapted.lab_values.hba1c_pct, 6.4)
        self.assertEqual(len(adapted.glucose_readings), 1)
        self.assertEqual(adapted.glucose_readings[0].value_mgdl, 118.0)
        self.assertEqual(adapted.glucose_readings[0].context, "fasting")
        self.assertEqual(len(adapted.medications), 1)
        self.assertEqual(adapted.medications[0].name, "SyntheticMed")
        self.assertEqual(adapted.raw_text, "Synthetic neutral source text.")
        self.assertEqual(adapted.warnings, ["synthetic warning"])
