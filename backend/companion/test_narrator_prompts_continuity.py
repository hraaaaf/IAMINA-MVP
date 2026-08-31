from companion.narrator_prompts import CHAT_USER, SYSTEM_WITH_STATE


def test_system_prompt_requires_current_constraint_adaptation():
    assert "réponds d'abord au message courant" in SYSTEM_WITH_STATE
    assert "ne renvoie jamais mot pour mot une réponse précédente" in SYSTEM_WITH_STATE


def test_system_prompt_requires_real_recap_from_history():
    assert "résume uniquement ce qui a réellement été convenu" in SYSTEM_WITH_STATE
    assert "sans recycler une ancienne réponse comme faux résumé" in SYSTEM_WITH_STATE


def test_chat_prompt_forces_new_constraint_and_recap_handling():
    assert "si une nouvelle contrainte ou une nouvelle intention apparaît" in CHAT_USER
    assert "adapte explicitement la réponse" in CHAT_USER
    assert "respecte exactement le format demandé" in CHAT_USER
