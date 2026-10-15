"""Pulper-Groq transport integration contract (synthetic, no network, no patient).
This test exercises the REAL Groq adapter and REAL Pulper parser with a mocked SDK
response while keeping the existing PHI pseudonymizer and evidence shield.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from diabetes.services.documents.pulper import _parse_with_llm
from diabetes.services.documents.schema import PulperOutput
from llm.lowcost_openai_compatible import OpenAICompatibleLowCostProvider


def _provider(content: str):
    provider = object.__new__(OpenAICompatibleLowCostProvider)
    provider.provider_id = "groq"
    provider.model = "openai/gpt-oss-120b"
    provider.timeout_seconds = 15.0
    provider.client = MagicMock()
    provider.client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=None,
    )
    return provider


def _parse_with_mock_sdk(content: str, source: str):
    provider = _provider(content)
    output = PulperOutput()
    with (
        patch("diabetes.services.documents.pulper.assert_ai_egress_allowed") as gate,
        patch("llm.factory.get_llm", return_value=provider),
    ):
        _parse_with_llm(output, source)
    gate.assert_called_once()
    return output, provider.client.chat.completions.create.call_args.kwargs


def test_groq_strict_reply_envelope_preserves_verified_source_provenance():
    extraction = {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"hba1c_pct": 7.2},
        "evidence": {"lab_values.hba1c_pct": {"r": "L0001", "v": "7.2"}},
    }
    result, request = _parse_with_mock_sdk(
        json.dumps({"reply": json.dumps(extraction)}),
        "HbA1c: 7.2 %",
    )
    assert result.errors == []
    assert result.parser_model == "openai/gpt-oss-120b"
    assert result.prompt_version == "pulper-parse-v6-fasting-evidence"
    assert result.lab_values.hba1c_pct == 7.2
    evidence = result.lab_values.evidence["hba1c_pct"]
    assert evidence.verified is True
    assert evidence.source_ref == "text:L0001"
    assert evidence.raw_value == "7.2"
    assert request["response_format"]["json_schema"]["strict"] is True
    assert request["response_format"]["json_schema"]["schema"]["required"] == ["reply"]
    assert request["extra_body"] == {"include_reasoning": False}
    assert "reasoning_format" not in str(request)


def test_groq_strict_reply_fasting_glucose_grounded_and_no_timestamp():
    extraction = {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"fasting_glucose_mgdl": 126},
        "evidence": {
            "lab_values.fasting_glucose_mgdl": {"r": "L0001", "v": "126"},
        },
    }
    result, request = _parse_with_mock_sdk(
        json.dumps({"reply": json.dumps(extraction)}),
        "Fasting glucose: 126 mg/dL",
    )
    assert result.errors == []
    assert result.lab_values.fasting_glucose_mgdl == 126
    assert result.lab_values.evidence["fasting_glucose_mgdl"].verified
    assert result.glucose_readings == []
    assert request["response_format"]["json_schema"]["strict"] is True


def test_groq_fasting_glucose_exemplar_cannot_insert_unsourced_value():
    extraction = {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"fasting_glucose_mgdl": 126},
        "evidence": {
            "lab_values.fasting_glucose_mgdl": {"r": "L0001", "v": "126"},
        },
    }
    result, _ = _parse_with_mock_sdk(
        json.dumps({"reply": json.dumps(extraction)}),
        "An unrelated HbA1c report with no glucose number",
    )
    assert result.lab_values.fasting_glucose_mgdl is None
    assert not result.lab_values.evidence.get("fasting_glucose_mgdl")


@pytest.mark.parametrize(
    "content",
    [
        '{"reply":"[]"}',
        '{"reply":4}',
        '{"reply":"{}","extra":"unsafe"}',
        '{"reply":"non JSON"}',
    ],
)
def test_groq_transport_wrong_shape_fails_closed(content):
    result, _ = _parse_with_mock_sdk(content, "HbA1c: 7.2 %")
    assert result.lab_values.hba1c_pct is None
    assert result.lab_values.evidence == {}
    assert result.errors
    assert result.confidence == 0.1


def test_direct_json_still_works_for_other_governed_provider_paths():
    payload = {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"fasting_glucose_mgdl": 126},
        "evidence": {"lab_values.fasting_glucose_mgdl": {"r": "L0001", "v": "126"}},
    }
    result, _ = _parse_with_mock_sdk(json.dumps(payload), "Fasting glucose: 126 mg/dL")
    assert result.errors == []
    assert result.lab_values.fasting_glucose_mgdl == 126
    assert result.lab_values.evidence["fasting_glucose_mgdl"].verified
