from core.input_safety import ALLOW, INSULIN_BLOCK, URGENT, evaluate_input_safety


def test_suicidal_ideation_is_urgent():
    decision = evaluate_input_safety("bghit nmout")
    assert decision.action == URGENT
    assert decision.reason == "suicidal_ideation"


def test_vital_glucose_emergency_is_urgent():
    decision = evaluate_input_safety("ma glycémie est à 32")
    assert decision.action == URGENT


def test_insulin_dose_request_is_blocked():
    decision = evaluate_input_safety("Quelle dose d'insuline je dois prendre ?")
    assert decision.action == INSULIN_BLOCK


def test_educational_insulin_question_is_allowed():
    decision = evaluate_input_safety("C'est quoi l'insuline ?")
    assert decision.action == ALLOW


def test_urgent_precedes_insulin_block():
    decision = evaluate_input_safety("Je suis inconscient, quelle dose d'insuline ?")
    assert decision.action == URGENT


def test_none_and_empty_are_allowed():
    assert evaluate_input_safety(None).action == ALLOW
    assert evaluate_input_safety("").action == ALLOW


def test_sse_urgent_fast_path_does_not_initialize_iamina(monkeypatch):
    from types import SimpleNamespace

    from django.test import RequestFactory

    from ai.api.v1 import ai

    monkeypatch.setattr(
        "core.input_safety.evaluate_input_safety",
        lambda message, language=None: type("D", (), {"action": URGENT})(),
    )
    monkeypatch.setattr(ai, "_get_patient_language", lambda user: "fr")
    monkeypatch.setattr(ai, "track", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "companion.core.IAmina",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("IAmina initialized")),
    )
    request = RequestFactory().get("/api/v1/ai/chat/stream")
    request.user = SimpleNamespace(id=1)
    response = ai.chat_stream(request, "urgence")
    assert list(response.streaming_content)[-1] == b"data: [DONE]\n\n"


def test_sse_insulin_fast_path_does_not_initialize_iamina(monkeypatch):
    from types import SimpleNamespace

    from django.test import RequestFactory

    from ai.api.v1 import ai

    monkeypatch.setattr(
        "core.input_safety.evaluate_input_safety",
        lambda message, language=None: type("D", (), {"action": INSULIN_BLOCK})(),
    )
    monkeypatch.setattr(ai, "_get_patient_language", lambda user: "fr")
    monkeypatch.setattr(ai, "track", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "companion.core.IAmina",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("IAmina initialized")),
    )
    request = RequestFactory().get("/api/v1/ai/chat/stream")
    request.user = SimpleNamespace(id=1)
    response = ai.chat_stream(request, "dose")
    assert list(response.streaming_content)[-1] == b"data: [DONE]\n\n"
