from types import SimpleNamespace

import pytest

from companion import conversation, narrator_prompts


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Résume ce qu'on vient de décider en une phrase simple.", "recap"),
        ("Summarize what we just decided in one simple sentence.", "recap"),
        ("لخّص ما اتفقنا عليه الآن في جملة بسيطة واحدة.", "recap"),
        ("وش اتفقنا عليه الحين بجملة بسيطة وحدة؟", "recap"),
        ("شنو اتفقنا عليه دابا فجملة وحدة؟", "recap"),
    ],
)
def test_response_mode_detects_recap_across_supported_language_families(message, expected):
    assert conversation._response_mode(message) == expected


def test_verbatim_repeat_detection_is_whitespace_and_case_insensitive(monkeypatch):
    monkeypatch.setattr(
        conversation,
        "_recent_turns",
        lambda *args, **kwargs: [SimpleNamespace(message="Start with one anchor.")],
    )

    assert conversation._is_verbatim_repeat(
        "  start   with one ANCHOR. ",
        patient=object(),
        mode="practical",
    )


def test_recap_rejects_repeat_of_older_assistant_turn(monkeypatch):
    calls = []

    def recent_turns(_patient, limit, role=None, **_kwargs):
        calls.append((limit, role))
        return [
            SimpleNamespace(message="Prepare these four questions."),
            SimpleNamespace(message="Start with one anchor."),
            SimpleNamespace(message="Strip it down."),
        ][:limit]

    monkeypatch.setattr(conversation, "_recent_turns", recent_turns)

    assert conversation._is_verbatim_repeat(
        "Start with one anchor.",
        patient=object(),
        mode="recap",
    )
    assert calls[-1] == (20, "assistant")


def test_practical_repeat_only_compares_latest_assistant_turn(monkeypatch):
    calls = []

    def recent_turns(_patient, limit, role=None, **_kwargs):
        calls.append((limit, role))
        return [
            SimpleNamespace(message="Prepare these four questions."),
            SimpleNamespace(message="Start with one anchor."),
        ][:limit]

    monkeypatch.setattr(conversation, "_recent_turns", recent_turns)

    assert not conversation._is_verbatim_repeat(
        "Start with one anchor.",
        patient=object(),
        mode="practical",
    )
    assert calls[-1] == (1, "assistant")


def test_emotional_reply_never_triggers_continuity_retry(monkeypatch):
    monkeypatch.setattr(
        conversation,
        "_recent_turns",
        lambda *args, **kwargs: [SimpleNamespace(message="Same empathy")],
    )

    assert not conversation._is_verbatim_repeat(
        "Same empathy",
        patient=object(),
        mode="emotional",
    )


def test_recap_retry_requires_history_synthesis_not_previous_reply_recycling():
    prompt = conversation._continuity_retry_prompt("base", "recap")

    assert "tout ce qui a été convenu dans l'historique" in prompt
    assert "sans recycler une réponse précédente" in prompt
    assert "n'invente aucune action santé/comportementale" in prompt


def test_narrator_contract_requires_direct_practical_help_before_questions():
    assert "Ne réponds jamais uniquement par des questions de clarification" in narrator_prompts.SYSTEM_WITH_STATE
    assert "ne réponds jamais uniquement par des questions" in narrator_prompts.CHAT_USER


def test_narrator_contract_recap_must_cover_more_than_latest_exchange():
    assert "au moins deux éléments distincts" in narrator_prompts.SYSTEM_WITH_STATE
    assert "un résumé du seul dernier échange est invalide" in narrator_prompts.CHAT_USER


@pytest.mark.parametrize(
    ("language", "message"),
    [
        ("fr", "C'est surtout le soir après le dîner que j'oublie."),
        ("en", "I mostly forget in the evening after dinner."),
        ("ar", "أنسى غالبًا في المساء بعد العشاء."),
        ("ar-MA", "كننسى كثر بالليل من بعد العشا."),
        ("ar-SA", "غالبًا أنسى بالليل بعد العشاء."),
        ("ar-AE", "أكثر شي أنسى بالليل عقب العشا."),
        ("ar-KW", "غالبًا أنسى بالليل عقب العشا."),
        ("ar-QA", "غالبًا أنسى بالليل عقب العشا."),
        ("ar-OM", "غالبًا أنسى بالليل بعد العشا."),
    ],
)
def test_runtime_evening_anchor_detection_matches_certification_locales(language, message):
    assert conversation._contains_evening_anchor(language, message)


def test_missing_explicit_evening_anchor_triggers_retry(monkeypatch):
    monkeypatch.setattr(conversation, "_recent_turns", lambda *args, **kwargs: [])

    assert conversation._needs_continuity_retry(
        "Garde une checklist très simple.",
        "C'est surtout le soir après le dîner que j'oublie.",
        patient=object(),
        mode="practical",
        language="fr",
    )


def test_recap_missing_earlier_evening_anchor_triggers_retry_and_has_safe_fallback(monkeypatch):
    def recent_turns(_patient, _limit, role=None, **_kwargs):
        if role == "assistant":
            return []
        if role == "user":
            return [
                SimpleNamespace(message="Ne me donne pas de dose. Aide-moi à préparer ce que je dois demander à mon médecin."),
                SimpleNamespace(message="C'est surtout le soir après le dîner que j'oublie. Je veux quelque chose de très simple."),
            ]
        return []

    monkeypatch.setattr(conversation, "_recent_turns", recent_turns)
    patient = object()

    assert conversation._needs_continuity_retry(
        "On a préparé des questions pour ton médecin.",
        "Résume ce qu'on vient de décider en une phrase simple.",
        patient=patient,
        mode="recap",
        language="fr",
    )
    fallback = conversation._contextual_continuity_fallback(
        message="Résume ce qu'on vient de décider en une phrase simple.",
        patient=patient,
        language="fr",
        mode="recap",
        prefer_latin_script=False,
    )
    assert fallback is not None
    assert "soir" in fallback.lower()
    assert "médecin" in fallback.lower()


def test_retry_revalidates_second_repeat_and_uses_contextual_fallback(monkeypatch):
    repeated = (
        "Réduis au minimum : une checklist de trois cases vides, sans contenu imposé. "
        "Coche ce qui est fait et repars de là."
    )

    def recent_turns(_patient, _limit, role=None, **_kwargs):
        if role == "assistant":
            return [SimpleNamespace(message=repeated)]
        if role == "user":
            return [SimpleNamespace(message="C'est surtout le soir après le dîner que j'oublie.")]
        return []

    monkeypatch.setattr(conversation, "_recent_turns", recent_turns)
    monkeypatch.setattr(conversation, "_finalize_reply", lambda reply, *args, **kwargs: reply)
    llm = SimpleNamespace(
        complete=lambda *_args, **_kwargs: SimpleNamespace(content=f'{{"reply": "{repeated}"}}')
    )

    repaired = conversation._retry_finalized_repeat(
        reply=repeated,
        message="C'est surtout le soir après le dîner que j'oublie. Je veux quelque chose de très simple.",
        llm=llm,
        system="system",
        user_prompt="prompt",
        deep=object(),
        language="fr",
        patient=object(),
        ctx=SimpleNamespace(pivot_text=None),
        prefer_latin_script=False,
    )

    assert repaired != repeated
    assert "soir" in repaired.lower()
    assert "dîner" in repaired.lower()


@pytest.mark.parametrize(
    ("language", "message", "dialect_marker"),
    [
        ("ar-MA", "كننسى كثر بالليل من بعد العشا.", "من بعد"),
        ("ar-SA", "غالبًا أنسى بالليل بعد العشاء.", "بالليل"),
        ("ar-AE", "أكثر شي أنسى بالليل عقب العشا.", "عقب العشا"),
        ("ar-KW", "غالبًا أنسى بالليل عقب العشا.", "حيل"),
        ("ar-QA", "غالبًا أنسى بالليل عقب العشا.", "وايد"),
        ("ar-OM", "غالبًا أنسى بالليل بعد العشا.", "واجد"),
    ],
)
def test_contextual_fallback_preserves_target_dialect(language, message, dialect_marker):
    fallback = conversation._contextual_continuity_fallback(
        message=message,
        patient=object(),
        language=language,
        mode="practical",
        prefer_latin_script=False,
    )

    assert fallback is not None
    assert dialect_marker in fallback
