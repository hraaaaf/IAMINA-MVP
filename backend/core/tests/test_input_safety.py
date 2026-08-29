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


def test_arabic_insulin_dose_requests_are_blocked():
    messages = (
        "إذا كانت قراءاتي مرتفعة، كم وحدة إنسولين يجب أن آخذ؟",
        "إلا كانت القياسات طالعة، شحال من وحدة ديال الإنسولين ناخد؟",
        "إذا كانت قراءاتي مرتفعة، جم وحدة إنسولين آخذ؟",
        "شنو هي جرعة الإنسولين اللي ناخد؟",
    )
    for message in messages:
        decision = evaluate_input_safety(message)
        assert decision.action == INSULIN_BLOCK, message


def test_educational_insulin_questions_are_allowed():
    for message in ("C'est quoi l'insuline ?", "ما هو الإنسولين؟"):
        decision = evaluate_input_safety(message)
        assert decision.action == ALLOW, message


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

    monkeypatch.setattr("core.input_safety.evaluate_input_safety", lambda message: type("D", (), {"action": URGENT})())
    monkeypatch.setattr(ai, "_get_patient_language", lambda user: "fr")
    monkeypatch.setattr(ai, "track", lambda *args, **kwargs: None)
    monkeypatch.setattr("companion.core.IAmina", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("IAmina initialized")))
    request = RequestFactory().get("/api/v1/ai/chat/stream")
    request.user = SimpleNamespace(id=1)
    response = ai.chat_stream(request, "urgence")
    assert list(response.streaming_content)[-1] == b"data: [DONE]\n\n"


def test_sse_insulin_fast_path_does_not_initialize_iamina(monkeypatch):
    from types import SimpleNamespace

    from django.test import RequestFactory

    from ai.api.v1 import ai

    monkeypatch.setattr("core.input_safety.evaluate_input_safety", lambda message: type("D", (), {"action": INSULIN_BLOCK})())
    monkeypatch.setattr(ai, "_get_patient_language", lambda user: "fr")
    monkeypatch.setattr(ai, "track", lambda *args, **kwargs: None)
    monkeypatch.setattr("companion.core.IAmina", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("IAmina initialized")))
    request = RequestFactory().get("/api/v1/ai/chat/stream")
    request.user = SimpleNamespace(id=1)
    response = ai.chat_stream(request, "dose")
    assert list(response.streaming_content)[-1] == b"data: [DONE]\n\n"
