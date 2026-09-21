from types import SimpleNamespace
from unittest.mock import patch

from companion import conversation
from core.contracts.advice_decision import AdviceDecision


class ExplodingLLM:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("LLM must not be called when policy denies narration")


def test_chat_policy_denial_blocks_llm_before_narration():
    with patch(
        "companion.conversation.authorize_narration",
        return_value=AdviceDecision.fail_closed(language="fr"),
    ):
        reply = conversation.chat(
            "Explique-moi ce que je dois faire.",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=None,
        )

    assert "Difficulté technique momentanée" in reply


def test_stream_policy_denial_blocks_llm_before_any_chunk():
    with patch(
        "companion.conversation.authorize_narration",
        return_value=AdviceDecision.fail_closed(language="fr"),
    ):
        chunks = list(
            conversation.stream_chat(
                "Explique-moi ce que je dois faire.",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=None,
            )
        )

    assert chunks == ["Difficulté technique momentanée. Réessaie dans un instant."]


def test_policy_exception_fails_closed_before_llm():
    with patch(
        "companion.conversation.authorize_narration",
        side_effect=RuntimeError("policy unavailable"),
    ):
        reply = conversation.chat(
            "Question libre",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=None,
        )

    assert "Difficulté technique momentanée" in reply


def test_valid_policy_is_passed_into_prompt_builder_before_model_call():
    captured = {}

    def build_prompt(**kwargs):
        captured["decision"] = kwargs["advice_decision"]
        captured["context"] = kwargs["preloaded_context"]
        return (
            "fr",
            kwargs["preloaded_context"],
            "system",
            "user",
        )

    llm = SimpleNamespace(
        complete=lambda *_args, **_kwargs: SimpleNamespace(
            content='{"reply":"Réponse descriptive."}'
        )
    )

    with (
        patch("companion.conversation._build_runtime_prompt", side_effect=build_prompt),
        patch(
            "companion.conversation._finalize_reply",
            return_value="Réponse descriptive.",
        ),
        patch(
            "companion.conversation._retry_finalized_repeat",
            return_value="Réponse descriptive.",
        ),
    ):
        reply = conversation.chat(
            "Peux-tu m'expliquer cette situation ?",
            memory=None,
            deep=object(),
            llm=llm,
            language="fr",
            patient=None,
        )

    assert reply == "Réponse descriptive."
    assert captured["decision"].rule_id == "core.narration.conversation"
    assert captured["decision"].authority_level.value == "L0"
    assert captured["context"].analysis_status == "insufficient_data"
