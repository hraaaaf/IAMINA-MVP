from companion.conversation import _response_mode


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
