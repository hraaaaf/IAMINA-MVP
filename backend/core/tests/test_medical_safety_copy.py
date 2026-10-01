from core.medical_safety import no_prescription_message


def test_french_no_prescription_message_keeps_clinical_authority_and_diacritics():
    message = no_prescription_message("fr")

    assert "Je ne peux pas prescrire" in message
    assert "modifier une dose d'insuline" in message
    assert "arrêter un traitement" in message
    assert "poser un diagnostic" in message
    assert "t'aider à organiser" in message
    assert "préparer les bonnes questions" in message
    assert "ton médecin" in message


def test_darija_no_prescription_message_mirrors_script():
    latin = no_prescription_message("ar-MA", script_preference="latin")
    arabic = no_prescription_message("ar-MA", script_preference="arabic")

    assert "Ma nqderch" in latin
    assert not any("\u0600" <= ch <= "\u06ff" for ch in latin)
    assert "ما نقدرش" in arabic
    assert not any(ch.isascii() and ch.isalpha() for ch in arabic)
