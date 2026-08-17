from companion.conversation import chat as conversation_chat
from companion.conversation import stream_chat as conversation_stream_chat
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import evaluate_input_safety


def test_direct_conversation_chat_uses_canonical_emergency_composer():
    message = "glycémie 35"
    decision = evaluate_input_safety(message)
    expected = compose_emergency_for_patient(
        decision,
        language="fr",
        message=message,
    ).reply

    reply = conversation_chat(
        message,
        memory=None,
        deep=None,
        language="fr",
        patient=None,
    )

    assert reply == expected


def test_direct_conversation_stream_uses_canonical_emergency_composer():
    message = "glycémie 35"
    decision = evaluate_input_safety(message)
    expected = compose_emergency_for_patient(
        decision,
        language="fr",
        message=message,
    ).reply

    chunks = list(
        conversation_stream_chat(
            message,
            memory=None,
            deep=None,
            language="fr",
            patient=None,
        )
    )

    assert chunks == [expected]
