import json
from types import SimpleNamespace

import pytest

from diabetes.evals.pulper_qualification import (
    FAIL_CLOSED_FORMATS,
    SUPPORTED_FORMATS,
    Score,
    build_corpus,
    critical_facts,
    parser_route_budget_ok,
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
from llm.tests.pulper_qualification_provider import (
    SyntheticQualificationTextProvider,
    bounded_synthetic_transport_probe,
    classify_live_reply_shape,
    classify_upstream_http_status,
)
from media.documents.extractors.pdf import extract_pdf


@pytest.mark.parametrize(
    ("retries", "accepted"),
    [(-1, False), (0, True), (1, False), (4, False), (5, False), ("4", False)],
)
def test_parser_route_budget_counts_live_cases_and_bounds_transport_retries(retries, accepted):
    counters = {
        "live_groq": 4,
        "deterministic_fixture": 3,
        "groq_strict_json_retries": retries,
    }
    assert parser_route_budget_ok(counters) is accepted
    assert not parser_route_budget_ok({**counters, "live_groq": 5})
    assert not parser_route_budget_ok({**counters, "deterministic_fixture": 2})


def test_synthetic_protocol_probe_bounds_calls_and_never_records_content(monkeypatch):
    monkeypatch.setenv("PULPER_SYNTHETIC_QUALIFICATION", "1")
    observed_pairs = []

    def create(**kwargs):
        assert kwargs["max_completion_tokens"] == 384
        assert kwargs["response_format"]["type"] == "json_schema"
        observed_pairs.append((
            kwargs["messages"][0]["content"],
            kwargs["messages"][1]["content"],
        ))
        reply = ('{"reply":"not json"}' if "Mandatory formatting:" not in
                 kwargs["messages"][1]["content"] else
                 '{"reply":"{\\\"document_type\\\":\\\"lab_report\\\"}"}')
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])

    delegate = SimpleNamespace(
        model="openai/gpt-oss-120b",
        timeout_seconds=15.0,
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )
    result = bounded_synthetic_transport_probe(delegate)
    assert len(observed_pairs) == 2
    assert "Place ALL requested clinical fields" in observed_pairs[0][1]
    assert "Extract medical data" in observed_pairs[0][1]
    assert "Mandatory formatting:" not in observed_pairs[0][1]
    assert "Mandatory formatting:" in observed_pairs[1][1]
    assert all("You are a medical document parser" in pair[0] for pair in observed_pairs)
    assert result == [
        {"variant": "pdf_base_preface", "status": "http_200", "shape": "reply_non_json"},
        {"variant": "pdf_strict_inner_json", "status": "http_200", "shape": "reply_json_object"},
    ]
    assert "SECRET" not in json.dumps(result)


def test_synthetic_live_text_seam_forwards_reply_preface_without_model_data():
    captured = []
    class Delegate:
        def __init__(self):
            self.client = SimpleNamespace(close=lambda: None)
        def complete(self, system, user):
            captured.append((system, user))
            return LLMResponse(content='{"reply":"{}"}', provider="synthetic-delegate")
    wrapper = SyntheticQualificationTextProvider(Delegate())
    wrapper.complete("original-system", "BEGIN_UNTRUSTED_DOCUMENT\nL0001|HbA1c: 7.2 %\nEND_UNTRUSTED_DOCUMENT")
    assert wrapper.live_calls == 1
    assert wrapper.deterministic_calls == 0
    assert len(captured) == 1
    assert captured[0][0] == "original-system"
    # Product Pulper inserts the preface inside the governed/FinOps-bounded
    # prompt. The test seam must never inject it a second time.
    assert captured[0][1].startswith("BEGIN_UNTRUSTED_DOCUMENT")
    assert captured[0][1].endswith("END_UNTRUSTED_DOCUMENT")


def test_upstream_http_status_diagnostics_show_only_numeric_codes():
    class UpstreamError(Exception):
        status_code = 400

    normalized = RuntimeError("safe")
    normalized.__cause__ = UpstreamError("sensitive-ignored")
    assert classify_upstream_http_status(normalized) == "http_400"
    assert classify_upstream_http_status(RuntimeError("unknown")) == "unknown"


def test_live_reply_diagnostic_keeps_only_structure_and_never_content():
    assert classify_live_reply_shape('{"reply":"{}"}') == "reply_json_object"
    assert classify_live_reply_shape('{"reply":"not json"}') == "reply_non_json"
    assert classify_live_reply_shape('{"lab_values":{}}') == "direct_json_object"
    assert classify_live_reply_shape('bad response') == "outer_non_json"
    assert classify_live_reply_shape('{"reply":42}') == "reply_not_string"


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
    assert _PARSE_PROMPT_VERSION == "pulper-parse-v5-fasting-lab-routing"
    rendered = _PARSE_PROMPT_TEMPLATE.format(text="L0001|HbA1c: 7.2 %")
    assert "null" not in rendered.lower()
    assert "omit every absent field" in rendered.lower()
    assert "Fasting glucose: 126 mg/dL" in rendered
    assert "lab_values.fasting_glucose_mgdl" in rendered
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



def test_groq_json_object_completion_is_one_call_without_reply_wrapper():
    from llm.lowcost_openai_compatible import OpenAICompatibleLowCostProvider

    requests = []

    def create(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(choices=[
            SimpleNamespace(message=SimpleNamespace(content='{"lab_values":{}}'))
        ])

    provider = object.__new__(OpenAICompatibleLowCostProvider)
    provider.provider_id = "groq"
    provider.model = "openai/gpt-oss-120b"
    provider.timeout_seconds = 15.0
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    reply = provider.complete_json_object(
        "You extract JSON.", "Return JSON for L0001|HbA1c: 7.2 %"
    )
    assert json.loads(reply.content) == {"lab_values": {}}
    assert len(requests) == 1
    assert requests[0]["response_format"] == {"type": "json_object"}
    assert requests[0]["temperature"] == 0.0
    assert requests[0]["reasoning_effort"] == "low"
    assert requests[0]["max_completion_tokens"] == 384
    assert requests[0]["timeout"] == 15.0
    assert "reply" not in reply.content


def test_synthetic_qualification_routes_live_document_to_direct_json_once():
    class Delegate:
        def __init__(self):
            self.client = SimpleNamespace(close=lambda: None)
            self.calls = 0

        def complete_json_object(self, _system, _user):
            self.calls += 1
            return LLMResponse(content='{"lab_values":{}}', provider="live-delegate")

        def complete(self, _system, _user):
            raise AssertionError("legacy double JSON must not be called")

    delegate = Delegate()
    provider = SyntheticQualificationTextProvider(delegate)
    prompt = (
        "qualification\\nBEGIN_UNTRUSTED_DOCUMENT\\n"
        "L0001|Fasting glucose: 126 mg/dL\\nEND_UNTRUSTED_DOCUMENT"
    )
    result = provider.complete_json_object("system", prompt)
    assert json.loads(result.content) == {"lab_values": {}}
    assert delegate.calls == 1
    assert provider.live_calls == 1
    assert provider.deterministic_calls == 0
    assert provider.live_reply_shapes == ["direct_json_object"]


@pytest.mark.parametrize("payload,accepted", [
    (
        {
            "document_type": "lab_report",
            "confidence": 0.99,
            "lab_values": {"fasting_glucose_mgdl": 126},
            "evidence": {
                "lab_values.fasting_glucose_mgdl": {
                    "r": "L0001", "v": "126"
                }
            },
        },
        True,
    ),
    ({"reply": "Fasting glucose: 126 mg/dL"}, False),
])
def test_pulper_groq_direct_json_preserves_verified_source_or_fails_closed(
    monkeypatch, payload, accepted
):
    from diabetes.services.documents import pulper

    class Provider:
        provider_policy_key = "groq"
        model_name = "openai/gpt-oss-120b"
        calls = 0

        def complete_json_object(self, system, user):
            self.calls += 1
            assert "The API forces a strict JSON object" not in user
            assert "Fasting glucose: 126 mg/dL" in user
            return LLMResponse(
                content=json.dumps(payload), provider=self.model_name
            )

        def complete(self, _system, _user):
            raise AssertionError("legacy double JSON must not be called")

    provider = Provider()
    monkeypatch.setattr("llm.factory.get_llm", lambda: provider)
    monkeypatch.setattr(pulper, "assert_ai_egress_allowed", lambda _: None)
    output = PulperOutput(source_sha256="a" * 64)
    pulper._parse_with_llm(output, "Fasting glucose: 126 mg/dL")
    assert provider.calls == 1
    assert output.prompt_version == "pulper-parse-v7-groq-direct-json"
    if accepted:
        assert output.errors == []
        assert output.lab_values.fasting_glucose_mgdl == 126.0
        proof = output.lab_values.evidence["fasting_glucose_mgdl"]
        assert proof.verified and proof.source_ref == "text:L0001"
        assert proof.raw_value == "126"
    else:
        assert output.errors
        assert output.lab_values.fasting_glucose_mgdl is None
        assert not output.lab_values.evidence



def test_groq_json_object_never_bypasses_processor_policy_or_finops(monkeypatch):
    from core.ai_processor_policy import AIProcessorPolicyDenied
    from llm import factory

    class Provider:
        provider_policy_key = "groq"

        def __init__(self):
            self.calls = 0

        def complete(self, _system, _user):
            raise AssertionError("wrong completion path")

        def complete_json_object(self, _system, _user):
            self.calls += 1
            return LLMResponse(content="{}", provider="openai/gpt-oss-120b")

        def stream(self, _system, _user):
            return iter(())

        def think(self, _system, _user):
            return ("", "")

    # Replace only the external policy dependencies, leaving the production
    # guarded method and its call to the FinOps gate intact.
    monkeypatch.setattr(
        factory, "get_processor_policy",
        lambda name: SimpleNamespace(external_egress=True),
    )
    monkeypatch.setattr(
        factory, "minimize_external_text_payload",
        lambda fields: SimpleNamespace(fields=fields),
    )
    monkeypatch.setattr(
        factory, "authorize_text_payload",
        lambda fields: SimpleNamespace(
            system_prompt=fields["system_prompt"],
            user_prompt=fields["user_prompt"],
            purpose="companion_chat",
        ),
    )
    def deny(*_args):
        raise AIProcessorPolicyDenied("blocked")

    monkeypatch.setattr(factory, "authorize_processor_policy", deny)
    underlying = Provider()
    guarded = factory._enforce_text_payload_policy(underlying)

    with pytest.raises(AIProcessorPolicyDenied):
        guarded.complete_json_object("system", "user")
    assert underlying.calls == 0

    monkeypatch.setattr(
        factory, "authorize_processor_policy",
        lambda *_: SimpleNamespace(external_egress=True),
    )
    reserved = []

    def enforce_reservation(**kwargs):
        reserved.append(kwargs)
        return kwargs["original_complete"](
            kwargs["payload"].system_prompt,
            kwargs["payload"].user_prompt,
        )

    monkeypatch.setattr(factory, "_execute_external_complete", enforce_reservation)
    reply = guarded.complete_json_object("system", "user")
    assert reply.content == "{}"
    assert underlying.calls == 1
    assert len(reserved) == 1
    assert reserved[0]["provider_name"] == "groq"
    assert reserved[0]["payload"].purpose == "companion_chat"
