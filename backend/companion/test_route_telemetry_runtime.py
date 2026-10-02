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


def test_common_meta_turns_bypass_llm():
    messages = (
        "salam ça va ?",
        "tu sais faire quoi ?",
        "qui es-tu ?",
        "t'as accès à mon historique ?",
        "malek chkouen sweltek ?",
    )
    for message in messages:
        with patch("companion.conversation.record_companion_route") as route:
            reply = chat(message, memory=None, deep=object(), llm=ExplodingLLM())
        assert "Difficulté technique" not in reply
        route.assert_called_once_with("zero_model")


def test_recent_exchange_recall_bypasses_llm_even_with_phi_shaped_date():
    patient = SimpleNamespace(id=99)
    turns = [
        SimpleNamespace(
            role="assistant",
            message="Je ne trouve aucune glycémie enregistrée le 2026-10-02 entre 20:00 et 20:59.",
        ),
        SimpleNamespace(
            role="user",
            message="Quelle était ma glycémie hier à 20h ?",
        ),
    ]
    with (
        patch("companion.conversation._recent_turns", return_value=turns),
        patch("companion.conversation._append_turn"),
        patch("companion.conversation.record_companion_route") as route,
    ):
        reply = chat(
            "Qu'est-ce qu'on s'était dit juste avant ?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            patient=patient,
        )

    assert "2026-10-02" in reply
    assert "Difficulté technique" not in reply
    route.assert_called_once_with("zero_model")


def test_one_sentence_recap_bypasses_llm():
    patient = SimpleNamespace(id=100)
    turns = [
        SimpleNamespace(role="assistant", message="Réponse locale."),
        SimpleNamespace(role="user", message="Question précédente."),
    ]
    with (
        patch("companion.conversation._recent_turns", return_value=turns),
        patch("companion.conversation._append_turn"),
        patch("companion.conversation.record_companion_route") as route,
    ):
        reply = chat(
            "Peux-tu me résumer notre échange en une phrase ?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            patient=patient,
        )

    assert "En bref" in reply
    assert "Question précédente" in reply
    assert "Réponse locale" in reply
    route.assert_called_once_with("zero_model")
