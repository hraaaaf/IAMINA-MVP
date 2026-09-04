from companion.narrator_prompts import CHAT_USER, SYSTEM_WITH_STATE


def test_system_prompt_requires_current_constraint_adaptation():
    assert "le message précise un moment, une cadence ou la simplicité" in SYSTEM_WITH_STATE
    assert "nomme explicitement cette contrainte" in SYSTEM_WITH_STATE
    assert "renvoie jamais mot pour mot une réponse précédente" in SYSTEM_WITH_STATE


def test_system_prompt_requires_real_recap_from_history():
    assert "résume uniquement ce qui a réellement été convenu" in SYSTEM_WITH_STATE
    assert "au moins deux éléments distincts" in SYSTEM_WITH_STATE
    assert "Ne décris jamais la demande de résumé elle-même" in SYSTEM_WITH_STATE


def test_system_prompt_forbids_invented_reminder_cadence():
    assert "aucun horaire/fréquence inventé" in SYSTEM_WITH_STATE
    assert "N'invente jamais de rappel ni d'heure fixe" in SYSTEM_WITH_STATE


def test_chat_prompt_forces_new_constraint_and_recap_handling():
    assert "reprends cette contrainte concrètement dans la réponse" in CHAT_USER
    assert "adapte-la au message courant au lieu de la répéter" in CHAT_USER
    assert "relie au moins deux éléments distincts" in CHAT_USER
    assert "un résumé du seul dernier échange est invalide" in CHAT_USER
