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
        with patch("companion.conversation.verify_advice_reply") as verify:
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
