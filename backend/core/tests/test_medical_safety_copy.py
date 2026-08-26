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
