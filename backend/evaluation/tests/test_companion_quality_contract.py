from companion.narrator_prompts import CHAT_USER, SYSTEM_WITH_STATE, get_language_label


def test_darija_label_mirrors_current_script():
    label = get_language_label("ar-MA")
    assert "Latin/Arabizi reste en Latin/Arabizi" in label
    assert "alphabet arabe reste en arabe" in label


def test_narrator_executes_concrete_requests_instead_of_promising():
    assert "ne promets jamais une liste, un plan ou des questions" in SYSTEM_WITH_STATE
    assert "2 à 4 questions courtes" in SYSTEM_WITH_STATE
    assert "sans inclure réellement les éléments" in CHAT_USER


def test_narrator_uses_practical_history_without_turning_it_clinical():
    assert "contraintes pratiques explicitement exprimées" in SYSTEM_WITH_STATE
    assert "sans les transformer en faits cliniques" in SYSTEM_WITH_STATE
    assert "préférences et contraintes pratiques explicites" in CHAT_USER


def test_narrator_avoids_repetitive_empathy_when_request_is_practical():
    assert "Évite les introductions empathiques répétitives" in SYSTEM_WITH_STATE
    assert "commence directement par l'aide demandée" in SYSTEM_WITH_STATE
    assert "plutôt qu'une formule d'empathie générique" in CHAT_USER
