import pytest

from llm.base import BaseLLMProvider, LLMResponse
from llm.pipeline import LLMPipeline, LLMPipelineModeBlocked


class CountingProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.stream_calls = 0
        self.think_calls = 0

    @property
    def model_name(self) -> str:
        return "counting-provider"

    def complete(self, system: str, user: str) -> LLMResponse:
        return LLMResponse(text="ok", model=self.model_name)

    def stream(self, system: str, user: str):
        self.stream_calls += 1
        yield "should-not-run"

    def think(self, system: str, user: str) -> tuple[str, str]:
        self.think_calls += 1
        return ("should-not-run", "reason")


def test_stream_fails_before_inner_provider_invocation():
    provider = CountingProvider()
    pipeline = LLMPipeline(provider)

    with pytest.raises(LLMPipelineModeBlocked, match="stream"):
        list(pipeline.stream("system", "user"))

    assert provider.stream_calls == 0


def test_think_fails_before_inner_provider_invocation():
    provider = CountingProvider()
    pipeline = LLMPipeline(provider)

    with pytest.raises(LLMPipelineModeBlocked, match="think"):
        pipeline.think("system", "user")

    assert provider.think_calls == 0
