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


def test_runtime_passes_previous_user_turn_to_module_advice_resolution():
    patient = SimpleNamespace(id=42, first_name="")
    previous = SimpleNamespace(role="user", message="Je peux manger un gâteau ?")
    captured = {}

    def resolve(*args, **kwargs):
        captured["previous_user_message"] = kwargs.get("previous_user_message")
        return _food_resolution()

    with (
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation._recent_turns", return_value=[previous]),
        patch("companion.conversation.get_advice_resolution", side_effect=resolve),
    ):
        _language, _ctx, _decision, resolution = (
            conversation._authorize_runtime_narration(
                "Et du riz ?",
                patient,
                "fr",
                14,
            )
        )

    assert resolution is not None
    assert captured["previous_user_message"] == "Je peux manger un gâteau ?"


def _monitoring_resolution():
    return AdviceResolution(
        decision=AdviceDecision(
            intent="monitoring_interpretation",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.monitoring.descriptive_interpretation",
            rule_version="1",
            allowed_actions=("explain_recorded_monitoring_summary",),
            forbidden_actions=(
                "diagnose_from_monitoring",
                "declare_clinical_improvement_or_deterioration",
                "calculate_insulin_dose",
                "change_treatment",
                "recommend_compensatory_activity",
            ),
            evidence_refs=("rule.metric.recorded-range-fractions.v1",),
            limitations=("descriptive_monitoring_only",),
        ),
        reply="Réponse MONITORING déterministe.",
    )


def test_module_monitoring_decision_short_circuits_llm_and_verifies_before_chat_storage():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.monitoring.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_monitoring_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        reply = conversation.chat(
            "Explique-moi ma tendance glycémique cette semaine.",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Réponse MONITORING déterministe."
    assert events == ["verify", "assistant_store"]
    record_route.assert_called_once_with("policy_rule")


def test_module_monitoring_decision_short_circuits_llm_and_verifies_before_stream_emit():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.monitoring.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_monitoring_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        chunks = list(
            conversation.stream_chat(
                "Explique-moi ma tendance glycémique cette semaine.",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    events.append("observed_emit")
    assert chunks == ["Réponse MONITORING déterministe."]
    assert events == ["verify", "assistant_store", "observed_emit"]
    record_route.assert_called_once_with("policy_rule")


def _activity_resolution():
    return AdviceResolution(
        decision=AdviceDecision(
            intent="activity_context",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.activity.descriptive_context",
            rule_version="1",
            allowed_actions=("explain_recorded_activity_context",),
            forbidden_actions=(
                "infer_activity_causality",
                "prescribe_exercise",
                "recommend_compensatory_activity",
                "calculate_insulin_dose",
                "change_treatment",
                "diagnose_from_activity",
            ),
            evidence_refs=("rule.pattern.low-with-recorded-activity.v1",),
            limitations=("temporal_or_longitudinal_association_does_not_establish_causality",),
        ),
        reply="Réponse ACTIVITY déterministe.",
    )


def test_module_activity_decision_short_circuits_llm_and_verifies_before_chat_storage():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.activity.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch("companion.conversation.get_advice_resolution", return_value=_activity_resolution()),
        patch("companion.conversation._get_context", return_value=DomainContext.empty(language="fr")),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        reply = conversation.chat(
            "Est-ce que le sport est lié à mes baisses de glycémie ?",
            memory=None, deep=object(), llm=ExplodingLLM(), language="fr", patient=patient,
        )

    assert reply == "Réponse ACTIVITY déterministe."
    assert events == ["verify", "assistant_store"]
    record_route.assert_called_once_with("policy_rule")


def test_module_activity_decision_short_circuits_llm_and_verifies_before_stream_emit():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.activity.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch("companion.conversation.get_advice_resolution", return_value=_activity_resolution()),
        patch("companion.conversation._get_context", return_value=DomainContext.empty(language="fr")),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        chunks = list(conversation.stream_chat(
            "Est-ce que le sport est lié à mes baisses de glycémie ?",
            memory=None, deep=object(), llm=ExplodingLLM(), language="fr", patient=patient,
        ))

    events.append("observed_emit")
    assert chunks == ["Réponse ACTIVITY déterministe."]
    assert events == ["verify", "assistant_store", "observed_emit"]
    record_route.assert_called_once_with("policy_rule")


def _symptom_triage_resolution():
    return AdviceResolution(
        decision=AdviceDecision(
            intent="symptom_triage",
            authority_level=AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
            decision=AdviceDisposition.ESCALATE,
            rule_id="diabetes.symptom.professional_triage",
            rule_version="1",
            forbidden_actions=(
                "diagnose_from_symptom",
                "attribute_symptom_to_glucose",
                "reassure_symptom_is_benign",
                "downgrade_emergency_urgency",
                "delay_professional_assessment",
                "calculate_insulin_dose",
                "change_treatment",
                "prescribe_symptom_treatment",
            ),
            evidence_refs=("rule.triage.symptom-professional-escalation.v1",),
            limitations=("shared_core_emergency_gate_has_precedence",),
            escalation="contact_clinical_team_for_symptom_assessment",
        ),
        reply="Réponse SYMPTOM_TRIAGE déterministe.",
    )


def test_module_symptom_triage_short_circuits_llm_and_verifies_before_chat_storage():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.symptom.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_symptom_triage_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        reply = conversation.chat(
            "J'ai des nausées et mal au ventre aujourd'hui.",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Réponse SYMPTOM_TRIAGE déterministe."
    assert events == ["verify", "assistant_store"]
    record_route.assert_called_once_with("policy_rule")


def test_module_symptom_triage_short_circuits_llm_and_verifies_before_stream_emit():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.symptom.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_symptom_triage_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        chunks = list(
            conversation.stream_chat(
                "J'ai des nausées et mal au ventre aujourd'hui.",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    events.append("observed_emit")
    assert chunks == ["Réponse SYMPTOM_TRIAGE déterministe."]
    assert events == ["verify", "assistant_store", "observed_emit"]
    record_route.assert_called_once_with("policy_rule")


def _clinician_prep_resolution():
    return AdviceResolution(
        decision=AdviceDecision(
            intent="clinician_prep",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.clinician_prep.structured_brief",
            rule_version="1",
            allowed_actions=(
                "prepare_clinician_discussion",
                "summarize_approved_consultation_brief",
            ),
            forbidden_actions=(
                "diagnose_from_consultation_brief",
                "infer_causality_from_consultation_brief",
                "calculate_insulin_dose",
                "change_treatment",
                "prescribe_treatment",
                "override_clinician",
                "decide_urgency",
                "invent_missing_clinical_data",
            ),
            evidence_refs=("rule.consultation.preparation.v1",),
            limitations=("consultation_brief_structured_fields_only",),
        ),
        reply="Réponse CLINICIAN_PREP déterministe.",
    )


def test_module_clinician_prep_short_circuits_llm_and_verifies_before_chat_storage():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.clinician_prep.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_clinician_prep_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        reply = conversation.chat(
            "Aide-moi à préparer les questions pour mon médecin.",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Réponse CLINICIAN_PREP déterministe."
    assert events == ["verify", "assistant_store"]
    record_route.assert_called_once_with("policy_rule")


def test_module_clinician_prep_short_circuits_llm_and_verifies_before_stream_emit():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.clinician_prep.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_clinician_prep_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        chunks = list(
            conversation.stream_chat(
                "Aide-moi à préparer les questions pour mon médecin.",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    events.append("observed_emit")
    assert chunks == ["Réponse CLINICIAN_PREP déterministe."]
    assert events == ["verify", "assistant_store", "observed_emit"]
    record_route.assert_called_once_with("policy_rule")


def _longitudinal_resolution():
    return AdviceResolution(
        decision=AdviceDecision(
            intent="longitudinal_personalization",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.longitudinal.descriptive_personalization",
            rule_version="1",
            allowed_actions=("describe_governed_longitudinal_observation",),
            forbidden_actions=(
                "infer_causality",
                "infer_treatment_response",
                "predict_future_outcome",
                "diagnose_from_longitudinal_history",
                "calculate_insulin_dose",
                "change_treatment",
                "promote_heuristic_inference",
                "invent_longitudinal_facts",
            ),
            evidence_refs=("rule.personal-response.repetition.v1",),
            limitations=("certified_companion_context_only",),
        ),
        reply="Réponse LONGITUDINAL déterministe.",
    )


def test_module_longitudinal_personalization_short_circuits_llm_and_verifies_before_chat_storage():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.longitudinal.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_longitudinal_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        reply = conversation.chat(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Réponse LONGITUDINAL déterministe."
    assert events == ["verify", "assistant_store"]
    record_route.assert_called_once_with("policy_rule")


def test_module_longitudinal_personalization_short_circuits_llm_and_verifies_before_stream_emit():
    patient = SimpleNamespace(id=42, first_name="")
    events = []

    def verify(_patient_id, resolution, candidate):
        assert resolution.decision.rule_id.startswith("diabetes.longitudinal.")
        events.append("verify")
        return candidate

    def append(_patient, role, _message):
        if role == "assistant":
            events.append("assistant_store")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=_longitudinal_resolution(),
        ),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.verify_advice_reply", side_effect=verify),
        patch("companion.conversation._append_turn", side_effect=append),
        patch("companion.conversation.record_companion_route") as record_route,
    ):
        chunks = list(
            conversation.stream_chat(
                "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
                memory=None,
                deep=object(),
                llm=ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )

    events.append("observed_emit")
    assert chunks == ["Réponse LONGITUDINAL déterministe."]
    assert events == ["verify", "assistant_store", "observed_emit"]
    record_route.assert_called_once_with("policy_rule")
