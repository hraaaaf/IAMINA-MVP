import json
from types import SimpleNamespace

import pytest

from diabetes.evals.pulper_qualification import (
    FAIL_CLOSED_FORMATS,
    SUPPORTED_FORMATS,
    Score,
    build_corpus,
    critical_facts,
    score_facts,
)
from diabetes.services.documents.neutral_adapter import to_neutral
from diabetes.services.documents.pulper import _PARSE_PROMPT_TEMPLATE, _PARSE_PROMPT_VERSION
from diabetes.services.documents.schema import (
    FieldEvidence,
    GlucoseReading,
    LabValues,
    PulperOutput,
)
from llm.base import LLMResponse
from llm.tests.pulper_qualification_provider import SyntheticQualificationTextProvider
from media.documents.extractors.pdf import extract_pdf


def test_supported_and_fail_closed_format_contract_is_explicit():
    assert SUPPORTED_FORMATS == {
        "pdf", "docx", "csv", "xlsx", "xls", "jpeg", "png", "webp"
    }
    assert FAIL_CLOSED_FORMATS == {"pdf_scanned", "bmp", "tiff", "heic"}
    assert SUPPORTED_FORMATS.isdisjoint(FAIL_CLOSED_FORMATS)


def test_pdf_golden_fixture_is_admissible_digital_pdf():
    pytest.importorskip("reportlab")
    pytest.importorskip("xlwt")
    case = next(case for case in build_corpus() if case.case_id == "pdf-hba1c")
    text, is_scanned = extract_pdf(case.payload)

    assert is_scanned is False
    assert len(text.strip()) > 50
    assert "HbA1c: 7.2 %" in text


def test_sparse_prompt_contract_stays_versioned_and_placeholder_free():
    assert _PARSE_PROMPT_VERSION == "pulper-parse-v4-sparse-output"
    rendered = _PARSE_PROMPT_TEMPLATE.format(text="L0001|HbA1c: 7.2 %")
    assert "null" not in rendered.lower()
    assert "omit every absent field" in rendered.lower()
    assert '"lab_values":{"hba1c_pct":7.2}' in rendered


def test_synthetic_image_parser_is_deterministic_and_other_text_stays_live():
    class Delegate:
        def __init__(self):
            self.client = SimpleNamespace(close=lambda: None)
            self.calls = 0

        def complete(self, _system: str, _user: str) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="{}", provider="live-delegate")

    delegate = Delegate()
    provider = SyntheticQualificationTextProvider(delegate)
    prompt = (
        "qualification\nBEGIN_UNTRUSTED_DOCUMENT\n"
        "L0001|HbA1c: 7.4 %\nEND_UNTRUSTED_DOCUMENT"
    )

    deterministic = provider.complete("system", prompt)
    payload = json.loads(deterministic.content)
    assert payload["lab_values"]["hba1c_pct"] == 7.4
    assert payload["evidence"]["lab_values.hba1c_pct"] == {
        "r": "L0001",
        "v": "7.4",
    }
    assert deterministic.provider == "qualification-deterministic-parser-v1"
    assert provider.deterministic_calls == 1
    assert provider.live_calls == 0
    assert delegate.calls == 0

    live_prompt = (
        "qualification\nBEGIN_UNTRUSTED_DOCUMENT\n"
        "L0001|HbA1c: 7.2 %\nEND_UNTRUSTED_DOCUMENT"
    )
    live = provider.complete("system", live_prompt)
    assert live.provider == "live-delegate"
    assert provider.deterministic_calls == 1
    assert provider.live_calls == 1
    assert delegate.calls == 1


def test_score_facts_counts_wrong_values_as_fp_and_fn():
    score = score_facts(
        {"lab_values.hba1c_pct": 7.2, "lab_values.fasting_glucose_mgdl": 126.0},
        {"lab_values.hba1c_pct": "7.2", "lab_values.fasting_glucose_mgdl": "127"},
    )
    assert score == Score(true_positive=1, false_positive=1, false_negative=1)
    assert score.precision == 0.5
    assert score.recall == 0.5


def test_critical_facts_preserve_explicit_timestamp_offset():
    output = PulperOutput(
        lab_values=LabValues(hba1c_pct=7.2),
        glucose_readings=[
            GlucoseReading(value_mgdl=111.0, timestamp="2026-08-20T08:15:00+01:00")
        ],
    )
    assert critical_facts(output) == {
        "lab_values.hba1c_pct": "7.2",
        "glucose_readings[0].value_mgdl": "111",
        "glucose_readings[0].timestamp": "2026-08-20T08:15:00+01:00",
    }


def test_verified_evidence_does_not_auto_accept_neutral_field():
    output = PulperOutput(
        source_sha256="a" * 64,
        extractor="qualification.synthetic",
        extractor_version="1",
        lab_values=LabValues(
            hba1c_pct=7.2,
            evidence={
                "hba1c_pct": FieldEvidence(
                    raw_value="7.2",
                    source_ref="text:L0001",
                    verified=True,
                )
            },
        ),
    )
    field = next(item for item in to_neutral(output).fields if item.code == "hba1c_pct")
    assert field.provenance is not None
    assert field.provenance.evidence_verified is True
    assert field.decision.value == "review_required"
