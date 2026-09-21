from types import SimpleNamespace
from unittest.mock import patch

from companion import conversation
from core.clinical_policy import (
    NarrationMode,
    NarrationPolicyRequest,
    authorize_narration,
)
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext


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

    assert len(chunks) == 1
    assert "Difficulté technique momentanée" in chunks[0]
    assert "évaluation" in chunks[0]


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


def test_l0_prompt_never_loads_companion_clinical_context():
    decision = authorize_narration(
        NarrationPolicyRequest(
            mode=NarrationMode.PRACTICAL,
            language="fr",
            has_approved_context=False,
            has_sufficient_data=False,
            analysis_status="insufficient_data",
        )
    )
    deep = SimpleNamespace(consecutive_log_days=0)

    with (
        patch("companion.conversation._recent_turns", return_value=[]),
        patch(
            "companion.conversation._get_companion_context",
            side_effect=AssertionError("L0 must not load clinical companion context"),
        ),
        patch("companion.conversation.compute_state", return_value=object()),
        patch("companion.conversation.state_to_prompt", return_value="safe-state"),
        patch(
            "companion.conversation.get_tone_instruction",
            return_value="safe-tone",
        ),
    ):
        language, ctx, system, _prompt = conversation._build_runtime_prompt(
            message="Parlons simplement.",
            memory=None,
            deep=deep,
            language="fr",
            patient=None,
            context_days=14,
            streaming=False,
            preloaded_context=DomainContext.empty(language="fr"),
            advice_decision=decision,
        )

    assert language == "fr"
    assert ctx.analysis_status == "insufficient_data"
    assert "Contexte de session approuvé" not in system
    assert "Contexte compagnon gouverné" not in system
    assert "[ADVICE_AUTHORITY]" in system


def _food_resolution():
    return AdviceResolution(
        decision=AdviceDecision(
            intent="food_permission",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.food.permission",
            rule_version="1",
            allowed_actions=("review_portion_and_carbohydrate_context",),
            forbidden_actions=("approve_food_personally",),
            evidence_refs=("ADA_SOC_2026_SECTION_5",),
        ),
        reply="Réponse FOOD déterministe.",
    )


def test_module_food_decision_short_circuits_llm_in_chat():
    patient = SimpleNamespace(id=42, first_name="")
    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_food_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.record_companion_route") as record_route,
        patch("companion.conversation._append_turn"),
    ):
        reply = conversation.chat(
            "je peux manger un mille feuille !?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Réponse FOOD déterministe."
    record_route.assert_called_once_with("policy_rule")


def test_module_food_decision_short_circuits_llm_in_stream():
    patient = SimpleNamespace(id=42, first_name="")
    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_food_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.record_companion_route") as record_route,
        patch("companion.conversation._append_turn"),
    ):
        chunks = list(
            conversation.stream_chat(
                "je peux manger un mille feuille !?",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    assert chunks == ["Réponse FOOD déterministe."]
    record_route.assert_called_once_with("policy_rule")


def test_module_food_reply_is_verified_before_chat_storage():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, _resolution, candidate):
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_food_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
    ):
        reply = conversation.chat(
            "je peux manger un mille feuille !?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Réponse FOOD déterministe."
    assert events == ["verify", "assistant_store"]


def test_module_food_reply_is_verified_before_stream_storage_and_emit():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, _resolution, candidate):
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_food_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
    ):
        chunks = list(
            conversation.stream_chat(
                "je peux manger un mille feuille !?",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    events.append("observed_emit")
    assert chunks == ["Réponse FOOD déterministe."]
    assert events == ["verify", "assistant_store", "observed_emit"]


def test_module_verifier_failure_blocks_governed_reply_in_chat():
    patient = SimpleNamespace(id=42, first_name="")
    stored = []

    def append(_patient, role, message):
        if role == "assistant":
            stored.append(message)

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_food_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=PermissionError("verifier rejected"),
        ),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        reply = conversation.chat(
            "je peux manger un mille feuille !?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply != "Réponse FOOD déterministe."
    assert "Difficulté technique momentanée" in reply
    assert stored == [reply]
    record_route.assert_called_once_with("policy_denied")


def test_module_verifier_failure_blocks_governed_reply_before_stream_emit():
    patient = SimpleNamespace(id=42, first_name="")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_food_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=PermissionError("verifier rejected"),
        ),
        patch("companion.conversation._append_turn"),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        chunks = list(
            conversation.stream_chat(
                "je peux manger un mille feuille !?",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    assert chunks != ["Réponse FOOD déterministe."]
    assert len(chunks) == 1
    assert "Difficulté technique momentanée" in chunks[0]
    record_route.assert_called_once_with("policy_denied")


def test_module_advice_exception_fails_closed_and_never_calls_llm():
    patient = SimpleNamespace(id=42, first_name="")
    with (
        patch(
            "companion.conversation.get_advice_resolution",
            side_effect=RuntimeError("food rule unavailable"),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.record_companion_route") as record_route,
        patch("companion.conversation._append_turn"),
    ):
        reply = conversation.chat(
            "je peux manger un mille feuille !?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert "Difficulté technique momentanée" in reply
    record_route.assert_called_once_with("policy_denied")
