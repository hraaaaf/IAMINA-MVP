from types import SimpleNamespace
from unittest.mock import patch

from companion.conversation import _response_mode, _shadow_narration_envelope
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution


def test_multilingual_emotional_messages_route_to_emotional_mode():
    messages = (
        "Franchement j'en ai marre de penser au diabète tous les jours, ça me fatigue.",
        "I'm honestly tired of thinking about diabetes every day. It's exhausting.",
        "بصراحة تعبت من التفكير في السكري كل يوم، هذا مرهق.",
        "بصراحة عييت من التفكير فالسكري كل نهار، راه تعبني.",
        "بصراحة تعبت من التفكير بالسكري كل يوم، الموضوع مرهقني.",
    )
    for message in messages:
        assert _response_mode(message) == "emotional", message


def test_multilingual_clinician_requests_route_to_clinician_mode():
    messages = (
        "Aide-moi à préparer ce que je dois demander à mon médecin.",
        "Help me prepare what I should ask my doctor.",
        "ساعدني في تحضير ما يجب أن أسأله للطبيب.",
        "عاوني غير نوجد شنو نسول الطبيب على هاد المشكل.",
        "ساعدني أجهز وش أسأل الدكتور عن هالمشكلة.",
    )
    for message in messages:
        assert _response_mode(message) == "clinician_prep", message


def test_neutral_arabic_tracking_message_remains_practical():
    assert (
        _response_mode("أنسى غالبًا في المساء بعد العشاء، وأريد شيئًا بسيطًا جدًا.")
        == "practical"
    )


def _shadow_resolution(intent: str) -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent=intent,
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id=f"synthetic.{intent}",
            rule_version="1",
            allowed_actions=("prepare_clinician_questions",),
            forbidden_actions=("diagnose",),
            required_facts=("certified_consultation_brief",),
            language="fr",
        ),
        reply="Réponse déterministe.",
    )


def test_clinician_prep_runtime_shadow_reverifies_with_active_patient():
    resolution = _shadow_resolution("clinician_prep")
    protected = type(
        "Protected",
        (),
        {
            "structurally_valid": True,
            "reinjected_reply": resolution.reply,
        },
    )()

    with patch(
        "companion.conversation.shadow_validate_protected_resolution",
        return_value=protected,
    ) as protected_shadow:
        with patch("companion.conversation.verify_protected_advice_reply") as verify:
            _shadow_narration_envelope(
                resolution,
                patient_id=77,
                language="fr",
                prefer_latin_script=False,
            )

    protected_shadow.assert_called_once()
    verify.assert_called_once_with(77, resolution, resolution.reply)


def test_non_clinician_runtime_shadow_does_not_use_protected_seam():
    resolution = _shadow_resolution("food")

    with patch(
        "companion.conversation.shadow_validate_protected_resolution"
    ) as protected_shadow:
        _shadow_narration_envelope(
            resolution,
            patient_id=77,
            language="fr",
            prefer_latin_script=False,
        )

    protected_shadow.assert_not_called()



def test_provider_shadow_candidate_is_verified_without_changing_patient_reply():
    resolution = _shadow_resolution("clinician_prep")
    token = "{{NVB_0123456789ABCDEF0123456789ABCDEF}}"
    envelope = type("Envelope", (), {"protected_body_token": token})()
    protected = type(
        "Protected",
        (),
        {
            "structurally_valid": True,
            "reinjected_reply": resolution.reply,
            "envelope": envelope,
        },
    )()
    provider_candidate = f"D'accord. {token}"

    with (
        patch(
            "companion.conversation.shadow_validate_protected_resolution",
            return_value=protected,
        ),
        patch(
            "companion.conversation.generate_protected_provider_shadow_candidate",
            return_value=provider_candidate,
        ),
        patch(
            "companion.conversation.verify_and_reinject_protected_narration",
            create=True,
        ) as _unused,
        patch(
            "companion.narration_envelope.verify_and_reinject_protected_narration",
            return_value=f"D'accord. {resolution.reply}",
        ),
        patch("companion.conversation.verify_protected_advice_reply") as verify,
    ):
        _shadow_narration_envelope(
            resolution,
            patient_id=77,
            language="fr",
            prefer_latin_script=False,
        )

    assert verify.call_count == 2
    assert verify.call_args_list[0].args == (77, resolution, resolution.reply)
    assert verify.call_args_list[1].args == (
        77,
        resolution,
        f"D'accord. {resolution.reply}",
    )


def test_runtime_shadow_marks_only_active_staff_as_internal_authorized():
    resolution = _shadow_resolution("clinician_prep")
    envelope = type("Envelope", (), {"protected_body_token": "{{NVB_INTERNAL}}"})()
    protected = type(
        "Protected",
        (),
        {
            "structurally_valid": True,
            "reinjected_reply": resolution.reply,
            "envelope": envelope,
        },
    )()

    with (
        patch(
            "companion.conversation.shadow_validate_protected_resolution",
            return_value=protected,
        ),
        patch(
            "companion.conversation.generate_protected_provider_shadow_candidate",
            return_value=None,
        ) as generator,
        patch("companion.conversation.verify_protected_advice_reply"),
    ):
        _shadow_narration_envelope(
            resolution,
            patient_id=77,
            language="fr",
            prefer_latin_script=False,
            internal_shadow_authorized=True,
        )

    assert generator.call_args.kwargs["internal_authorized"] is True


def test_chat_wires_active_staff_to_internal_shadow():
    from companion import conversation

    patient = SimpleNamespace(id=77, first_name="", is_active=True, is_staff=True)
    resolution = _shadow_resolution("clinician_prep")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=resolution,
        ),
        patch(
            "companion.conversation._get_context",
            return_value=__import__(
                "core.contracts.domain_context",
                fromlist=["DomainContext"],
            ).DomainContext.empty(language="fr"),
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=lambda _pid, _res, candidate: candidate,
        ),
        patch("companion.conversation._shadow_narration_envelope") as shadow,
        patch("companion.conversation.record_clinical_decision_audit"),
        patch("companion.conversation.record_companion_route"),
        patch("companion.conversation._append_turn"),
    ):
        reply = conversation.chat(
            "Aide-moi à préparer les questions pour mon médecin.",
            memory=None,
            deep=object(),
            llm=object(),
            language="fr",
            patient=patient,
        )

    assert reply == resolution.reply
    assert shadow.call_args.kwargs["internal_shadow_authorized"] is True


def test_stream_wires_active_staff_to_internal_shadow():
    from companion import conversation

    patient = SimpleNamespace(id=77, first_name="", is_active=True, is_staff=True)
    resolution = _shadow_resolution("clinician_prep")

    with (
        patch(
            "companion.conversation.get_advice_resolution",
            return_value=resolution,
        ),
        patch(
            "companion.conversation._get_context",
            return_value=__import__(
                "core.contracts.domain_context",
                fromlist=["DomainContext"],
            ).DomainContext.empty(language="fr"),
        ),
        patch(
            "companion.conversation.verify_advice_reply",
            side_effect=lambda _pid, _res, candidate: candidate,
        ),
        patch("companion.conversation._shadow_narration_envelope") as shadow,
        patch("companion.conversation.record_clinical_decision_audit"),
        patch("companion.conversation.record_companion_route"),
        patch("companion.conversation._append_turn"),
    ):
        chunks = list(
            conversation.stream_chat(
                "Aide-moi à préparer les questions pour mon médecin.",
                memory=None,
                deep=object(),
                llm=object(),
                language="fr",
                patient=patient,
            )
        )

    assert chunks == [resolution.reply]
    assert shadow.call_args.kwargs["internal_shadow_authorized"] is True
