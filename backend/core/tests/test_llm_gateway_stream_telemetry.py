from unittest.mock import patch

import pytest

from core.contracts.capabilities import Capability
from llm.usage_telemetry import current_usage_workload


class StreamProvider:
    model_name = "fake-stream-model"

    def complete(self, _system, _user):
        raise AssertionError("complete must not be used when direct streaming is enabled")

    def stream(self, _system, _user):
        yield "alpha"
        yield " beta"


class FailingStreamProvider(StreamProvider):
    def stream(self, _system, _user):
        raise RuntimeError("SECRET_STREAM_PROVIDER_BODY")
        yield  # pragma: no cover


def _gateway(provider):
    with patch("core.llm_gateway.get_llm", return_value=provider):
        from core.llm_gateway import GatewayLLM

        return GatewayLLM()


def test_direct_stream_records_content_free_usage_with_null_tokens():
    gateway = _gateway(StreamProvider())
    observed_workloads = []

    def capture_success(response, **kwargs):
        observed_workloads.append(current_usage_workload())
        assert response.content == "alpha beta"
        assert response.provider == "fake-stream-model"
        assert response.usage is None
        assert kwargs["prompt_chars"] == len("systemuser")
        assert kwargs["latency_ms"] >= 0

    with (
        patch("core.llm_gateway.medical_streaming_enabled", return_value=True),
        patch("core.llm_gateway.assert_ai_egress_allowed"),
        patch("core.llm_gateway._prepare_unstructured_prompt", side_effect=lambda text, _p: text),
        patch("core.llm_gateway.record_llm_success", side_effect=capture_success) as success,
        patch("core.llm_gateway.record_llm_failure") as failure,
    ):
        chunks = list(
            gateway.stream(
                "system",
                "user",
                capability=Capability.SUMMARIZE_APPROVED_DATA,
            )
        )

    assert chunks == ["alpha beta"]
    success.assert_called_once()
    failure.assert_not_called()
    assert observed_workloads == ["summary"]


def test_direct_stream_records_error_type_not_exception_body():
    gateway = _gateway(FailingStreamProvider())
    observed_workloads = []

    def capture_failure(**kwargs):
        observed_workloads.append(current_usage_workload())
        assert kwargs["prompt_chars"] == len("systemuser")
        assert kwargs["latency_ms"] >= 0
        assert kwargs["error_type"] == "RuntimeError"

    with (
        patch("core.llm_gateway.medical_streaming_enabled", return_value=True),
        patch("core.llm_gateway.assert_ai_egress_allowed"),
        patch("core.llm_gateway._prepare_unstructured_prompt", side_effect=lambda text, _p: text),
        patch("core.llm_gateway.record_llm_failure", side_effect=capture_failure) as failure,
        patch("core.llm_gateway.record_llm_success") as success,
    ):
        with pytest.raises(RuntimeError, match="SECRET_STREAM_PROVIDER_BODY"):
            list(gateway.stream("system", "user"))

    failure.assert_called_once()
    success.assert_not_called()
    assert observed_workloads == ["conversation"]
