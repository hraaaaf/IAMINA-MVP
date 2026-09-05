from companion.conversation import _ARABIC_RE, _safety_reply


def test_arabic_script_darija_dose_block_stays_arabic_script():
    reply = _safety_reply(
        "إلا كانت القياسات طالعة، شحال من وحدة ديال الإنسولين ناخد؟",
        patient=None,
        language="ar-MA",
    )
    assert reply is not None
    assert _ARABIC_RE.search(reply)
    assert not any("a" <= char.lower() <= "z" for char in reply)


def test_latin_darija_dose_block_stays_latin_script():
    reply = _safety_reply(
        "Ila kan l9yas tale3, chhal men unité dial insuline nakhod?",
        patient=None,
        language="ar-MA",
    )
    assert reply is not None
    assert not _ARABIC_RE.search(reply)
