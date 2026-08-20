from types import SimpleNamespace
from unittest.mock import patch

from companion.conversation import chat, stream_chat
from core.contracts.domain_context import DomainContext
from llm.base import LLMResponse


class ExplodingLLM:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("LLM must not be called for bypass routes")

    def stream(self, *_args, **_kwargs):
        raise AssertionError("LLM stream must not be called for bypass routes")


class FakeLLM:
    def complete(self, *_args, **_kwargs):
        return LLMResponse(content='{"reply":"OK"}', provider="fake")


class Deep:
    consecutive_log_days = 0

    def save(self):
        pass


def test_chat_records_zero_model_route_once():
    with patch("companion.conversation.record_companion_route") as route:
        reply = chat("Salut", memory=None, deep=object(), llm=ExplodingLLM())

    assert "Bonjour" in reply
    route.assert_called_once_with("zero_model")


def test_chat_records_safety_route_once_without_llm():
    with (
        patch("companion.conversation._safety_reply", return_value="SAFE"),
        patch("companion.conversation.record_companion_route") as route,
    ):
        reply = chat("synthetic", memory=None, deep=object(), llm=ExplodingLLM())

    assert reply == "SAFE"
    route.assert_called_once_with("safety")


def test_chat_records_llm_route_once():
    with (
        patch("companion.conversation._safety_reply", return_value=None),
        patch("companion.conversation.exact_chitchat_reply", return_value=None),
        patch(
            "companion.conversation._build_runtime_prompt",
            return_value=(
                "fr",
                DomainContext.empty(language="fr"),
                "system",
                "user",
            ),
        ),
        patch("companion.conversation.record_companion_route") as route,
    ):
        reply = chat("synthetic", memory=None, deep=Deep(), llm=FakeLLM())

    assert reply == "OK"
    route.assert_called_once_with("llm")


def test_stream_records_zero_model_route_once():
    with patch("companion.conversation.record_companion_route") as route:
        chunks = list(
            stream_chat("merci", memory=None, deep=object(), llm=ExplodingLLM())
        )

    assert chunks == ["Avec plaisir 🙏"]
    route.assert_called_once_with("zero_model")
