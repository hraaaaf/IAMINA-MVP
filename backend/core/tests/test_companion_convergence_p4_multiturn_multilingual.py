from types import SimpleNamespace
from unittest.mock import patch

import pytest

from companion.conversation import _build_runtime_prompt, detect_language
from companion.narrator_prompts import SYSTEM_WITH_STATE, get_language_label
from core.contracts.companion_context import CompanionContext
from core.contracts.domain_context import DomainContext


class _Memory:
    emotional_signals: list[str] = []
    last_concern = None


class _Deep:
    consecutive_log_days = 0


@pytest.mark.parametrize(
    ("code", "expected_label"),
    (
        ("fr", "français"),
        ("en", "English"),
        ("ar", "العربية الفصحى"),
        ("ar-MA", "الدارجة المغربية"),
    ),
)
def test_narrator_governance_is_language_invariant(code, expected_label):
    system = SYSTEM_WITH_STATE.format(
        language=get_language_label(code),
        tone="neutral",
        state="",
    )

    assert expected_label in system
    assert "Tu es un NARRATEUR, pas une autorité clinique." in system
    assert "N'invente aucun diagnostic" in system
    assert "N'invente aucune éligibilité proactive" in system
    assert "Ne prescris jamais" in system
    assert "le message courant prévaut" in system
    assert "il ne peut jamais remplacer ni contredire le contexte clinique gouverné" in system


def test_language_resolution_preserves_explicit_ar_and_detects_darija():
    assert detect_language("مرحبا، كيف حالك؟", "ar") == "ar"
    assert detect_language("salam, bghit nfhem hadchi", "fr") == "ar-MA"
    assert detect_language("I want to understand this", "en") == "en"
    assert detect_language("Bonjour", "fr") == "fr"


def test_multiturn_current_correction_overrides_history_only_for_patient_declared_facts():
    old_turns = [
        SimpleNamespace(role="assistant", message="Tu m'as dit être très fatigué."),
        SimpleNamespace(role="user", message="Je suis très fatigué aujourd'hui."),
    ]
    tone = SimpleNamespace(mode=SimpleNamespace(value="neutral"))
    patient = SimpleNamespace(id=42, first_name="")

    with (
        patch("companion.conversation._recent_turns", return_value=old_turns),
        patch("companion.conversation._turn_count", return_value=2),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch(
            "companion.conversation._get_companion_context",
            return_value=CompanionContext.empty(language="fr"),
        ),
        patch("companion.conversation.select_relationship_tone", return_value=tone),
        patch("companion.conversation.get_tone_instruction", return_value=""),
        patch(
            "companion.conversation.compute_state",
            return_value=SimpleNamespace(concern_level=0.0),
        ),
        patch("companion.conversation.state_to_prompt", return_value=""),
    ):
        _, _, system, user_prompt = _build_runtime_prompt(
            message="Correction : aujourd'hui je ne suis plus fatigué.",
            memory=_Memory(),
            deep=_Deep(),
            language="fr",
            patient=patient,
            context_days=14,
            streaming=False,
        )

    assert "Je suis très fatigué aujourd'hui." in user_prompt
    assert "Correction : aujourd'hui je ne suis plus fatigué." in user_prompt
    assert "le message courant prévaut" in system
    assert "contexte clinique gouverné" in system
    assert "[GOVERNED_COMPANION_CONTEXT]" in system


def test_multiturn_rule_does_not_turn_history_into_clinical_authority():
    formatted = SYSTEM_WITH_STATE.format(
        language=get_language_label("fr"),
        tone="neutral",
        state="",
    )

    assert "Tout fait de santé doit provenir explicitement" in formatted
    assert "[APPROVED_SESSION_CONTEXT]" in formatted
    assert "[GOVERNED_COMPANION_CONTEXT]" in formatted
    assert "historique conversationnel" in formatted
    assert "contexte clinique gouverné" in formatted
